from flask import render_template, g, flash
from flask_security import login_required, roles_accepted
import appli
import appli.part.prj
import datetime
import requests
import sys
from appli import app, PrintInCharte, database, gvp, ntcv
from appli.database import ExecSQL, db

######################################################################################################################

SQLTreeSelect = """concat(t14.name||'>',t13.name||'>',t12.name||'>',t11.name||'>',t10.name||'>',t9.name||'>',t8.name
            ||'>',t7.name||'>'
            ,t6.name||'>',t5.name||'>',t4.name||'>',t3.name||'>',t2.name||'>',t1.name||'>',t.name) tree"""
SQLTreeJoin = """left join taxonomy t1 on t.parent_id=t1.id
      left join taxonomy t2 on t1.parent_id=t2.id
      left join taxonomy t3 on t2.parent_id=t3.id
      left join taxonomy t4 on t3.parent_id=t4.id
      left join taxonomy t5 on t4.parent_id=t5.id
      left join taxonomy t6 on t5.parent_id=t6.id
      left join taxonomy t7 on t6.parent_id=t7.id
      left join taxonomy t8 on t7.parent_id=t8.id
      left join taxonomy t9 on t8.parent_id=t9.id
      left join taxonomy t10 on t9.parent_id=t10.id
      left join taxonomy t11 on t10.parent_id=t11.id
      left join taxonomy t12 on t11.parent_id=t12.id
      left join taxonomy t13 on t12.parent_id=t13.id
      left join taxonomy t14 on t13.parent_id=t14.id"""


@app.route('/taxo/browse/', methods=['GET', 'POST'])
def routetaxobrowse():
    if gvp('updatestat') == 'Y':
        DoFullSync()
    g.taxoserver_url = app.config.get('TAXOSERVER_URL')
    return PrintInCharte(render_template('taxonomy/browse.html'))


def request_withinstanceinfo(urlend, params):
    params['id_instance'] = app.config.get('TAXOSERVER_INSTANCE_ID')
    params['sharedsecret'] = app.config.get('TAXOSERVER_SHARED_SECRET')
    params['ecotaxa_version'] = appli.ecotaxa_version

    r = requests.post(app.config.get('TAXOSERVER_URL') + urlend, params)
    return r.json()


@app.route('/taxo/dosync', methods=['POST'])
@login_required
@roles_accepted(database.AdministratorLabel, database.ProjectCreatorLabel)
def routetaxodosync():
    return DoFullSync()


def DoFullSync():
    txt = ""
    try:
        updatable_cols = ['parent_id', 'name', 'taxotype', 'taxostatus', 'id_source', 'id_instance', 'rename_to',
                          'display_name', 'source_desc', 'source_url', 'creation_datetime', 'creator_email']
        max_update = database.GetAll("""
                    select coalesce(max(lastupdate_datetime),to_timestamp('2000-01-01','YYYY-MM-DD')) lastupdate 
                    from taxonomy""")
        max_update_date = max_update[0]['lastupdate']

        j = request_withinstanceinfo("/gettaxon/", {'filtertype': 'since', 'startdate': max_update_date})
        if 'msg' in j:
            return appli.ErrorFormat("Sync Error :" + j['msg'])
        nbr_row = len(j)
        nbr_update = nbr_insert = 0
        txt += "Received {} rows<br>".format(nbr_row)
        if nbr_row > 0:
            txt += "Taxo 0 = {}<br>".format(j[0])
        for jtaxon in j:
            taxon = db.session.query(database.Taxonomy).filter_by(id=int(jtaxon['id'])).first()
            lastupdate_datetime = datetime.datetime.strptime(jtaxon['lastupdate_datetime'], '%Y-%m-%d %H:%M:%S')
            if taxon:
                if taxon.lastupdate_datetime == lastupdate_datetime:
                    continue  # already up to date
                nbr_update += 1
            else:
                if ntcv(jtaxon['rename_to']) != '':
                    continue  # don't insert taxon that should be renamed
                if ntcv(jtaxon['taxostatus']) == 'D':
                    continue  # don't insert taxon that are deprecated and planned to be deleted
                nbr_insert += 1
                taxon = database.Taxonomy()
                taxon.id = int(jtaxon['id'])
                db.session.add(taxon)

            for c in updatable_cols:
                setattr(taxon, c, jtaxon[c])
            taxon.lastupdate_datetime = lastupdate_datetime
            db.session.commit()
        # On marque à recalculer les samples qui ont des categories qui sont renommées
        sql = """update part_samples
            set daterecalculhistotaxo=null
            where psampleid in (select psampleid from part_histocat_lst lst
            join taxonomy t on lst.classif_id=t.id and (t.rename_to is not null or taxostatus='D') )
        """
        nbr_sample_to_recalc = ExecSQL(sql)
        # on efface les taxon qui doivent être renomé car ils l'ont normalement été
        sql = """delete from taxonomy where rename_to is not null """
        ExecSQL(sql)
        sql = """delete from taxonomy t where taxostatus='D' """
        ExecSQL(sql)
        # il faut recalculer part_histocat,part_histocat_lst pour ceux qui referencaient un taxon renomé et donc disparu
        app.logger.info(f"nbr_sample_to_recalc={nbr_sample_to_recalc}")
        if nbr_sample_to_recalc > 0:
            # recalcul part_histocat,part_histocat_lst
            appli.part.prj.GlobalTaxoCompute()

        flash("Received {} rows,Insertion : {} Update :{}".format(nbr_row, nbr_insert, nbr_update), "success")

        # txt="<script>location.reload(true);</script>" # non car ça reprovoque le post de l'arrivée initiale
        txt = "<script>window.location=window.location;</script>"
    except:
        msg = "Error while syncing {}".format(sys.exc_info())
        app.logger.error(msg)
        txt += appli.ErrorFormat(msg)

    return txt
