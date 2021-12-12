# -*- coding: utf-8 -*-
import bz2
import datetime
import logging
import os
import shutil
import zipfile
from pathlib import Path
from typing import List, Dict

import psycopg2.extras
from flask import render_template, g, flash, request

from .taskmanager import AsyncTask
from ..app import part_app, db
from ..constants import PartDetClassLimit, PartRedClassLimit, CTDFixedColByKey
from ..db_utils import GetAssoc2Col, GetAll
from ..funcs.uvp_sample_import import GetPathForRawHistoFile
from ..http_utils import gvg, gvp
from ..prod_or_dev import DEV_BEHAVIOR
from ..remote import EcoTaxaInstance
from ..txt_utils import GetClassLimitTxt, GetPartClassLimitListText, DecodeEqualList, ntcv
from ..urls import PART_URL
from ..views.drawchart import GetTaxoHistoWaterVolumeSQLExpr
from ..views.part_main import GetFilteredSamples, PartstatsampleGetData


def GetEmptyTaxoRow(lstcat: list, nbrbvfilled: int = 1) -> list:
    # La premiere serie est pour les LPM initialisé à 0
    # la seconde pour les biovolume qui ne sont pas dispo pour tout les instrument, dans ce cas ils sont à None
    # la troisième pour les ESD Moyen par defaut à None
    # noinspection PyTypeChecker
    if DEV_BEHAVIOR:
        return ([0] * len(lstcat)) + \
               ([0 if nbrbvfilled else None] * len(lstcat)) + \
               ([None] * len(lstcat))
    else:
        return [None for i in range(3 * len(lstcat))]


def WriteODVPartColHead(f, PartClassLimit, ctd_fixed_cols):
    for i in range(1, len(PartClassLimit)):
        f.write(";LPM (%s) [# l-1]" % (GetClassLimitTxt(PartClassLimit, i)))
    for i in range(1, len(PartClassLimit)):
        f.write(";LPM biovolume (%s) [mm3 l-1]" % (GetClassLimitTxt(PartClassLimit, i)))
    for c in ctd_fixed_cols:
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

    def SPCommon(self):
        logging.info("Execute SPCommon for Part Export")
        self.pgcur = db.engine.raw_connection().cursor(cursor_factory=psycopg2.extras.DictCursor)

    def GetSamples(self):
        logging.info("samples = %s" % (self.param.samples,))
        sql = """SELECT  p.cruise,s.stationid site,s.profileid station,'HDR'||s.filename rawfilename
                        ,p.instrumtype ,s.instrumsn,coalesce(ctd_origfilename,'') ctd_origfilename
                        ,to_char(s.sampledate,'YYYY-MM-DD HH24:MI:SS') sampledate
                        ,concat(p.do_name,'(',do_email,')') dataowner
                        ,s.latitude,s.longitude,s.psampleid,s.acq_pixel,acq_aa,acq_exp,p.ptitle"""
        if DEV_BEHAVIOR:
            sql += """
                        , (select count(totalbiovolume) 
                                       from part_histocat hc 
                                       where hc.psampleid=s.psampleid) nbrbvfilled
            """
        else:
            sql += """
                        , 1 as nbrbvfilled
            """
        sql += """ from part_samples s
                        join part_projects p on s.pprojid = p.pprojid
                        where s.psampleid in (%s)
                        order by s.profileid
                        """ % ((",".join([str(x[0]) for x in self.param.samples])),)
        samples = GetAll(sql)
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

    def writeTSVSummaryFile(self, base_file_name, samples, zfile, zoo_file_par_station):
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

    def writeOdvCategHeader(self, f, header_suffix, lstcat):
        self.WriteODVCommentArea(f)
        lst_head: List[Dict] = sorted(lstcat.values(), key=lambda cat: cat['idx'])
        for v in lst_head:
            f.write(";%s %s [# m-3]" % (v['nom'], header_suffix))
        for v in lst_head:
            f.write(";%s biovolume %s [mm3 l-1]" % (v['nom'], header_suffix))
        for v in lst_head:
            f.write(";%s avgesd %s [mm]" % (v['nom'], header_suffix))
        f.write("\n")

    def writeTSVPart(self, base_file_name, samples, sqlhisto, zfile, ctd_fixed_cols, PartClassLimit):
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
                f = self.createTSVPartFile(nomfichier, PartClassLimit, ctd_fixed_cols)
            self.pgcur.execute(sqlhisto, [S["psampleid"], S["psampleid"]])
            for h in self.pgcur:
                if ntcv(h['fdatetime']) == '':
                    ligne = [S['station'], S['rawfilename'], S['sampledate']]
                else:
                    ligne = [S['station'], S['rawfilename'], h['fdatetime']]
                if self.param.aggregatefiles:
                    ligne.extend([S['ptitle']])
                ligne.extend([h['depth'], h['watervolume']])
                if DEV_BEHAVIOR:
                    partclasslimit = PartClassLimit
                    ligne.extend((((h['class%02d' % i] / h['watervolume'])
                                   if h['class%02d' % i] is not None and h['watervolume'] else '')
                                  for i in range(1, len(partclasslimit))))
                else:
                    ligne.extend((((h['class%02d' % i] / h['watervolume'])
                                   if h['watervolume'] else '')
                                  for i in range(1, len(PartClassLimit))))
                ligne.extend((h['biovol%02d' % i] for i in range(1, len(PartClassLimit))))
                f.write("\t".join((str(ntcv(x)) for x in ligne)))
                for c in ctd_fixed_cols:
                    f.write("\t%s" % (ntcv(h["ctd_" + c])))
                f.write("\n")
            if not self.param.aggregatefiles:
                f.close()
                zfile.write(nomfichier)
        if self.param.aggregatefiles:
            f.close()
        zfile.write(nomfichier)
        return nomfichier

    def writeOdvPart(self, as_odv, base_file_name, ctd_fixed_cols, samples, sqlhisto, zfile, PartClassLimit):
        nomfichier = base_file_name + "_PAR_odv.txt"
        fichier = os.path.join(self.GetWorkingDir(), nomfichier)
        with open(fichier, 'w', encoding='latin-1') as f:
            self.WriteODVCommentArea(f)
            WriteODVPartColHead(f, PartClassLimit, ctd_fixed_cols)
            for S in samples:
                ligne = [S['cruise'], S['site'], S['station'], S['dataowner'], S['rawfilename'], S['instrumtype'],
                         S['instrumsn'], S['ctd_origfilename'], S['sampledate'], S['latitude'], S['longitude']]
                self.pgcur.execute(sqlhisto, [S["psampleid"], S["psampleid"]])
                for h in self.pgcur:
                    if ntcv(h['fdatetime']) == '':
                        ligne[8] = S['sampledate']
                    else:
                        ligne[8] = h['fdatetime']
                    ligne.extend([h['depth'], h['watervolume']])
                    if DEV_BEHAVIOR:
                        ligne.extend((((h['class%02d' % i] / h['watervolume'])
                                       if h['class%02d' % i] is not None and h['watervolume'] else '')
                                      for i in range(1, len(PartClassLimit))))
                    else:
                        ligne.extend((((h['class%02d' % i] / h['watervolume']) if h['watervolume'] else '')
                                      for i in range(1, len(PartClassLimit))))
                    # Les biovolumes proviennent de la DB (part_histopart_reduit.biovol*) directement
                    # ils sont calculés dans GenerateReducedParticleHistogram
                    biovols = [h['biovol%02d' % i] for i in range(1, len(PartClassLimit))]
                    # biovols = [round(f, 16) for f in biovols if f is not None]
                    ligne.extend(biovols)
                    str_ligne = ";".join((str(ntcv(x)) for x in ligne))
                    f.write(str_ligne)
                    for c in ctd_fixed_cols:
                        f.write(";%s" % (ntcv(h["ctd_" + c])))
                    f.write("\n")
                    ligne = ['', '', '', '', '', '', '', '', '', '', '']
        zfile.write(nomfichier)
        return nomfichier

    # noinspection DuplicatedCode
    def CreateRED(self):
        logging.info("CreateRED Input Param = %s" % (self.param.__dict__))
        as_odv = (self.param.fileformat == 'ODV')
        samples = self.GetSamples()
        dt_nom_fichier = datetime.datetime.now().strftime("%Y%m%d_%H_%M")
        base_file_name = "export_reduced_{0:s}".format(dt_nom_fichier)
        self.param.OutFile = base_file_name + ".zip"
        zfile = zipfile.ZipFile(os.path.join(self.GetWorkingDir(), self.param.OutFile)
                                , 'w', allowZip64=True, compression=zipfile.ZIP_DEFLATED)
        ctd_fixed_cols = list(CTDFixedColByKey.keys())
        ctd_fixed_cols.remove('datetime')
        ctd_fixed_cols.extend(["extrames%02d" % (i + 1) for i in range(20)])
        ctdsql = ",".join(["avg({0}) as ctd_{0} ".format(c) for c in ctd_fixed_cols])
        ctdsql = """select floor(depth/5)*5+2.5 tranche ,{0}
                from part_ctd t
                where psampleid=(%s)
                group by tranche""".format(ctdsql)
        depth_filter = ""
        if self.param.redfiltres.get('filt_depthmin'):
            depth_filter += " and depth>=%d" % int(self.param.redfiltres.get('filt_depthmin'))
        if self.param.redfiltres.get('filt_depthmax'):
            depth_filter += " and depth<=%d" % int(self.param.redfiltres.get('filt_depthmax'))

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
        # -------------------------- Fichier Particules RED --------------------------------
        if as_odv:
            nomfichier = self.writeOdvPart(as_odv, base_file_name, ctd_fixed_cols, samples, sqlhisto, zfile,
                                           PartRedClassLimit)
        else:  # -------- Particule TSV RED --------------------------------
            nomfichier = self.writeTSVPart(base_file_name, samples, sqlhisto, zfile, ctd_fixed_cols, PartRedClassLimit)

        # --------------- Traitement fichier par categorie -------------------------------
        f = None
        taxo_list = self.param.redfiltres.get('taxo', [])
        # On liste les categories pour fixer les colonnes de l'export
        if len(taxo_list) > 0:
            # c'est la liste des taxo passée en paramètre
            classif_ids = [int(x) for x in taxo_list]
            logging.info("classif_ids from params = %s" % classif_ids)
        else:
            # on liste les taxo de tous les samples concernés
            sample_ids_for_taxo_export = self.exportable_sample_ids()
            if len(sample_ids_for_taxo_export) == 0:
                sample_ids_for_taxo_export = ['-1']
            sql_cats_dans_samples = "select distinct classif_id from part_histocat where psampleid in ({0}) {1}" \
                .format((",".join(sample_ids_for_taxo_export)), depth_filter)
            classif_ids = [x for x, in GetAll(sql_cats_dans_samples)]
            logging.info("classif_ids from samples = %s" % classif_ids)
        lstcat = self.ecotaxa_if.get_taxo3(classif_ids)
        self._add_idx_in_category_dict(lstcat, False)
        logging.info("lstcat = %s" % lstcat)
        if self.param.redfiltres.get('taxochild', '') == '1' and len(taxo_list) > 0:
            # Filtre sur les catégories, _avec aggrégation sur leurs enfants_
            sqlhisto = ""
            for taxo in taxo_list:
                child_classif_ids = [str(x) for x in self.ecotaxa_if.get_taxo_subtree(int(taxo))]
                logging.info("%d descendants for %d", len(child_classif_ids), taxo)
                sql_taxo_tree_where = " and h.classif_id in (" + ",".join(child_classif_ids) + ")"
                if sqlhisto != "":
                    sqlhisto += " \nunion all\n "
                sqlhisto += """select {1} as classif_id, h.psampleid,h.depth,h.lineno,h.avgesd,h.nbr,h.totalbiovolume ,h.watervolume
                    from part_histocat h
                    where psampleid=%(psampleid)s {0} {2} """.format(depth_filter, taxo, sql_taxo_tree_where)
            sqlhisto = """select classif_id,{0} as tranche ,avg(avgesd) avgesd,sum(nbr) nbr,sum(totalbiovolume) totalbiovolume 
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

        if as_odv:  # ------------ RED Categories AS ODV
            if DEV_BEHAVIOR:
                if self.param.redfiltres.get('taxochild', '') == '1':
                    header_suffix = "w/ children"
                else:
                    header_suffix = "w/o children"
            nomfichier = base_file_name + "_ZOO_odv.txt"
            fichier = os.path.join(self.GetWorkingDir(), nomfichier)
            with open(fichier, 'w', encoding='latin-1') as f:
                self.writeOdvCategHeader(f, header_suffix, lstcat)
                for S in samples:
                    if not self.is_zoo_exportable(S["psampleid"]):
                        continue  # pas les permission d'exporter le ZOO de ce sample on le saute
                    ligne = [S['cruise'], S['site'], S['station'], S['dataowner'], S['rawfilename'],
                             S['instrumtype'],
                             S['instrumsn'], S['ctd_origfilename'], S['sampledate'], S['latitude'], S['longitude']]
                    t = GetEmptyTaxoRow(lstcat, S['nbrbvfilled'])
                    logging.info("sqlhisto = %s ; %s" % (sqlhisto, S["psampleid"]))
                    cat_histo = GetAll(sqlhisto, {'psampleid': S["psampleid"]})
                    water_volume = GetAssoc2Col(sql_wv, {'psampleid': S["psampleid"]})
                    for i in range(len(cat_histo)):
                        h = cat_histo[i]
                        idx = lstcat[h['classif_id']]['idx']
                        water_volume_tranche = water_volume.get(h['tranche'], 0)
                        if water_volume_tranche > 0:
                            t[idx] = 1000 * h['nbr'] / water_volume_tranche
                        else:
                            t[idx] = ""
                        biovolume = ""
                        if h['totalbiovolume'] is not None and water_volume_tranche > 0:
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
                            t = GetEmptyTaxoRow(lstcat, S['nbrbvfilled'])
                            ligne = ['', '', '', '', '', '', '', '', '', '', '']
            zfile.write(nomfichier)
        else:  # ------------ RED Categories AS TSV
            # TODO: Much copy/paste from above.
            zoo_file_par_station = {}
            if self.param.aggregatefiles:  # Un seul fichier avec tous les fichiers aggrégés dedans
                nomfichier = base_file_name + "_ZOO_Aggregated.tsv"
            create_file = True
            for S in samples:
                if not self.is_zoo_exportable(S["psampleid"]):
                    continue  # pas la permission d'exporter le ZOO de ce sample on le saute
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
                t = GetEmptyTaxoRow(lstcat, S['nbrbvfilled'])
                water_volume = GetAssoc2Col(sql_wv, {'psampleid': S["psampleid"]})
                for i in range(len(cat_histo)):
                    h = cat_histo[i]
                    idx = lstcat[h['classif_id']]['idx']
                    water_volume_tranche = water_volume.get(h['tranche'], 0)
                    if water_volume_tranche > 0:
                        t[idx] = 1000 * h['nbr'] / water_volume_tranche
                    else:
                        t[idx] = ""
                    biovolume = ""
                    if h['totalbiovolume'] is not None and water_volume_tranche > 0:
                        biovolume = h['totalbiovolume'] / water_volume_tranche
                    t[idx + len(lstcat)] = biovolume
                    t[idx + 2 * len(lstcat)] = h['avgesd']
                    fin_ligne = False
                    if (i + 1) == len(cat_histo):  # Derniere ligne du dataset
                        fin_ligne = True
                    elif cat_histo[i]['tranche'] != cat_histo[i + 1]['tranche']:  # on change de ligne
                        fin_ligne = True

                    if fin_ligne:
                        ligne = [S['station'], S['rawfilename'], S['sampledate'], h['tranche'],
                                 water_volume_tranche]
                        if self.param.aggregatefiles:
                            ligne.append(S['ptitle'])
                        ligne.extend(t)
                        f.write("\t".join((str(ntcv(x)) for x in ligne)))
                        f.write("\n")
                        t = GetEmptyTaxoRow(lstcat, S['nbrbvfilled'])
                if not self.param.aggregatefiles:
                    f.close()
                    zfile.write(nomfichier)
            if self.param.aggregatefiles and f:
                f.close()
                zfile.write(nomfichier)

        # -------------------------- Fichier Synthèse TSV only --------------------------------
        if not as_odv:
            self.writeTSVSummaryFile(base_file_name, samples, zfile, zoo_file_par_station)

    def _add_idx_in_category_dict(self, cats_dict, order_by_tree):
        """ Rajoute une clef d'ordre dans chaque dictionnaire, valeur du dictionnaire.
            On s'en sert pour avoir un ordre fixé des taxa dans les reports. """
        if DEV_BEHAVIOR and not order_by_tree:
            # Emulation du SQL: rank() over (order by t14.name,t13.name,t12.name,t11.name,t10.name,t9.name,t8.name,
            #  t7.name,t6.name,t5.name,t4.name,t3.name,t2.name,t1.name,t.name)-1 idx.
            # Du fait des outer joins, il y a de nombreux NULLs, l'ordre implicite est NULLs last,
            # que l'on émule avec une constante "loin" dans l'alphabet.
            def ordr(cat):
                lineage = tuple(cat['tree'].split(">"))
                return tuple((chr(65536),) * (14 - len(lineage)) + lineage)
        else:
            # Ordre 'naturel'
            ordr = lambda cat: cat['tree']
        cats_vals: List[Dict] = sorted(cats_dict.values(), key=ordr)
        for v, ndx in zip(cats_vals, range(len(cats_vals))):
            v['idx'] = ndx

    def CreateDET(self):
        logging.info("CreateDET Input Param = %s" % (self.param.__dict__,))
        as_odv = (self.param.fileformat == 'ODV')
        # Prj=partdatabase.part_projects.query.filter_by(pprojid=self.param.pprojid).first()
        logging.info("samples = %s" % self.param.samples)
        samples = self.GetSamples()
        dt_nom_fichier = datetime.datetime.now().strftime("%Y%m%d_%H_%M")
        base_file_name = "export_detailed_{0:s}".format(dt_nom_fichier)
        self.param.OutFile = base_file_name + ".zip"
        zfile = zipfile.ZipFile(os.path.join(self.GetWorkingDir(), self.param.OutFile)
                                , 'w', allowZip64=True, compression=zipfile.ZIP_DEFLATED)
        ctd_fixed_cols = list(CTDFixedColByKey.keys())
        ctd_fixed_cols.remove('datetime')
        ctd_fixed_cols.extend(["extrames%02d" % (i + 1) for i in range(20)])
        ctdsql = ",".join(["avg({0}) as ctd_{0} ".format(c) for c in ctd_fixed_cols])
        ctdsql = """select floor(depth/5)*5+2.5 tranche ,{0}
                from part_ctd t
                where psampleid=(%s)
                group by tranche""".format(ctdsql)
        depth_filter = ""
        if self.param.redfiltres.get('filt_depthmin'):
            depth_filter += " and depth>=%d" % int(self.param.redfiltres.get('filt_depthmin'))
        if self.param.redfiltres.get('filt_depthmax'):
            depth_filter += " and depth<=%d" % int(self.param.redfiltres.get('filt_depthmax'))

        sqlhisto = """select h.*,to_char(datetime,'YYYY-MM-DD HH24:MI:SS') fdatetime,ctd.* 
                from part_histopart_det h 
                left join ({0}) ctd on h.depth=ctd.tranche
                where psampleid=(%s) {1}
                order by h.datetime,h.depth """.format(ctdsql, depth_filter)
        logging.info("sql = %s" % sqlhisto)
        logging.info("samples = %s" % samples)
        # -------------------------- Fichier Particules DET --------------------------------
        if as_odv:
            nomfichier = self.writeOdvPart(as_odv, base_file_name, ctd_fixed_cols, samples, sqlhisto, zfile,
                                           PartDetClassLimit)
        else:  # -------- Particule TSV DET --------------------------------
            nomfichier = self.writeTSVPart(base_file_name, samples, sqlhisto, zfile, ctd_fixed_cols, PartDetClassLimit)
        # --------------- Traitement fichier par categorie -------------------------------
        f = None
        # On liste les categories pour fixer les colonnes de l'export
        # liste toutes les cat pour les samples et la depth
        sample_ids_for_taxo_export = self.exportable_sample_ids()
        if len(sample_ids_for_taxo_export) == 0:
            sample_ids_for_taxo_export = ['-1']

        # TODO: dup code
        sql_cats_dans_samples = """select distinct classif_id 
                                     from part_histocat hc 
                                    where psampleid in ({0}) {1} 
                            """.format((",".join(sample_ids_for_taxo_export)), depth_filter)
        classif_ids_dans_samples = [x for x, in GetAll(sql_cats_dans_samples)]
        if self.param.excludenotliving:
            # On ne prend que ceux qui ne sont pas descendants de not-living
            logging.info("classif_ids to filter: %s", sorted(classif_ids_dans_samples))
            ecotaxa_cats = self.ecotaxa_if.get_taxo2(classif_ids_dans_samples)
            classif_ids_dans_samples = [a_cat["classif_id"]
                                        for a_cat in ecotaxa_cats
                                        if not a_cat["tree"].startswith("not-living>")]
            logging.info("Filtered classif_ids: %s", sorted(classif_ids_dans_samples))
        if len(classif_ids_dans_samples) == 0:
            # Défaut à 'rien ne matche'
            classif_ids_dans_samples = [-1]

        lstcatwhere = ",".join((str(x) for x in classif_ids_dans_samples))
        logging.info("DET lstcatwhere = %s" % lstcatwhere)

        # On récupère toutes les catégories parentes de toutes les catégories présentes,
        # car elles vont apparaître dans le résultat final
        lstcat = self.ecotaxa_if.get_taxo_all_parents(classif_ids_dans_samples)
        self._add_idx_in_category_dict(lstcat, True)
        logging.info("DET %s lstcat = %s" % (len(lstcat), lstcat))

        sql_histo = """select classif_id, lineno, psampleid, depth, watervolume, avgesd, nbr, totalbiovolume 
        from part_histocat h 
        where psampleid=%(psampleid)s {0} and classif_id in ({1}) """.format(depth_filter, lstcatwhere)
        # Ajout calcul des cumul sur les parents via une requête récursive qui duplique les données sur toute la hiérarchie
        # Puis qui aggrège à chaque niveau (somme/moyenne)
        mini_taxo = ["(%s,%s)" % (r["id"], r["pid"] if r["pid"] else "NULL")
                     for r in lstcat.values()]
        sqlhisto = """WITH recursive subtaxo (id,parent_id) AS (VALUES %s),
        """ % ",".join(mini_taxo)
        sqlhisto += """    h4t(classif_id, lineno, psampleid, depth, watervolume, avgesd, nbr, totalbiovolume)   
              as ( {0} 
            union all
            select txo.parent_id classif_id, h4t.lineno, h4t.psampleid, 
                   h4t.depth, h4t.watervolume, h4t.avgesd, h4t.nbr, h4t.totalbiovolume
              from subtaxo txo join h4t on txo.id = h4t.classif_id
             where txo.parent_id is not null
            )
            select classif_id, lineno, psampleid, 
                   depth, watervolume, avg(avgesd) avgesd, sum(nbr) nbr, sum(totalbiovolume) totalbiovolume
            from h4t
            group by classif_id, lineno, psampleid, depth, watervolume              
        """.format(sql_histo)
        sqlhisto += " order by lineno"
        if as_odv:
            nomfichier = base_file_name + "_ZOO_odv.txt"
            fichier = os.path.join(self.GetWorkingDir(), nomfichier)
            with open(fichier, 'w', encoding='latin-1') as f:
                header_suffix = ""
                self.writeOdvCategHeader(f, header_suffix, lstcat)
                for S in samples:
                    if not self.is_zoo_exportable(S["psampleid"]):
                        continue  # pas les permission d'exporter le ZOO de ce sample le saute
                    ligne = [S['cruise'], S['site'], S['station'], S['dataowner'], S['rawfilename'], S['instrumtype'],
                             S['instrumsn'], S['ctd_origfilename'], S['sampledate'], S['latitude'], S['longitude']]
                    t = GetEmptyTaxoRow(lstcat, S['nbrbvfilled'])
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
                            t = GetEmptyTaxoRow(lstcat, S['nbrbvfilled'])
                            ligne = ['', '', '', '', '', '', '', '', '', '', '']
            zfile.write(nomfichier)
        else:  # ------------ Categories AS TSV
            zoo_file_par_station = {}
            if self.param.aggregatefiles:  # Un seul fichier avec tous les fichiers aggrégés dedans
                nomfichier = base_file_name + "_ZOO_Aggregated.tsv"
            create_file = True
            for S in samples:
                if not self.is_zoo_exportable(S["psampleid"]):
                    continue  # pas les permission d'exporter le ZOO de ce sample le saute
                cat_histo = GetAll(sqlhisto, {'psampleid': S["psampleid"]})
                if len(cat_histo) == 0: continue  # on ne genere pas les fichiers vides.
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
                t = GetEmptyTaxoRow(lstcat, S['nbrbvfilled'])
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
                        t = GetEmptyTaxoRow(lstcat, S['nbrbvfilled'])
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
                f.write(
                    "profile\tCruise\tSite\tDataOwner\tRawfilename\tInstrument\tCTDrosettefilename\tyyyy-mm-dd hh:mm\tLatitude \tLongitude\taa\texp\tPixel size\tParticle filename\tPlankton filename\tProject\n")

                for S in samples:
                    ligne = [S['station'], S['cruise'], S['site'], S['dataowner'], S['rawfilename'], S['instrumtype'],
                             S['ctd_origfilename'], S['sampledate'], S['latitude'], S['longitude'], S['acq_aa'],
                             S['acq_exp'], S['acq_pixel']
                        , base_file_name + "_PAR_" + S['station'] + ".tsv"]
                    ligne.append(
                        zoo_file_par_station[S['station']] if S[
                                                                  'station'] in zoo_file_par_station else "no data available")
                    ligne.append(S['ptitle'])
                    f.write("\t".join((str(ntcv(x)) for x in ligne)))
                    f.write("\n")
            zfile.write(nomfichier)

    def CreateRAW(self):
        logging.info("CreateRAW Input Param = %s" % (self.param.__dict__,))
        logging.info("samples = %s" % (self.param.samples))
        dt_nom_fichier = datetime.datetime.now().strftime("%Y%m%d_%H_%M")
        base_file_name = "export_raw_{0:s}".format(dt_nom_fichier)
        self.param.OutFile = base_file_name + ".zip"
        zfile = zipfile.ZipFile(os.path.join(self.GetWorkingDir(), self.param.OutFile)
                                , 'w', allowZip64=True, compression=zipfile.ZIP_DEFLATED)
        self.UpdateProgress(10, "Getting samples")
        sql = """select s.*,
          pp.ptitle, pp.rawfolder, pp.ownerid as owner_id, pp.projid, pp.instrumtype, pp.op_name, 
          pp.op_email, pp.cs_name, pp.cs_email, pp.do_name, pp.do_email, pp.prj_info, pp.prj_acronym, 
          pp.cruise, pp.ship, pp.default_instrumsn, pp.default_depthoffset,
          (select count(*) from part_histocat where psampleid=s.psampleid) nbrlinetaxo,
          (select count(*) from part_ctd where psampleid=s.psampleid) nbrlinectd,
          null::varchar as ownerid -- placeholder
        from part_samples s
        join part_projects pp on s.pprojid=pp.pprojid
        where s.psampleid in (%s)
        order by s.profileid
        """ % ((",".join([str(x[0]) for x in self.param.samples])),)
        samples = GetAll(sql)
        # On complète les users si possible
        for S in samples:
            owner_id = S['owner_id']
            person = self.ecotaxa_if.get_user_by_id(owner_id)
            if person is None:
                S['ownerid'] = "Private"
            else:
                S['ownerid'] = person.name + " (" + person.email + ")"
        # On a tous les samples EcoPart voulus, on récupère les projets EcoTaxa correspondants
        zoo_projs = {}  # EcoTaxa project (value) à partir de EcoPart project ID (key)
        self.UpdateProgress(20, "Fetching projects")
        for S in samples:
            ecotaxa_project_id = S["projid"]
            if ecotaxa_project_id is None:
                continue
            part_project_id = S["pprojid"]
            if part_project_id not in zoo_projs:
                zoo_projs[part_project_id] = self.ecotaxa_if.get_project(ecotaxa_project_id)
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
            if DEV_BEHAVIOR:
                ok_for_exp = ('uvp6remote',)
            else:
                # Ca ressemble à un bug en prod', car e.g., 'uvp6' est dans 'uvp6remote'
                ok_for_exp = ('uvp6remote')
            if S['histobrutavailable'] and S['instrumtype'] in ok_for_exp:
                zfile.write(GetPathForRawHistoFile(S['psampleid']),
                            arcname="{0}_rawfiles.zip".format(S['profileid']))
        # Fichiers CTD
        ctd_file_par_p_sample_id = {}
        self.UpdateProgress(30, "Producing CTD files")
        for S in samples:
            psampleid = S["psampleid"]
            if S['nbrlinectd'] > 0:
                nomfichier = "{0}_{1}_CTD_raw_{2}.tsv".format(S['filename'], S['profileid'], dt_nom_fichier)
                ctd_file_par_p_sample_id[psampleid] = nomfichier
                fichier = os.path.join(self.GetWorkingDir(), nomfichier)
                with open(fichier, "wt") as f:
                    cols = sorted(CTDFixedColByKey.keys())
                    cols.remove('datetime')
                    res = GetAll("""select to_char(datetime,'YYYYMMDDHH24MISSMS') as datetime,{},{} 
                                      from part_ctd where psampleid=%s 
                                      ORDER BY lineno""".format(
                        ",".join(cols), ",".join(["extrames%02d" % (i + 1) for i in range(20)]))
                        , (psampleid,))
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
        nb_samples = len(samples)
        taxo_cache = {}  # On évite de faire plein de fois des queries API qui rendent le même résultat
        for sample_num, S in enumerate(samples, 1):
            self.UpdateProgress(40 + (50 * sample_num / nb_samples),
                                "Producing ZOO file %d/%d" % (sample_num, nb_samples))
            psampleid = S["psampleid"]
            depth_offset = S['default_depthoffset']
            if depth_offset is None:
                depth_offset = S['acq_depthoffset']
            if depth_offset is None:
                depth_offset = 0

            if not self.is_zoo_exportable(psampleid):
                continue  # pas les permission d'exporter le ZOO de ce sample, on le saute
            if S['nbrlinetaxo'] > 0:
                sampleid = S['sampleid']  # Get EcoTaxa sample num
                ecotaxa_proj = zoo_projs.get(S["pprojid"])
                if ecotaxa_proj is None:
                    # Le projet EcoTaxa associé n'a pas pu être lu ou n'existe pas
                    # assert sampleid is None, "Sample associé avec projet non associé"
                    taxo_reverse_mapping = {}
                else:
                    taxo_reverse_mapping = ecotaxa_proj.obj_free_cols  # key: free column name, value: DB column name
                nomfichier = "{0}_{1}_ZOO_raw_{2}.tsv".format(S['filename'], S['profileid'], dt_nom_fichier)
                zoo_file_par_p_sample_id[psampleid] = nomfichier
                fichier = os.path.join(self.GetWorkingDir(), nomfichier)
                with open(fichier, "wt") as f:
                    # Query the related objects
                    queried_columns = ["obj.objid", "obj.orig_id", "obj.classif_id", "obj.classif_qual",
                                       "obj.depth_min", "obj.depth_max",
                                       "txo.display_name"]
                    queried_columns.extend(["fre.%s" % free_col for free_col in taxo_reverse_mapping.keys()])
                    if ecotaxa_proj is None:
                        api_res = []
                    else:
                        api_res = self.ecotaxa_if.get_objects_for_sample(ecotaxa_proj.projid, sampleid, queried_columns,
                                                                         not self.param.includenotvalidated)
                    # Do some calculations/filtering for returned data
                    res = []
                    for an_obj in api_res:
                        an_obj["name"] = an_obj["display_name"]
                        an_obj["depth_including_offset"] = (an_obj["depth_min"] + an_obj[
                            "depth_max"]) / 2 + depth_offset
                        an_obj["psampleid"] = psampleid
                        classif_id = an_obj["classif_id"]
                        if classif_id is None:
                            continue
                        hier = self.ecotaxa_if.get_taxo_tree(classif_id, taxo_cache)
                        if self.param.excludenotliving:
                            if hier.startswith('not-living'):
                                continue
                        an_obj["taxo_hierarchy"] = hier
                        res.append(an_obj)
                    # Produce text file from gathered data
                    cols = ['orig_id', 'objid', 'name', 'taxo_hierarchy', 'classif_qual', 'depth_including_offset',
                            'psampleid']
                    extracols = list(taxo_reverse_mapping.keys())
                    extracols.sort()
                    if extracols:
                        cols.extend(extracols)
                    f.write("\t".join(cols) + "\n")
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
        self.UpdateProgress(90, "Producing summary files")
        with open(fichier, 'w', encoding='latin-1') as f:
            f.write("\t".join(cols) + "\tParticle filename\tCTD filename\tPlankton filename\n")
            for S in samples:
                psampleid = S["psampleid"]
                ligne = [S[c] for c in cols]
                for i, v in enumerate(ligne):
                    if isinstance(v, str):
                        ligne[i] = '"' + v.replace('\n', '$') + '"'
                # L = [str(S[c]).replace('\n','$') for c in cols]
                ligne.extend(
                    ["{0}_{1}_PAR_raw_{2}.tsv".format(S['filename'], S['profileid'], dt_nom_fichier)
                     if S['histobrutavailable'] else None,
                     ctd_file_par_p_sample_id[psampleid]
                     if psampleid in ctd_file_par_p_sample_id else "no data available",
                     zoo_file_par_p_sample_id[psampleid]
                     if psampleid in zoo_file_par_p_sample_id else "no data available"
                     ])
                f.write("\t".join((str(ntcv(x)) for x in ligne)))
                f.write("\n")
        zfile.write(nomfichier)

    def is_zoo_exportable(self, psampleid):
        # 3 = visibility, 1 =Second char=Zoo visibility
        return self.samplesdict[psampleid][3][1] == 'Y'

    def exportable_sample_ids(self):
        return [str(x[0]) for x in self.param.samples if x[3][1] == 'Y']

    def SPStep1(self):
        logging.info("Input Param = %s" % (self.param.__dict__,))
        self.ecotaxa_if = EcoTaxaInstance(self.cookie)
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
            fichierdest = Path(part_app.config['FTPEXPORTAREA'])
            if not fichierdest.exists():
                fichierdest.mkdir()
            nom_fichier = "task_%d_%s" % (self.task.id, self.param.OutFile)
            fichierdest = fichierdest / nom_fichier
            # fichier.rename(fichierdest) si ce sont des volumes sur des devices differents ça ne marche pas
            shutil.copyfile(fichier.as_posix(), fichierdest.as_posix())
            self.param.OutFile = ''
            self.task.taskstate = "Done"
            self.UpdateProgress(100, "Export successful : File '%s' is available on "
                                     "the 'Exported_data' FTP folder" % nom_fichier)
        else:
            self.task.taskstate = "Done"
            self.UpdateProgress(100, "Export successful")
        # self.task.taskstate="Error"
        # self.UpdateProgress(10,"Test Error")

    def QuestionProcess(self):
        ecotaxa_if = EcoTaxaInstance(request)
        backurl = ("%s?{0}" % PART_URL).format(str(request.query_string, 'utf-8'))
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
        # applique le filtre des sample et passe la liste à la tache car besoin du 'current user' (ou pas!)
        self.param.samples, _ignored = GetFilteredSamples(ecotaxa_if=ecotaxa_if, Filter=self.param.filtres,
                                                          GetVisibleOnly=True
                                                          # Les exports Reduit Particule se contente de la visibité les autres requiert l'export
                                                          # Pour le Zoo c'est traité dans la routine d'export elle même
                                                          , MinimumPartVisibility=(
                'V' if self.param.what == 'RED' else 'Y'))

        if self.task.taskstep == 0:
            # Le projet de base est choisi second écran ou validation du second ecran
            if gvp('starttask') == "Y":
                # validation du second ecran
                ecotaxa_user = ecotaxa_if.get_current_user()
                self.param.what = gvp("what")
                # TODO: Not really needed, it's just for writing author in the ODV header,
                # and in the task subprocess we have current user as well.
                self.param.user_name = ecotaxa_user.name
                self.param.user_email = ecotaxa_user.email
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

            # Tous les "Users Administrator"
            lst_users = ecotaxa_if.get_users_admins()
            g.LstUser = ",".join(["<a href='mailto:{0}'>{0}</a></li> ".format(r.email) for r in lst_users])

            # On récolte les stats sur la sélection courante
            statdata = PartstatsampleGetData(ecotaxa_if)
            if isinstance(statdata, str):
                statdata = False
            # noinspection PyUnresolvedReferences
            html = render_template('tasks/partexport_create.html', header=txt, data=self.param,
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
