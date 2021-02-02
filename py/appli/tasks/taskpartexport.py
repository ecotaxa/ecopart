# -*- coding: utf-8 -*-
import bz2
import datetime
import logging
import os
import psycopg2.extras
import shutil
import zipfile
from pathlib import Path
from flask import render_template, g, flash, request
from flask_login import current_user
from appli import db, app, database, gvp, gvg, DecodeEqualList, ntcv
from appli.database import GetAll, GetAssoc
from appli.part import PartDetClassLimit, PartRedClassLimit, GetClassLimitTxt, CTDFixedColByKey, \
    GetPartClassLimitListText
from appli.part.common_sample_import import GetPathForRawHistoFile
from appli.part.drawchart import GetTaxoHistoWaterVolumeSQLExpr
from appli.part.part_main import GetFilteredSamples, PartstatsampleGetData
from appli.tasks.taskmanager import AsyncTask


def getCTDFixedCols():
    ctd_fixed_cols = list(CTDFixedColByKey.keys())
    ctd_fixed_cols.remove('datetime')
    ctd_fixed_cols.extend(["extrames%02d" % (i + 1) for i in range(20)])
    return ctd_fixed_cols


def getCTDSQL(ctd_fixed_cols):
    ctdsql = ",".join(["avg({0}) as ctd_{0} ".format(c) for c in ctd_fixed_cols])
    ctdsql = """select floor(depth/5)*5+2.5 tranche ,{0}
            from part_ctd t
            where psampleid=(%s)
            group by tranche""".format(ctdsql)
    return ctdsql


def WriteODVPartColHead(f, PartClassLimit):
    for i in range(1, len(PartClassLimit)):
        f.write(";LPM (%s) [# l-1]" % (GetClassLimitTxt(PartClassLimit, i)))
    for i in range(1, len(PartClassLimit)):
        f.write(";LPM biovolume (%s) [mm3 l-1]" % (GetClassLimitTxt(PartClassLimit, i)))
    for c in getCTDFixedCols():
        f.write(";%s" % (CTDFixedColByKey.get(c, c)))
    f.write("\n")


class TaskPartExport(AsyncTask):
    class Params(AsyncTask.Params):
        def __init__(self, InitStr=None):
            self.steperrors = []
            super().__init__(InitStr)
            if InitStr is None:  # Valeurs par defaut ou vide pour init
                self.what = None  # RAW,DET,RED
                self.fileformat = None
                self.filtres = {}
                self.redfiltres = {}
                self.user_name = ""
                self.user_email = ""
                self.samples = []
                self.samplesdict = {}
                self.excludenotliving = False
                self.aggregatefiles = False
                self.includenotvalidated = False
                self.OutFile = None
                self.putfileonftparea = ''

    def __init__(self, task=None):
        self.pgcur = None
        self.OwnerList = None
        super().__init__(task)
        if task is None:
            self.param = self.Params()
        else:
            self.param = self.Params(task.inputparam)
        self.samplesdict = {}

    def SPCommon(self):
        logging.info("Execute SPCommon for Part Export")
        self.pgcur = db.engine.raw_connection().cursor(cursor_factory=psycopg2.extras.DictCursor)

    def GetSamples(self):
        logging.info("samples = %s" % (self.param.samples,))
        # noinspection SqlShadowingAlias
        sql = """SELECT  p.cruise,s.stationid site,s.profileid station,'HDR'||s.filename rawfilename
                        ,p.instrumtype ,s.instrumsn,coalesce(ctd_origfilename,'') ctd_origfilename
                        ,to_char(s.sampledate,'YYYY-MM-DD HH24:MI:SS') sampledate
                        ,concat(p.do_name,'(',do_email,')') dataowner
                        ,s.latitude,s.longitude,s.psampleid,s.acq_pixel,acq_aa,acq_exp,p.ptitle
                        from part_samples s
                        join part_projects p on s.pprojid = p.pprojid
                        where s.psampleid in (%s)
                        order by s.profileid
                        """ % ((",".join([str(x[0]) for x in self.param.samples])),)
        samples = database.GetAll(sql)
        self.OwnerList = {S['dataowner'] for S in samples}
        return samples

    def WriteODVCommentArea(self, f):
        f.write("//<Creator>%s (%s)</Creator>\n" % (self.param.user_name, self.param.user_email))
        f.write("//<CreateTime>%s</CreateTime>\n" % (datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")))
        f.write(
            "//<DataField>Ocean</DataField>\n//<DataType>Profiles</DataType>\n//<Method>Particle abundance and volume "
            "from the Underwater Vision Profiler. The Underwater Video Profiler is designed for the quantification of "
            "particles and of large zooplankton in the water column. Light reflected by undisturbed target objects "
            "forms a dark-field image.</Method>\n")
        for Owner in self.OwnerList:
            f.write("//<Owner1>{}</Owner1>\n".format(Owner))
        f.write(
            "Cruise:METAVAR:TEXT:40;Site:METAVAR:TEXT:20;Station:METAVAR:TEXT:20;DataOwner:METAVAR:TEXT:20"
            ";Rawfilename:METAVAR:TEXT:20;Instrument:METAVAR:TEXT:10;SN:METAVAR:TEXT:10;CTDrosettefilename"
            ":METAVAR:TEXT:40;yyyy-mm-dd hh:mm:METAVAR:TEXT:40;Latitude ["
            "degrees_north]:METAVAR:DOUBLE;Longitude [degrees_east]:METAVAR:DOUBLE;Depth ["
            "m]:PRIMARYVAR:DOUBLE;Sampled volume [L]")

    def createTSVPartFile(self, nomfichier, PartClassLimit, CTDFixedCols):
        fichier = os.path.join(self.GetWorkingDir(), nomfichier)
        f = open(fichier, 'w', encoding='latin-1')
        f.write("Profile\tRawfilename\tyyyy-mm-dd hh:mm")
        if self.param.aggregatefiles:
            f.write("\tProject")
        f.write("\tDepth [m]\tSampled volume [L]")
        for i in range(1, len(PartClassLimit)):
            f.write("\tLPM (%s) [# l-1]" % (GetClassLimitTxt(PartClassLimit, i)))
        for i in range(1, len(PartClassLimit)):
            f.write("\tLPM biovolume (%s) [mm3 l-1]" % (GetClassLimitTxt(PartClassLimit, i)))
        for c in CTDFixedCols:
            f.write("\t%s" % (CTDFixedColByKey.get(c, c)))
        f.write("\n")
        return f

    def initOutFile(self, file_mask: str):
        dt_nom_fichier = datetime.datetime.now().strftime("%Y%m%d_%H_%M")
        base_file_name = file_mask.format(dt_nom_fichier)
        self.param.OutFile = base_file_name + ".zip"
        zfile = zipfile.ZipFile(os.path.join(self.GetWorkingDir(), self.param.OutFile),
                                'w', allowZip64=True, compression=zipfile.ZIP_DEFLATED)
        return dt_nom_fichier, base_file_name, zfile

    def getDephFilter(self):
        depth_filter = ""
        if self.param.redfiltres.get('filt_depthmin'):
            depth_filter += " and depth>=%d" % int(self.param.redfiltres.get('filt_depthmin'))
        if self.param.redfiltres.get('filt_depthmax'):
            depth_filter += " and depth<=%d" % int(self.param.redfiltres.get('filt_depthmax'))
        return depth_filter

    def CreateRED(self):
        logging.info("CreateRED Input Param = %s" % (self.param.__dict__,))
        as_odv = (self.param.fileformat == 'ODV')
        samples = self.GetSamples()
        dt_nom_fichier, base_file_name, zfile = self.initOutFile("export_reduced_{0:s}")
        ctd_fixed_cols = getCTDFixedCols()
        ctdsql = getCTDSQL(ctd_fixed_cols)
        depth_filter = self.getDephFilter()

        # noinspection SqlResolve
        sqlhisto = """select h.*,to_char(datetime,'YYYY-MM-DD HH24:MI:SS') fdatetime,ctd.* 
                from part_histopart_reduit h 
                left join ({0}) ctd on h.depth=ctd.tranche
                where psampleid=(%s) {1}
                order by h.datetime,h.depth """.format(ctdsql, depth_filter)
        sql_wv = """ select {0} tranche,sum(watervolume) 
                    from part_histopart_det 
                    where psampleid=%(psampleid)s 
                    group by tranche""".format(GetTaxoHistoWaterVolumeSQLExpr("depth", "middle"))
        logging.info("sql = %s" % sqlhisto)
        logging.info("samples = %s" % samples)
        # -------------------------- Fichier Particules --------------------------------
        if as_odv:
            nomfichier = base_file_name + "_PAR_odv.txt"
            fichier = os.path.join(self.GetWorkingDir(), nomfichier)
            with open(fichier, 'w', encoding='latin-1') as f:
                self.WriteODVCommentArea(f)
                WriteODVPartColHead(f, PartRedClassLimit)
                for S in samples:
                    ligne = [S['cruise'], S['site'], S['station'], S['dataowner'], S['rawfilename'], S['instrumtype'],
                             S['instrumsn'], S['ctd_origfilename'], S['sampledate'], S['latitude'], S['longitude']]
                    self.pgcur.execute(sqlhisto, [S["psampleid"], S["psampleid"]])
                    for h in self.pgcur:
                        if ntcv(h['fdatetime']) == '':
                            ligne[8] = S['sampledate']
                        else:
                            ligne[8] = h['fdatetime']
                        if not as_odv:  # si TSV
                            ligne = [S['station'], S['rawfilename'], ligne[7]]  # station + rawfilename + sampledate
                        ligne.extend([h['depth'], h['watervolume']])
                        ligne.extend((((h['class%02d' % i] / h['watervolume']) if h['watervolume'] else '') for i in
                                      range(1, len(PartRedClassLimit))))
                        ligne.extend((h['biovol%02d' % i] for i in range(1, len(PartRedClassLimit))))
                        f.write(";".join((str(ntcv(x)) for x in ligne)))
                        for c in ctd_fixed_cols:
                            f.write(";%s" % (ntcv(h["ctd_" + c])))
                        f.write("\n")
                        ligne = ['', '', '', '', '', '', '', '', '', '', '']
            zfile.write(nomfichier)
        else:  # -------- Particule TSV --------------------------------
            if self.param.aggregatefiles:  # Un seul fichier avec tous les fichiers aggrégés dedans
                nomfichier = base_file_name + "_PAR_Aggregated.tsv"
            else:
                nomfichier = None
            create_file = True
            f = None
            for S in samples:
                if not self.param.aggregatefiles:  # Un seul fichier avec tous les fichiers aggrégés dedans
                    create_file = True
                    # nommé par le profileid qui est dans le champ station
                    nomfichier = base_file_name + "_PAR_" + S['station'] + ".tsv"
                if create_file:
                    create_file = False
                    f = self.createTSVPartFile(nomfichier, PartRedClassLimit, ctd_fixed_cols)
                self.pgcur.execute(sqlhisto, [S["psampleid"], S["psampleid"]])
                for h in self.pgcur:
                    if ntcv(h['fdatetime']) == '':
                        ligne = [S['station'], S['rawfilename'], S['sampledate']]
                    else:
                        ligne = [S['station'], S['rawfilename'], h['fdatetime']]
                    if self.param.aggregatefiles:
                        ligne.extend([S['ptitle']])
                    ligne.extend([h['depth'], h['watervolume']])
                    ligne.extend((((h['class%02d' % i] / h['watervolume']) if h['watervolume'] else '') for i in
                                  range(1, len(PartRedClassLimit))))
                    ligne.extend((h['biovol%02d' % i] for i in range(1, len(PartRedClassLimit))))
                    f.write("\t".join((str(ntcv(x)) for x in ligne)))
                    for c in ctd_fixed_cols:
                        f.write("\t%s" % (ntcv(h["ctd_" + c])))
                    f.write("\n")
                if not self.param.aggregatefiles:
                    f.close()
                    zfile.write(nomfichier)
            if self.param.aggregatefiles and f:
                f.close()
                zfile.write(nomfichier)

        # --------------- Traitement fichier par categorie -------------------------------
        f = None
        taxo_list = self.param.redfiltres.get('taxo', [])
        # On liste les categories pour fixer les colonnes de l'export
        # if self.param.redfiltres.get('taxochild','')=='1' and len(TaxoList)>0:
        if len(taxo_list) > 0:
            # c'est la liste des taxo passées en paramètres
            sqllstcat = """select t.id,concat(t.name,'('||t1.name||')') nom
        , rank() over (order by t14.name,t13.name,t12.name,t11.name,t10.name,t9.name,t8.name,t7.name,t6.name,t5.name
        ,t4.name,t3.name,t2.name,t1.name,t.name)-1 idx
,concat(t14.name||'>',t13.name||'>',t12.name||'>',t11.name||'>',t10.name||'>',t9.name||'>',t8.name||'>',t7.name||'>',
     t6.name||'>',t5.name||'>',t4.name||'>',t3.name||'>',t2.name||'>',t1.name||'>',t.name) tree
                        from taxonomy t 
                        left join taxonomy t1 on t.parent_id=t1.id
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
                        left join taxonomy t14 on t13.parent_id=t14.id
                        where t.id in ({0})
                        """.format(",".join([str(x) for x in taxo_list]))
            logging.info("sqllstcat = %s" % sqllstcat)
        else:
            sample_ids_for_taxo_export = [str(x[0]) for x in self.param.samples if x[3][1] == 'Y']
            if len(sample_ids_for_taxo_export) == 0:
                sample_ids_for_taxo_export = ['-1']
            sqllstcat = """select t.id,concat(t.name,'('||t1.name||')') nom
            , rank() over (order by t14.name,t13.name,t12.name,t11.name,t10.name,t9.name,t8.name,t7.name,t6.name,t5.name
            ,t4.name,t3.name,t2.name,t1.name,t.name)-1 idx
,concat(t14.name||'>',t13.name||'>',t12.name||'>',t11.name||'>',t10.name||'>',t9.name||'>',t8.name||'>',t7.name||'>',
     t6.name||'>',t5.name||'>',t4.name||'>',t3.name||'>',t2.name||'>',t1.name||'>',t.name) tree
                    from (select distinct classif_id from part_histocat where psampleid in ( {0}) {1} ) cat
                    join taxonomy t on cat.classif_id=t.id
                    left join taxonomy t1 on t.parent_id=t1.id
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
                    left join taxonomy t14 on t13.parent_id=t14.id
                    """.format((",".join(sample_ids_for_taxo_export)), depth_filter)
            # x[3][1]==Y ==> Zoo exportable
        if self.param.redfiltres.get('taxochild', '') == '1' and len(taxo_list) > 0:
            sql_taxo_tree_from = " \njoin taxonomy t0 on h.classif_id=t0.id "
            for i in range(1, 15):
                sql_taxo_tree_from += " \nleft join taxonomy t{0} on t{1}.parent_id=t{0}.id ".format(i, i - 1)
            sqlhisto = ""
            for taxo in taxo_list:
                sql_taxo_tree_where = " and ( h.classif_id = {}  ".format(taxo)
                for i in range(1, 15):
                    sql_taxo_tree_where += " or t{0}.id= {1}".format(i, taxo)
                sql_taxo_tree_where += ")"
                if sqlhisto != "":
                    sqlhisto += " \nunion all\n "
                sqlhisto += """select {1} as classif_id, h.psampleid,h.depth,h.lineno,h.avgesd,h.nbr,h.totalbiovolume 
                            ,h.watervolume
                    from part_histocat h {2} 
                    where psampleid=%(psampleid)s {0} {3} """.format(depth_filter, taxo, sql_taxo_tree_from,
                                                                     sql_taxo_tree_where)
            # noinspection SqlResolve
            sqlhisto = """select classif_id,{0} as tranche ,avg(avgesd) avgesd,sum(nbr) nbr
                        ,sum(totalbiovolume) totalbiovolume 
                from ({1}) q
                group by classif_id,tranche
                order by tranche """.format(GetTaxoHistoWaterVolumeSQLExpr('depth', 'middle'), sqlhisto)
        else:
            # noinspection SqlShadowingAlias
            sqlhisto = """select classif_id,{1} as tranche ,avg(avgesd) avgesd,sum(nbr) nbr
                        ,sum(totalbiovolume) totalbiovolume 
                from part_histocat h where psampleid=%(psampleid)s {0}
                group by classif_id,tranche
                order by tranche """.format(depth_filter, GetTaxoHistoWaterVolumeSQLExpr('depth', 'middle'))
        lstcat = GetAssoc(sqllstcat)
        zoo_file_par_station = {}
        if as_odv:  # ------------ RED Categories AS ODV
            nomfichier = base_file_name + "_ZOO_odv.txt"
            fichier = os.path.join(self.GetWorkingDir(), nomfichier)
            with open(fichier, 'w', encoding='latin-1') as f:
                self.WriteODVCommentArea(f)
                if self.param.redfiltres.get('taxochild', '') == '1':
                    header_suffix = "w/ children"
                else:
                    header_suffix = "w/o children"
                lst_head = sorted(lstcat.values(), key=lambda cat: cat['idx'])
                for v in lst_head:
                    f.write(";%s %s [# m-3]" % (v['nom'], header_suffix))
                for v in lst_head:
                    f.write(";%s biovolume %s [mm3 l-1]" % (v['nom'], header_suffix))
                for v in lst_head:
                    f.write(";%s avgesd %s [mm]" % (v['nom'], header_suffix))
                f.write("\n")
                for S in samples:
                    if self.samplesdict[S["psampleid"]][3][1] != 'Y':  # 3 = visibility, 1 =Second char=Zoo visibility
                        continue  # pas les permission d'exporter le ZOO de ce sample le saute
                    ligne = [S['cruise'], S['site'], S['station'], S['dataowner'], S['rawfilename'], S['instrumtype'],
                             S['instrumsn'], S['ctd_origfilename'], S['sampledate'], S['latitude'], S['longitude']]
                    t = [None] * (3 * len(lstcat))
                    logging.info("sqlhisto = %s ; %s" % (sqlhisto, S["psampleid"]))
                    cat_histo = GetAll(sqlhisto, {'psampleid': S["psampleid"]})
                    water_volume = database.GetAssoc2Col(sql_wv, {'psampleid': S["psampleid"]})
                    for i in range(len(cat_histo)):
                        h = cat_histo[i]
                        idx = lstcat[h['classif_id']]['idx']
                        water_volume_tranche = water_volume.get(h['tranche'], 0)
                        if water_volume_tranche > 0:
                            t[idx] = 1000 * h['nbr'] / water_volume_tranche
                        else:
                            t[idx] = ""
                        biovolume = ""
                        if h['totalbiovolume'] and water_volume_tranche > 0:
                            biovolume = h['totalbiovolume'] / water_volume_tranche
                        t[idx + len(lstcat)] = biovolume
                        t[idx + 2 * len(lstcat)] = h['avgesd']
                        fin_ligne = False
                        if (i + 1) == len(cat_histo):  # Derniere ligne du dataset
                            fin_ligne = True
                        elif cat_histo[i]['tranche'] != cat_histo[i + 1]['tranche']:  # on change de ligne
                            fin_ligne = True

                        if fin_ligne:
                            ligne.extend([h['tranche'], water_volume_tranche])
                            ligne.extend(t)
                            f.write(";".join((str(ntcv(x)) for x in ligne)))
                            f.write("\n")
                            t = [None] * (3 * len(lstcat))
                            ligne = ['', '', '', '', '', '', '', '', '', '', '']
            zfile.write(nomfichier)
        else:  # ------------ RED Categories AS TSV
            if self.param.aggregatefiles:  # Un seul fichier avec tous les fichiers aggrégés dedans
                nomfichier = base_file_name + "_ZOO_Aggregated.tsv"
            create_file = True
            for S in samples:
                if self.samplesdict[S["psampleid"]][3][1] != 'Y':  # 3 = visibility, 1 =Second char=Zoo visibility
                    continue  # pas les permission d'exporter le ZOO de ce sample le saute
                cat_histo = GetAll(sqlhisto, {'psampleid': S["psampleid"]})
                if len(cat_histo) == 0:
                    continue  # on ne genere pas les fichiers vides.
                if not self.param.aggregatefiles:
                    create_file = True
                    nomfichier = base_file_name + "_ZOO_" + S[
                        'station'] + ".tsv"  # nommé par le profileid qui est dans le champ station
                zoo_file_par_station[S['station']] = nomfichier
                fichier = os.path.join(self.GetWorkingDir(), nomfichier)
                if create_file:
                    create_file = False
                    f = open(fichier, 'w', encoding='latin-1')
                    f.write("Profile\tRawfilename\tyyyy-mm-dd hh:mm\tDepth [m]\tSampled volume [L]")
                    if self.param.aggregatefiles:
                        f.write("\tProject")
                    lst_head = sorted(lstcat.values(), key=lambda cat: cat['idx'])
                    for v in lst_head:
                        f.write("\t%s [# m-3]" % (v['tree']))
                    for v in lst_head:
                        f.write("\t%s biovolume [mm3 l-1]" % (v['tree']))
                    for v in lst_head:
                        f.write("\t%s avgesd [mm]" % (v['tree']))
                    f.write("\n")
                t = [None] * (3 * len(lstcat))
                water_volume = database.GetAssoc2Col(sql_wv, {'psampleid': S["psampleid"]})
                for i in range(len(cat_histo)):
                    h = cat_histo[i]
                    idx = lstcat[h['classif_id']]['idx']
                    water_volume_tranche = water_volume.get(h['tranche'], 0)
                    if water_volume_tranche > 0:
                        t[idx] = 1000 * h['nbr'] / water_volume_tranche
                    else:
                        t[idx] = ""
                    biovolume = ""
                    if h['totalbiovolume'] and water_volume_tranche:
                        biovolume = h['totalbiovolume'] / water_volume_tranche
                    t[idx + len(lstcat)] = biovolume
                    t[idx + 2 * len(lstcat)] = h['avgesd']
                    fin_ligne = False
                    if (i + 1) == len(cat_histo):  # Derniere ligne du dataset
                        fin_ligne = True
                    elif cat_histo[i]['tranche'] != cat_histo[i + 1]['tranche']:  # on change de ligne
                        fin_ligne = True

                    if fin_ligne:
                        ligne = [S['station'], S['rawfilename'], S['sampledate'], h['tranche'], water_volume_tranche]
                        if self.param.aggregatefiles:
                            ligne.append(S['ptitle'])
                        ligne.extend(t)
                        f.write("\t".join((str(ntcv(x)) for x in ligne)))
                        f.write("\n")
                        t = [None] * (3 * len(lstcat))
                if not self.param.aggregatefiles:
                    f.close()
                    zfile.write(nomfichier)
            if self.param.aggregatefiles and f:
                f.close()
                zfile.write(nomfichier)

        # -------------------------- Fichier Synthèse TSV only --------------------------------
        if not as_odv:
            nomfichier = base_file_name + "_Export_metadata_summary.tsv"
            fichier = os.path.join(self.GetWorkingDir(), nomfichier)
            with open(fichier, 'w', encoding='latin-1') as f:
                f.write("profile\tCruise\tSite\tDataOwner\tRawfilename\tInstrument\tCTDrosettefilename"
                        "\tyyyy-mm-dd hh:mm\tLatitude \tLongitude\taa\texp\tPixel size\tParticle filename"
                        "\tPlankton filename\tProject\n")

                for S in samples:
                    # noinspection PyListCreation
                    ligne = [S['station'], S['cruise'], S['site'], S['dataowner'], S['rawfilename'], S['instrumtype'],
                             S['ctd_origfilename'], S['sampledate'], S['latitude'], S['longitude'], S['acq_aa'],
                             S['acq_exp'], S['acq_pixel']]
                    ligne.append(base_file_name + "_PAR_" + S['station'] + ".tsv")
                    ligne.append(zoo_file_par_station[S['station']] if S['station'] in zoo_file_par_station
                                 else "no data available")
                    ligne.append(S['ptitle'])
                    f.write("\t".join((str(ntcv(x)) for x in ligne)))
                    f.write("\n")
            zfile.write(nomfichier)

    def CreateDET(self):
        logging.info("CreateDET Input Param = %s" % (self.param.__dict__,))
        as_odv = (self.param.fileformat == 'ODV')
        # Prj=partdatabase.part_projects.query.filter_by(pprojid=self.param.pprojid).first()
        logging.info("samples = %s" % (self.param.samples,))
        samples = self.GetSamples()
        dt_nom_fichier, base_file_name, zfile = self.initOutFile("export_detailed_{0:s}")
        ctd_fixed_cols = getCTDFixedCols()
        ctdsql = getCTDSQL(ctd_fixed_cols)
        depth_filter = self.getDephFilter()
        # noinspection SqlResolve
        sqlhisto = """select h.*,to_char(datetime,'YYYY-MM-DD HH24:MI:SS') fdatetime,ctd.* 
                from part_histopart_det h 
                left join ({0}) ctd on h.depth=ctd.tranche
                where psampleid=(%s) {1}
                order by h.datetime,h.depth """.format(ctdsql, depth_filter)
        logging.info("sql = %s" % sqlhisto)
        logging.info("samples = %s" % samples)
        # -------------------------- Fichier Particules --------------------------------
        if as_odv:
            nomfichier = base_file_name + "_PAR_odv.txt"
            fichier = os.path.join(self.GetWorkingDir(), nomfichier)
            with open(fichier, 'w', encoding='latin-1') as f:
                self.WriteODVCommentArea(f)
                WriteODVPartColHead(f, PartDetClassLimit)
                for S in samples:
                    ligne = [S['cruise'], S['site'], S['station'], S['dataowner'], S['rawfilename'], S['instrumtype'],
                             S['instrumsn'], S['ctd_origfilename'], S['sampledate'], S['latitude'], S['longitude']]
                    self.pgcur.execute(sqlhisto, [S["psampleid"], S["psampleid"]])
                    for h in self.pgcur:
                        if ntcv(h['fdatetime']) == '':
                            ligne[8] = S['sampledate']
                        else:
                            ligne[8] = h['fdatetime']
                        if not as_odv:  # si TSV
                            ligne = [S['station'], S['rawfilename'], ligne[7]]  # station + rawfilename + sampledate
                        ligne.extend([h['depth'], h['watervolume']])
                        ligne.extend((((h['class%02d' % i] / h['watervolume']) if h['class%02d' % i] and h[
                            'watervolume'] else '') for i in range(1, len(PartDetClassLimit))))
                        ligne.extend((h['biovol%02d' % i] for i in range(1, len(PartDetClassLimit))))
                        f.write(";".join((str(ntcv(x)) for x in ligne)))
                        for c in ctd_fixed_cols:
                            f.write(";%s" % (ntcv(h["ctd_" + c])))
                        f.write("\n")
                        ligne = ['', '', '', '', '', '', '', '', '', '', '']
            zfile.write(nomfichier)
        else:  # -------- Particule TSV --------------------------------
            if self.param.aggregatefiles:  # Un seul fichier avec tous les fichiers aggrégés dedans
                nomfichier = base_file_name + "_PAR_Aggregated.tsv"
            else:
                nomfichier = None
            f = None
            create_file = True
            for S in samples:
                if not self.param.aggregatefiles:
                    # nommé par le profileid qui est dans le champ station
                    nomfichier = base_file_name + "_PAR_" + S['station'] + ".tsv"
                    create_file = True
                if create_file:
                    create_file = False
                    f = self.createTSVPartFile(nomfichier, PartDetClassLimit, ctd_fixed_cols)
                self.pgcur.execute(sqlhisto, [S["psampleid"], S["psampleid"]])
                for h in self.pgcur:
                    if ntcv(h['fdatetime']) == '':
                        ligne = [S['station'], S['rawfilename'], S['sampledate']]
                    else:
                        ligne = [S['station'], S['rawfilename'], h['fdatetime']]
                    if self.param.aggregatefiles:
                        ligne.extend([S['ptitle']])
                    ligne.extend([h['depth'], h['watervolume']])
                    ligne.extend(
                        (((h['class%02d' % i] / h['watervolume']) if h['class%02d' % i] and h['watervolume'] else '')
                         for i in range(1, len(PartDetClassLimit))))
                    ligne.extend((h['biovol%02d' % i] for i in range(1, len(PartDetClassLimit))))
                    f.write("\t".join((str(ntcv(x)) for x in ligne)))
                    for c in ctd_fixed_cols:
                        f.write("\t%s" % (ntcv(h["ctd_" + c])))
                    f.write("\n")
                if not self.param.aggregatefiles:
                    f.close()
                    zfile.write(nomfichier)
            if self.param.aggregatefiles and f:
                f.close()
                zfile.write(nomfichier)

        # --------------- Traitement fichier par categorie -------------------------------
        f = None
        # On liste les categories pour fixer les colonnes de l'export
        # liste toutes les cat pour les samples et la depth
        sample_ids_for_taxo_export = [str(x[0]) for x in self.param.samples if x[3][1] == 'Y']
        if len(sample_ids_for_taxo_export) == 0:
            sample_ids_for_taxo_export = ['-1']

        sqllstcat = """select distinct classif_id from part_histocat hc where psampleid in ({0}) {1} 
                            """.format((",".join(sample_ids_for_taxo_export)), depth_filter)
        # x[3][1]==Y ==> Zoo exportable
        if self.param.excludenotliving:  # On ne prend que ceux qui ne sont pas desendant de not-living
            sql_taxo_tree_from = " \njoin taxonomy t0 on hc.classif_id=t0.id "
            for i in range(1, 15):
                sql_taxo_tree_from += " \nleft join taxonomy t{0} on t{1}.parent_id=t{0}.id ".format(i, i - 1)
            sqllstcat = sqllstcat.replace(" hc", " hc" + sql_taxo_tree_from)
            for i in range(0, 15):
                sqllstcat += " and (t{0}.id is null or t{0}.name!='not-living') ".format(i)

        logging.info("sqllstcat = %s" % sqllstcat)
        lstcatwhere = GetAll(sqllstcat)
        if lstcatwhere:
            lstcatwhere = ",".join(
                (str(x[0]) for x in lstcatwhere))  # extraction de la 1ère colonne seulement et mise en format in
        else:
            lstcatwhere = "-1"
        logging.info("lstcatwhere = %s" % lstcatwhere)
        sqllstcat = """with RECURSIVE th(id ) AS (
    SELECT t.id
    FROM taxonomy t
    WHERE t.id IN ({0})
union ALL
select distinct tlink.parent_id
from th join taxonomy tlink on tlink.id=th.id
where tlink.parent_id is not null
)
select id,nom,rank() over (order by tree)-1 idx,tree
from (
SELECT t0.id,concat(t0.name,'('||t1.name||')') nom
,concat(t14.name||'>',t13.name||'>',t12.name||'>',t11.name||'>',t10.name||'>',t9.name||'>',t8.name||'>',t7.name||'>',
     t6.name||'>',t5.name||'>',t4.name||'>',t3.name||'>',t2.name||'>',t1.name||'>',t0.name) tree
from
(select distinct * from th) thd
join taxonomy t0 on thd.id=t0.id
left join taxonomy t1 on t0.parent_id=t1.id
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
left join taxonomy t14 on t13.parent_id=t14.id )q
order by tree""".format(lstcatwhere)
        lstcat = GetAssoc(sqllstcat)
        logging.info("lstcat = %s" % lstcat)

        sqlhisto = """select classif_id,lineno,psampleid,depth,watervolume ,avgesd,nbr,totalbiovolume 
                        from part_histocat h 
                        where psampleid=%(psampleid)s {0} and classif_id in ({1})
                    """.format(depth_filter, lstcatwhere)
        # Ajout calcul des cumul sur les parents via un requete récursive qui duplique les données sur toutes la
        # hierarchie puis qui somme à chaque niveau
        sqlhisto = """with recursive t(classif_id,lineno,psampleid,depth,watervolume ,avgesd,nbr,totalbiovolume)   
              as ( {0} 
            union all
            select taxonomy.parent_id classif_id,t.lineno,t.psampleid,t.depth,t.watervolume ,t.avgesd,t.nbr
                    ,t.totalbiovolume
            from taxonomy join t on taxonomy.id=t.classif_id
            where taxonomy.parent_id is not null
            )
            select classif_id,lineno,psampleid,depth,watervolume,
                  avg(avgesd) avgesd,sum(nbr) nbr,sum(totalbiovolume) totalbiovolume
            from t
            group by classif_id,lineno,psampleid,depth,watervolume              
        """.format(sqlhisto)
        sqlhisto += " order by lineno"
        zoo_file_par_station = {}
        if as_odv:
            nomfichier = base_file_name + "_ZOO_odv.txt"
            fichier = os.path.join(self.GetWorkingDir(), nomfichier)
            with open(fichier, 'w', encoding='latin-1') as f:
                self.WriteODVCommentArea(f)
                header_suffix = ""
                lst_head = sorted(lstcat.values(), key=lambda cat: cat['idx'])
                for v in lst_head:
                    f.write(";%s %s [# m-3]" % (v['nom'], header_suffix))
                for v in lst_head:
                    f.write(";%s biovolume %s [mm3 l-1]" % (v['nom'], header_suffix))
                for v in lst_head:
                    f.write(";%s avgesd %s [mm]" % (v['nom'], header_suffix))
                f.write("\n")
                for S in samples:
                    if self.samplesdict[S["psampleid"]][3][1] != 'Y':  # 3 = visibility, 1 =Second char=Zoo visibility
                        continue  # pas les permission d'exporter le ZOO de ce sample le saute
                    ligne = [S['cruise'], S['site'], S['station'], S['dataowner'], S['rawfilename'], S['instrumtype'],
                             S['instrumsn'], S['ctd_origfilename'], S['sampledate'], S['latitude'], S['longitude']]
                    t = [None] * (3 * len(lstcat))
                    logging.info("sqlhisto=%s" % sqlhisto)
                    cat_histo = GetAll(sqlhisto, {'psampleid': S["psampleid"]})
                    for i in range(len(cat_histo)):
                        h = cat_histo[i]
                        idx = lstcat[h['classif_id']]['idx']
                        if h['watervolume'] and h['watervolume'] > 0:
                            t[idx] = h['nbr'] * 1000 / h['watervolume']
                        else:
                            t[idx] = ""
                        biovolume = ""
                        if h['totalbiovolume'] and h['watervolume']:
                            biovolume = h['totalbiovolume'] / h['watervolume']
                        t[idx + len(lstcat)] = biovolume
                        t[idx + 2 * len(lstcat)] = h['avgesd']
                        fin_ligne = False
                        if (i + 1) == len(cat_histo):  # Derniere ligne du dataset
                            fin_ligne = True
                        elif cat_histo[i]['lineno'] != cat_histo[i + 1]['lineno']:  # on change de ligne
                            fin_ligne = True

                        if fin_ligne:
                            ligne.extend([h['depth'], h['watervolume']])
                            ligne.extend(t)
                            f.write(";".join((str(ntcv(x)) for x in ligne)))
                            f.write("\n")
                            t = [None] * (3 * len(lstcat))
                            ligne = ['', '', '', '', '', '', '', '', '', '', '']
            zfile.write(nomfichier)
        else:  # ------------ Categories AS TSV
            if self.param.aggregatefiles:  # Un seul fichier avec tous les fichiers aggrégés dedans
                nomfichier = base_file_name + "_ZOO_Aggregated.tsv"
            create_file = True
            for S in samples:
                if self.samplesdict[S["psampleid"]][3][1] != 'Y':  # 3 = visibility, 1 =Second char=Zoo visibility
                    continue  # pas les permission d'exporter le ZOO de ce sample le saute
                cat_histo = GetAll(sqlhisto, {'psampleid': S["psampleid"]})
                if len(cat_histo) == 0:
                    continue  # on ne genere pas les fichiers vides.
                if not self.param.aggregatefiles:
                    create_file = True
                    nomfichier = base_file_name + "_ZOO_" + S[
                        'station'] + ".tsv"  # nommé par le profileid qui est dans le champ station
                zoo_file_par_station[S['station']] = nomfichier
                fichier = os.path.join(self.GetWorkingDir(), nomfichier)
                if create_file:
                    create_file = False
                    f = open(fichier, 'w', encoding='latin-1')
                    f.write("Profile\tRawfilename\tyyyy-mm-dd hh:mm\tDepth [m]\tSampled volume [L]")
                    if self.param.aggregatefiles:
                        f.write("\tProject")
                    lst_head = sorted(lstcat.values(), key=lambda cat: cat['idx'])
                    for v in lst_head:
                        f.write("\t%s [# m-3]" % (v['tree']))
                    for v in lst_head:
                        f.write("\t%s biovolume [mm3 l-1]" % (v['tree']))
                    for v in lst_head:
                        f.write("\t%s avgesd [mm]" % (v['tree']))
                    f.write("\n")
                t = [None] * (3 * len(lstcat))
                for i in range(len(cat_histo)):
                    h = cat_histo[i]
                    idx = lstcat[h['classif_id']]['idx']
                    if h['watervolume']:
                        t[idx] = 1000 * h['nbr'] / h['watervolume']
                    else:
                        t[idx] = ""
                    biovolume = ""
                    if h['totalbiovolume'] and h['watervolume']:
                        biovolume = h['totalbiovolume'] / h['watervolume']
                    t[idx + len(lstcat)] = biovolume
                    t[idx + 2 * len(lstcat)] = h['avgesd']
                    fin_ligne = False
                    if (i + 1) == len(cat_histo):  # Derniere ligne du dataset
                        fin_ligne = True
                    elif cat_histo[i]['lineno'] != cat_histo[i + 1]['lineno']:  # on change de ligne
                        fin_ligne = True

                    if fin_ligne:
                        ligne = [S['station'], S['rawfilename'], S['sampledate'], h['depth'], h['watervolume']]
                        if self.param.aggregatefiles:
                            ligne.append(S['ptitle'])
                        ligne.extend(t)
                        f.write("\t".join((str(ntcv(x)) for x in ligne)))
                        f.write("\n")
                        t = [None] * (3 * len(lstcat))
                if not self.param.aggregatefiles:
                    f.close()
                    zfile.write(nomfichier)
            if self.param.aggregatefiles and f:
                f.close()
                zfile.write(nomfichier)

        # -------------------------- Fichier Synthèse TSV only --------------------------------
        if not as_odv:
            nomfichier = base_file_name + "_Export_metadata_summary.tsv"
            fichier = os.path.join(self.GetWorkingDir(), nomfichier)
            with open(fichier, 'w', encoding='latin-1') as f:
                f.write("profile\tCruise\tSite\tDataOwner\tRawfilename\tInstrument\tCTDrosettefilename"
                        "\tyyyy-mm-dd hh:mm\tLatitude \tLongitude\taa\texp\tPixel size\tParticle filename"
                        "\tPlankton filename\tProject\n")

                for S in samples:
                    # noinspection PyListCreation
                    ligne = [S['station'], S['cruise'], S['site'], S['dataowner'], S['rawfilename'], S['instrumtype'],
                             S['ctd_origfilename'], S['sampledate'], S['latitude'], S['longitude'], S['acq_aa'],
                             S['acq_exp'], S['acq_pixel'],
                             base_file_name + "_PAR_" + S['station'] + ".tsv"]
                    ligne.append(zoo_file_par_station[S['station']] if S['station'] in zoo_file_par_station
                                 else "no data available")
                    ligne.append(S['ptitle'])
                    f.write("\t".join((str(ntcv(x)) for x in ligne)))
                    f.write("\n")
            zfile.write(nomfichier)

    def CreateRAW(self):
        logging.info("CreateRAW Input Param = %s" % (self.param.__dict__,))
        logging.info("samples = %s" % (self.param.samples,))
        dt_nom_fichier, base_file_name, zfile = self.initOutFile("export_raw_{0:s}")
        # noinspection SqlShadowingAlias
        sql = """select s.*
          ,pp.ptitle,pp.rawfolder,concat(u.name,' ('||u.email||')') ownerid,pp.projid,pp.instrumtype,pp.op_name
          ,pp.op_email,pp.cs_name,pp.cs_email,pp.do_name,pp.do_email,pp.prj_info,pp.prj_acronym,pp.cruise,pp.ship
          ,pp.default_instrumsn,pp.default_depthoffset
          ,(select count(*) from part_histocat where psampleid=s.psampleid) nbrlinetaxo
          ,(select count(*) from part_ctd where psampleid=s.psampleid) nbrlinectd
          ,p.mappingobj
        from part_samples s
        join part_projects pp on s.pprojid=pp.pprojid
        LEFT JOIN projects p on pp.projid=p.projid
        LEFT JOIN users u on pp.ownerid=u.id
        where s.psampleid in (%s)
        order by s.profileid
        """ % ((",".join([str(x[0]) for x in self.param.samples])),)
        samples = GetAll(sql)
        # Fichiers particule
        for S in samples:
            if S['histobrutavailable'] and S['instrumtype'] in ('uvp5', 'uvp6'):
                for flashflag in ('0', '1'):
                    nomfichier = "{0}_{1}_PAR_raw_{2}{3}.tsv".format(S['filename'], S['profileid'], dt_nom_fichier,
                                                                     '_black' if flashflag == '0' else '')
                    fichier = os.path.join(self.GetWorkingDir(), nomfichier)
                    raworigfile = GetPathForRawHistoFile(S['psampleid'], flashflag)
                    if os.path.isfile(raworigfile):
                        with bz2.open(raworigfile, 'rb') as rf, open(fichier, "wb") as rawtargetfile:
                            shutil.copyfileobj(rf, rawtargetfile)
                        zfile.write(nomfichier)
                        os.unlink(nomfichier)
            if S['histobrutavailable'] and S['instrumtype'] in ['uvp6remote']:
                zfile.write(GetPathForRawHistoFile(S['psampleid']), arcname="{0}_rawfiles.zip".format(S['profileid']))
        # fichiers CTD
        ctd_file_par_p_sample_id = {}
        for S in samples:
            if S['nbrlinectd'] > 0:
                nomfichier = "{0}_{1}_CTD_raw_{2}.tsv".format(S['filename'], S['profileid'], dt_nom_fichier)
                ctd_file_par_p_sample_id[S["psampleid"]] = nomfichier
                fichier = os.path.join(self.GetWorkingDir(), nomfichier)
                with open(fichier, "wt") as f:
                    cols = sorted(CTDFixedColByKey.keys())
                    cols.remove('datetime')
                    res = GetAll("""select to_char(datetime,'YYYYMMDDHH24MISSMS') as datetime,{},{} 
                                      from part_ctd where psampleid=%s 
                                      ORDER BY lineno"""
                                 .format(",".join(cols), ",".join(["extrames%02d" % (i + 1) for i in range(20)])),
                                 (S['psampleid'],))
                    cols.remove('depth')
                    cols = ["depth", "datetime"] + cols  # passe dept et datetime en premieres colonnes
                    colsname = [CTDFixedColByKey[x] for x in cols]
                    ctd_custom_cols = DecodeEqualList(S['ctd_desc'])
                    ctd_custom_cols_keys = sorted(['extrames%s' % x for x in ctd_custom_cols.keys()])
                    cols.extend(ctd_custom_cols_keys)
                    colsname.extend([ctd_custom_cols[x[-2:]] for x in ctd_custom_cols_keys])

                    f.write("\t".join(colsname) + "\n")
                    for R in res:
                        ligne = [R[c] for c in cols]
                        f.write("\t".join((str(ntcv(x)) for x in ligne)))
                        f.write("\n")
                zfile.write(nomfichier)
        # Fichiers ZOO
        zoo_file_par_p_sample_id = {}
        for S in samples:
            depth_offset = S['default_depthoffset']
            if depth_offset is None:
                depth_offset = S['acq_depthoffset']
            if depth_offset is None:
                depth_offset = 0

            if self.samplesdict[S["psampleid"]][3][1] != 'Y':  # 3 = visibility, 1 =Second char=Zoo visibility
                continue  # pas les permission d'exporter le ZOO de ce sample le saute
            if S['nbrlinetaxo'] > 0:
                taxo_reverse_mapping = {v: k for k, v in DecodeEqualList(ntcv(S['mappingobj'])).items()}
                nomfichier = "{0}_{1}_ZOO_raw_{2}.tsv".format(S['filename'], S['profileid'], dt_nom_fichier)
                zoo_file_par_p_sample_id[S["psampleid"]] = nomfichier
                fichier = os.path.join(self.GetWorkingDir(), nomfichier)
                with open(fichier, "wt") as f:
                    # excludenotliving
                    sql = """select of.*
                        ,t0.display_name as "name", classif_qual ,ps.psampleid                        
                        ,((oh.depth_min+oh.depth_max)/2)+{DepthOffset} as depth_including_offset,objid
                        ,concat(t14.name||'>',t13.name||'>',t12.name||'>',t11.name||'>',t10.name||'>',t9.name||'>'
                                ,t8.name||'>',t7.name||'>',t6.name||'>',t5.name||'>',t4.name||'>',t3.name||'>'
                                ,t2.name||'>',t1.name||'>',t0.name) taxo_hierarchy
                      from part_samples ps
                      join obj_head oh on ps.sampleid=oh.sampleid 
                      join obj_field of on of.objfid=oh.objid                      
                        join taxonomy t0 on oh.classif_id=t0.id
                        left join taxonomy t1 on t0.parent_id=t1.id
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
                        left join taxonomy t14 on t13.parent_id=t14.id                                           
                      where ps.psampleid=%s """.format(DepthOffset=depth_offset)
                    if self.param.excludenotliving:
                        sql += """ and coalesce(t14.name,t13.name,t12.name,t11.name,t10.name,t9.name,t8.name,t7.name
                                        ,t6.name,t5.name,t4.name,t3.name,t2.name,t1.name,t0.name)!='not-living' """
                    if self.param.includenotvalidated == False:
                        sql += " and oh.classif_qual='V' "
                    res = GetAll(sql, (S['psampleid'],))
                    cols = ['orig_id', 'objid', 'name', 'taxo_hierarchy', 'classif_qual', 'depth_including_offset',
                            'psampleid']
                    extracols = list(taxo_reverse_mapping.keys())
                    extracols.sort()
                    colsname = cols[:]
                    if extracols:
                        colsname.extend(extracols)
                        cols.extend([taxo_reverse_mapping.get(x, None) for x in extracols])
                    f.write("\t".join(colsname) + "\n")
                    for R in res:
                        ligne = [R[c] if c else '' for c in cols]
                        f.write("\t".join((str(ntcv(x)) for x in ligne)))
                        f.write("\n")
                zfile.write(nomfichier)
        # Summary File
        cols = (
            'psampleid', 'pprojid', 'profileid', 'filename', 'sampleid', 'latitude', 'longitude', 'organizedbydeepth',
            'histobrutavailable',
            'qualitytaxo', 'qualitypart', 'daterecalculhistotaxo', 'winddir', 'winspeed', 'seastate', 'nebuloussness',
            'comment', 'stationid', 'firstimage',
            'lastimg', 'lastimgused', 'bottomdepth', 'yoyo', 'sampledate', 'op_sample_name', 'op_sample_email',
            'ctd_desc', 'ctd_origfilename', 'ctd_import_name',
            'ctd_import_email', 'ctd_import_datetime', 'ctd_status', 'instrumsn', 'acq_aa', 'acq_exp', 'acq_volimage',
            'acq_depthoffset', 'acq_pixel', 'acq_shutterspeed',
            'acq_smzoo', 'acq_exposure', 'acq_gain', 'acq_filedescription', 'acq_eraseborder', 'acq_tasktype',
            'acq_threshold', 'acq_choice', 'acq_disktype',
            'acq_smbase', 'acq_ratio', 'acq_descent_filter', 'acq_presure_gain', 'acq_xsize', 'acq_ysize',
            'acq_barcode', 'proc_datetime', 'proc_gamma', 'proc_soft',
            'lisst_zscat_filename', 'lisst_kernel', 'txt_data01', 'txt_data02', 'txt_data03', 'txt_data04',
            'txt_data05', 'txt_data06', 'txt_data07', 'txt_data08',
            'txt_data09', 'txt_data10', 'ptitle', 'rawfolder', 'ownerid', 'projid', 'instrumtype', 'op_name',
            'op_email', 'cs_name', 'cs_email', 'do_name', 'do_email',
            'prj_info', 'prj_acronym', 'cruise', 'ship', 'default_instrumsn', 'default_depthoffset')
        nomfichier = base_file_name + "_Export_metadata_summary.tsv"
        fichier = os.path.join(self.GetWorkingDir(), nomfichier)
        with open(fichier, 'w', encoding='latin-1') as f:
            f.write("\t".join(cols) + "\tParticle filename\tCTD filename\tPlankton filename\n")
            for S in samples:
                ligne = [S[c] for c in cols]
                for i, v in enumerate(ligne):
                    if isinstance(v, str):
                        ligne[i] = '"' + v.replace('\n', '$') + '"'
                # L = [str(S[c]).replace('\n','$') for c in cols]
                ligne.extend(
                    ["{0}_{1}_PAR_raw_{2}.tsv".format(S['filename'], S['profileid'], dt_nom_fichier)
                     if S['histobrutavailable'] else None,
                     ctd_file_par_p_sample_id[S["psampleid"]]
                     if S["psampleid"] in ctd_file_par_p_sample_id else "no data available",
                     zoo_file_par_p_sample_id[S["psampleid"]]
                     if S["psampleid"] in zoo_file_par_p_sample_id else "no data available"
                     ])
                f.write("\t".join((str(ntcv(x)) for x in ligne)))
                f.write("\n")
        zfile.write(nomfichier)

    def SPStep1(self):
        logging.info("Input Param = %s" % (self.param.__dict__,))
        # dictionnaire par sample
        self.samplesdict = {int(x[0]): x for x in self.param.samples}
        if self.param.what == "RED":
            self.CreateRED()
        elif self.param.what == "DET":
            self.CreateDET()
        elif self.param.what == "RAW":
            self.CreateRAW()
        else:
            raise Exception("Unsupported exportation type : %s" % (self.param.what,))

        if self.param.putfileonftparea == 'Y':
            fichier = Path(self.GetWorkingDir()) / self.param.OutFile
            fichierdest = Path(app.config['FTPEXPORTAREA'])
            if not fichierdest.exists():
                fichierdest.mkdir()
            nom_fichier = "task_%d_%s" % (self.task.id, self.param.OutFile)
            fichierdest = fichierdest / nom_fichier
            # fichier.rename(fichierdest) si ce sont des volumes sur des devices differents ça ne marche pas
            shutil.copyfile(fichier.as_posix(), fichierdest.as_posix())
            self.param.OutFile = ''
            self.task.taskstate = "Done"
            self.UpdateProgress(100, "Export successfull : File '%s' is available on the 'Exported_data' FTP folder"
                                % nom_fichier)
        else:
            self.task.taskstate = "Done"
            self.UpdateProgress(100, "Export successfull")
        # self.task.taskstate="Error"
        # self.UpdateProgress(10,"Test Error")

    def QuestionProcess(self):
        backurl = "/part/?{0}".format(str(request.query_string, 'utf-8'))
        txt = "<a href='{0}'>Back to Particle Module Home page</a>".format(backurl)
        txt += "<h3>Particle sample data export</h3>"
        errors = []
        for k in request.args:
            if k in ('gpr', 'gpd', 'ctd'):
                pass  # ces champs sont completement ignorés
            elif k == 'taxolb':
                self.param.redfiltres['taxo'] = request.args.getlist('taxolb')
            elif k in ('taxochild', 'filt_depthmax', 'filt_depthmin') and gvg(k, "") != "":
                self.param.redfiltres[k] = gvg(k)
            elif gvg(k, "") != "":
                self.param.filtres[k] = gvg(k, "")
        if len(self.param.filtres) > 0:
            txt_filtres = ",".join([k + "=" + v for k, v in self.param.filtres.items() if v != ""])
        else:
            txt_filtres = ""
        # applique le filtre des sample et passe la liste à la tache car besoin de currentuser
        # Les exports Reduit Particule se contente de la visibité les autres requiert l'export
        # Pour le Zoo c'est traité dans la routine d'export elle même
        self.param.samples = GetFilteredSamples(Filter=self.param.filtres,
                                                GetVisibleOnly=True,
                                                RequiredPartVisibility=('V' if self.param.what == 'RED' else 'Y'))

        if self.task.taskstep == 0:
            # Le projet de base est choisi second écran ou validation du second ecran
            if gvp('starttask') == "Y":
                # validation du second ecran
                self.param.what = gvp("what")
                self.param.user_name = current_user.name
                self.param.user_email = current_user.email
                self.param.putfileonftparea = gvp("putfileonftparea")
                if self.param.what == 'RED':
                    self.param.fileformat = gvp("fileformat")
                    self.param.aggregatefiles = (gvp("aggregatefilesr") == 'Y')
                elif self.param.what == 'DET':
                    self.param.fileformat = gvp("fileformatd")
                    self.param.excludenotliving = (gvp("excludenotlivingd") == 'Y')
                    self.param.aggregatefiles = (gvp("aggregatefilesd") == 'Y')
                elif self.param.what == 'RAW':
                    self.param.excludenotliving = (gvp("excludenotlivingr") == 'Y')
                    self.param.includenotvalidated = (gvp("includenotvalidatedr") == 'Y')
                self.param.CustomReturnLabel = "Back to particle module"
                self.param.CustomReturnURL = gvp("backurl")

                if self.param.what == '':
                    errors.append("You must select What you want to export")
                if len(errors) > 0:
                    for e in errors:
                        flash(e, "error")
                else:  # Pas d'erreur, on lance la tache
                    return self.StartTask(self.param)
            else:  # valeurs par default
                self.param.what = "RED"
                self.param.fileformat = "ODV"

            lst_users = database.GetAll("""select distinct u.email,u.name,Lower(u.name)
                        FROM users_roles ur join users u on ur.user_id=u.id
                        where ur.role_id=2
                        and u.active=TRUE and email like '%@%'
                        order by Lower(u.name)""")
            g.LstUser = ",".join(["<a href='mailto:{0}'>{0}</a></li> ".format(*r) for r in lst_users])

            statdata = PartstatsampleGetData()
            if isinstance(statdata, str):
                statdata = False
            # noinspection PyUnresolvedReferences
            html = render_template('task/partexport_create.html', header=txt, data=self.param,
                                   SampleCount=len(self.param.samples),
                                   RedFilter=",".join(("%s=%s" % (k, v) for k, v in self.param.redfiltres.items())),
                                   TxtFiltres=txt_filtres,
                                   GetPartDetClassLimitListTextResult=GetPartClassLimitListText(PartDetClassLimit),
                                   GetPartRedClassLimitListTextResult=GetPartClassLimitListText(PartRedClassLimit),
                                   statdata=statdata,
                                   backurl=backurl
                                   )

            return html

    def GetResultFile(self):
        return self.param.OutFile
