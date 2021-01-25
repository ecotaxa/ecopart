from flask import render_template, request, g
from flask_login import current_user
from flask_security import login_required
import appli
import appli.part.common_sample_import as common_import
import appli.part.database as partdatabase
import appli.part.lisst_sample_import as lisst_sample_import
import appli.part.sampleedit as sampleedit
import appli.part.uvp6remote_sample_import as uvp6remote_sample_import
import appli.part.uvp_sample_import as uvp_sample_import
import logging
from appli import app, PrintInCharte, database, gvg, gvp, ErrorFormat
from appli.database import GetAll, db


@app.route('/part/prj/')
@login_required
def part_prj():
    params = {}
    sql = """select pprojid,ptitle,up.ownerid,u.name,u.email,rawfolder,instrumtype,ep.title
            ,(select count(*) from part_samples where pprojid=up.pprojid) samplecount
            from part_projects up
            left JOIN projects ep on up.projid=ep.projid
            LEFT JOIN users u on ownerid=u.id
          """
    sql += " where 1=1 "
    if not current_user.has_role(database.AdministratorLabel):
        sql += "  and ownerid=%d" % (current_user.id,)
    if gvg('filt_title', '') != '':
        sql += """ and (  up.ptitle ilike '%%'||%(title)s ||'%%' 
                        or to_char(up.pprojid,'999999') like '%%'||%(title)s 
                        or ep.title ilike '%%'||%(title)s ||'%%' 
                        or to_char(ep.projid,'999999') like '%%'||%(title)s) """
        params['title'] = gvg('filt_title')
    if gvg('filt_instrum', '') != '':
        sql += " and up.instrumtype ilike '%%'||%(filt_instrum)s ||'%%'  "
        params['filt_instrum'] = gvg('filt_instrum')
    sql += " order by lower(ep.title),lower(ptitle)"
    res = GetAll(sql, params)  # ,debug=True
    # app.logger.info("res=%s",res)
    can_create = False
    if current_user.has_role(database.AdministratorLabel) or current_user.has_role(database.ProjectCreatorLabel):
        can_create = True
    # noinspection HtmlUnknownTarget
    g.headcenter = "<h4>Particle Projects management</h4><a href='/part/'>Particle Module Home</a>"
    # noinspection PyUnresolvedReferences
    return PrintInCharte(
        render_template('part/list.html', PrjList=res, CanCreate=can_create,
                        AppManagerMailto=appli.GetAppManagerMailto(),
                        filt_title=gvg('filt_title'), filt_subset=gvg('filt_subset'),
                        filt_instrum=gvg('filt_instrum')))


@app.route('/part/prj_uvpgraph/<int:PrjId>/<int:offset>')
@login_required
def part_prj_vpgraph(PrjId, offset):
    prj = GetAll("""select pp.* from part_projects pp where pprojid=%s""", (PrjId,))
    if len(prj) != 1:
        return PrintInCharte(ErrorFormat("Project doesn't exists"))
    prj = prj[0]
    if prj['ownerid'] != current_user.id and not current_user.has_role(database.AdministratorLabel):
        return PrintInCharte(ErrorFormat("Access Denied"))
    g.headcenter = "<h4>Particle Project %s : %s</h4><a href='/part/prj/%s'>Project home</a>" % (
        prj['projid'], prj['ptitle'], prj['pprojid'],)
    dbsample = database.GetAll("""
            select psampleid,filename,profileid 
            from part_samples s 
            where pprojid=%s
            order by filename desc limit 50 OFFSET %s 
          """ % (PrjId, offset))
    txt = """<style>
    .idepth,.ipart {height: auto}
    </style>
    <button class='btn' onclick='dozoom(50);'>50%</button>
    <button class='btn' onclick='dozoom(75);'>75%</button>
    <button class='btn' onclick='dozoom(100);'>100%</button>
    <script>
    function dozoom(z) {
      $('.idepth').css('width',(800*z/100).toFixed().toString()+"px");
      $('.ipart').css('width',(1600*z/100).toFixed().toString()+"px");
    }
</script>
    """
    for s in dbsample:
        txt += """<p class='ghead'>Graph for {psampleid} - {filename} - {profileid} - </p>
          <img src='/vault/{idepth}' class='idepth'> <img src='/vault/{ipart}' class='ipart'>
          """.format(psampleid=s['psampleid'], filename=s['filename'], profileid=s['profileid'],
                     idepth=uvp_sample_import.GetPathForImportGraph(s['psampleid'], 'depth', True),
                     ipart=uvp_sample_import.GetPathForImportGraph(s['psampleid'], 'particle', True))
    return PrintInCharte(txt)


@app.route('/part/prj/<int:PrjId>')
@login_required
def part_prj_main(PrjId):
    # Prj = partdatabase.part_projects.query.filter_by(pprojid=PrjId).first()
    prj = GetAll("""select pp.*
                    ,oldestsampledate+make_interval(0,public_visibility_deferral_month) visibility_date  
                    ,oldestsampledate+make_interval(0,public_partexport_deferral_month) partexport_date 
                    ,oldestsampledate+make_interval(0,public_zooexport_deferral_month) zooexport_date 
                    from part_projects pp where pprojid=%s""", (PrjId,))
    if len(prj) != 1:
        return PrintInCharte(ErrorFormat("Project doesn't exists"))
    prj = prj[0]
    if prj['ownerid'] != current_user.id and not current_user.has_role(database.AdministratorLabel):
        return PrintInCharte(ErrorFormat("Access Denied"))
    g.headcenter = "<h4>Particle Project %s : %s</h4><a href='/part/'>Particle Module Home</a>" % (
        prj['pprojid'], prj['ptitle'])
    dbsample = database.GetAll("""
      select profileid,psampleid,organizedbydeepth,filename,stationid,firstimage,lastimg,lastimgused,sampleid
          ,histobrutavailable,comment,daterecalculhistotaxo,ctd_import_datetime,sampledate,imp_descent_filtered_row
          ,imp_removed_empty_slice
          ,(select count(*) from part_histopart_det where psampleid=s.psampleid) nbrlinedet
          ,(select count(*) from part_histopart_reduit where psampleid=s.psampleid) nbrlinereduit
          ,(select count(*) from part_histocat where psampleid=s.psampleid) nbrlinetaxo
          ,(select count(*) from part_ctd where psampleid=s.psampleid) nbrlinectd
      from part_samples s
      where pprojid=%s
      order by filename desc
          """ % (PrjId,))
    min_sample_date = prj['oldestsampledate']
    visibility_text = ""
    if min_sample_date is not None:
        visibility_text += """<br> Oldest sample date is {0:%Y-%m-%d}, Visibility date is {1}
          , Particule export date is {2}, Zooplankton classification export date is {3} 
          """.format(min_sample_date,
                     "Not Defined" if prj['visibility_date'] is None else prj['visibility_date'].strftime("%Y-%m-%d"),
                     "Not Defined" if prj['partexport_date'] is None else prj['partexport_date'].strftime("%Y-%m-%d"),
                     "Not Defined" if prj['zooexport_date'] is None else prj['zooexport_date'].strftime("%Y-%m-%d"))

    # noinspection PyUnresolvedReferences
    return PrintInCharte(
        render_template('part/prj_index.html', PrjId=PrjId, dbsample=dbsample, Prj=prj, VisibilityText=visibility_text))


def ComputeHistoDet(psampleid, instrumtype):
    try:
        if instrumtype in ('uvp5', 'uvp6'):
            uvp_sample_import.GenerateParticleHistogram(psampleid)
            return " Detailed & reduced Histogram computed"
        elif instrumtype == 'lisst':
            lisst_sample_import.GenerateParticleHistogram(psampleid)
            return " Detailed & reduced Histogram computed"
        elif instrumtype == 'uvp6remote':
            uvp6remote_sample_import.GenerateParticleHistogram(psampleid)
            return " Detailed & reduced Histogram computed"
        else:
            msg = 'Invalid instrument'
    except Exception as E:
        msg = str(E)
    return " <span style='color: red;'>" + msg + "</span>"


def ComputeHistoRed(psampleid):
    return uvp_sample_import.GenerateReducedParticleHistogram(psampleid)


def ComputeZooMatch(psampleid, projid):
    if projid is not None:
        ecosample = database.GetAll("""select samples.sampleid from samples
                                        join part_samples ps on psampleid=%s
                                        where samples.projid=%s and samples.orig_id=ps.profileid""",
                                    (psampleid, int(projid)))
        if len(ecosample) == 1:
            database.ExecSQL("update part_samples set sampleid=(%s) where psampleid=(%s)",
                             (ecosample[0]['sampleid'], psampleid))
            return " Matched"
        else:
            return " <span style='color: orange;'>No match found in Ecotaxa</span>"
    else:
        return " <span style='color: red;'>" + \
               "Ecotaxa sample matching impossible if Particle project not linked to an Ecotaxa project</span>"


def ComputeZooHisto(psampleid, instrumtype):
    try:
        if instrumtype == 'uvp6remote':
            uvp6remote_sample_import.GenerateTaxonomyHistogram(psampleid)
        else:
            uvp_sample_import.GenerateTaxonomyHistogram(psampleid)
        return " Taxonomy Histogram computed"
    except Exception as E:
        logging.exception("Taxonomy Histogram can't be computed ")
        return " <span style='color: red;'>Taxonomy Histogram can't be computed : %s </span>" % (E,)


def GlobalTaxoCompute():
    # Sample Particule sans liens etabli avec Zoo qui sont liables
    samples = database.GetAll("""select ps.psampleid,pp.projid from samples
            join part_samples ps on samples.orig_id=ps.profileid
            join part_projects pp on ps.pprojid = pp.pprojid and samples.projid=pp.projid
            where ps.sampleid is null""")
    for S in samples:
        logging.info("Matching %s %s", S['psampleid'], ComputeZooMatch(S['psampleid'], S['projid']))
    # sample ayant un objet qui à été classifié depuis le dernier calcul de l'histogramme
    samples = database.GetAll("""select psampleid, daterecalculhistotaxo,pp.instrumtype
                from part_samples ps
                join part_projects pp on ps.pprojid = pp.pprojid 
                where ps.sampleid is not null
                and (
                      exists (select 1 from obj_head 
                              where obj_head.sampleid=ps.sampleid and obj_head.classif_when>ps.daterecalculhistotaxo)
                or ps.daterecalculhistotaxo is null 
                or exists (select 1 from part_histocat_lst hc 
                           where hc.psampleid=ps.psampleid and classif_id not in (select id from taxonomy)) 
                )""")
    for S in samples:
        ComputeZooHisto(S['psampleid'], S['instrumtype'])


@app.route('/part/prjcalc/<int:PrjId>', methods=['post'])
@login_required
def part_prjcalc(PrjId):
    prj = db.session.query(partdatabase.part_projects).filter_by(pprojid=PrjId).first()
    if prj.ownerid != current_user.id and not current_user.has_role(database.AdministratorLabel):
        return PrintInCharte(ErrorFormat("Access Denied"))
    txt = ""
    checked_sample_list = []
    for f in request.form:
        if f[0:2] == "s_" and request.form.get(f) == 'Y':
            checked_sample_list.append(int(f[2:]))

    app.logger.info("request.form=%s", request.form)
    app.logger.info("CheckedSampleList=%s", checked_sample_list)
    app.logger.info("dohistodet=%s,domatchecotaxa=%s,dohistotaxo=%s", gvp('dohistodet'), gvp('domatchecotaxa'),
                    gvp('dohistotaxo'))
    dbsample = database.GetAll("""select profileid,psampleid,filename,sampleid,histobrutavailable
          ,(select count(*) from part_histopart_det where psampleid=s.psampleid) nbrlinedet
          from part_samples s
          where pprojid=%s and psampleid = any (%s)""", (PrjId, checked_sample_list))
    for S in dbsample:
        prefix = "<br>{profileid} :".format(**S)
        if gvp('delete') == 'Y':
            sampleedit.delete_sample(S['psampleid'])
            txt += prefix + " deleted"
            continue
        if gvp('dohistodet') == 'Y':
            txt += prefix + ComputeHistoDet(S['psampleid'], prj.instrumtype)
        if gvp('dohistored') == 'Y':
            txt += prefix + ComputeHistoRed(S['psampleid'])
        if gvp('domatchecotaxa') == 'Y':
            txt += prefix + ComputeZooMatch(S['psampleid'], prj.projid)
        if gvp('dohistotaxo') == 'Y':
            txt += prefix + ComputeZooHisto(S['psampleid'], prj.instrumtype)
            # try:
            #     uvp_sample_import.GenerateTaxonomyHistogram(S['psampleid'])
            #     txt += prefix + " Taxonomy Histogram computed"
            # except Exception as E:
            #     txt += prefix + " <span style='color: red;'>Taxonomy Histogram can't be computed : %s </span>"%(E)
        if gvp('doctdimport') == 'Y':
            if common_import.ImportCTD(S['psampleid'], current_user.name, current_user.email):
                txt += prefix + " CTD imported"
            else:
                txt += prefix + " <span style='color: red;'>CTD No file</span>"
    # noinspection HtmlUnknownTarget
    txt += """<br><br><a href=/part/prj/%s class='btn btn-primary'>
        <span class='glyphicon glyphicon-arrow-left'></span> Back to project samples list</a>""" % PrjId
    return PrintInCharte(txt)
