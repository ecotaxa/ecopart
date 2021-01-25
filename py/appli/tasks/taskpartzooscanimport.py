# -*- coding: utf-8 -*-
import csv
import logging
import re
import time
from pathlib import Path
from flask import render_template, flash, request, g
from flask_login import current_user
import appli.part.common_sample_import
import appli.part.database as partdatabase
import appli.part.lisst_sample_import
import appli.part.prj
import appli.part.uvp6remote_sample_import as uvp6remote_sample_import
import appli.part.uvp_sample_import
from appli import db, app, database, PrintInCharte, gvp, gvg, ErrorFormat
from appli.part import LstInstrumType
from appli.tasks.taskmanager import AsyncTask, DoTaskClean


class TaskPartZooscanImport(AsyncTask):
    class Params(AsyncTask.Params):
        def __init__(self, InitStr=None):
            self.steperrors = []
            super().__init__(InitStr)
            if InitStr is None:  # Valeurs par defaut ou vide pour init
                self.pprojid = None
                self.profilelistinheader = []
                self.profiletoprocess = {}
                self.ProcessOnlyMetadata = False
                self.user_name = ""
                self.user_email = ""

    def __init__(self, task=None):
        super().__init__(task)
        self.pgcur = None
        if task is None:
            self.param = self.Params()
        else:
            self.param = self.Params(task.inputparam)

    def SPCommon(self):
        logging.info("Execute SPCommon")
        self.pgcur = db.engine.raw_connection().cursor()

    def SPStep1(self):
        logging.info("Input Param = %s" % self.param.__dict__)
        logging.info("Start Step 1")
        prj = db.session.query(partdatabase.part_projects).filter_by(pprojid=self.param.pprojid).first()
        if prj.instrumtype == 'uvp6remote':
            rsf = uvp6remote_sample_import.RemoteServerFetcher(int(self.param.pprojid))
            lst_sample = []
            for sample in self.param.profilelistinheader:
                if self.param.profiletoprocess.get(sample['profileid']):
                    lst_sample.append(sample['profileid'])
            # print(LstSample)
            lst_sample_id = rsf.FetchServerDataForProject(lst_sample)
            # print(LstSampleID)
            if not self.param.ProcessOnlyMetadata:
                for psampleid in lst_sample_id:
                    logging.info(
                        "uvp6remote Sample %d Metadata processed, Détailled histogram in progress" % (psampleid,))
                    uvp6remote_sample_import.GenerateParticleHistogram(psampleid)
                    uvp6remote_sample_import.GenerateTaxonomyHistogram(psampleid)

        else:  # process normal par traitement du repertoire des données
            nbr = 0
            for sample in self.param.profilelistinheader:
                if self.param.profiletoprocess.get(sample['profileid']):
                    nbr += 1
            if nbr == 0:
                nbr = 1  # pour éviter les div / 0
            nbr_done = 0
            for sample in self.param.profilelistinheader:
                if self.param.profiletoprocess.get(sample['profileid']):
                    logging.info("Process profile %s " % (sample['profileid']))
                    if prj.instrumtype in ('uvp5', 'uvp6'):
                        psampleid = appli.part.uvp_sample_import.CreateOrUpdateSample(self.param.pprojid, sample)
                    if prj.instrumtype == 'lisst':
                        psampleid = appli.part.lisst_sample_import.CreateOrUpdateSample(self.param.pprojid, sample)
                    self.UpdateProgress(100 * (nbr_done + 0.1) / nbr,
                                        "Metadata of profile %s  processed" % (sample['profileid']))

                    if not self.param.ProcessOnlyMetadata:
                        if prj.instrumtype in ('uvp5', 'uvp6'):
                            # noinspection PyUnboundLocalVariable
                            logging.info("UVP Sample %d Metadata processed, Raw histogram in progress" % (psampleid,))
                            appli.part.uvp_sample_import.GenerateRawHistogram(psampleid)
                            self.UpdateProgress(100 * (nbr_done + 0.6) / nbr,
                                                "Raw histogram of profile %s  processed, Particle histogram in progress"
                                                % (sample['profileid']))
                            self.UpdateProgress(100 * (nbr_done + 0.7) / nbr,
                                                "Particle histogram of profile %s  processed, CTD in progress"
                                                % (sample['profileid']))
                        if prj.instrumtype == 'lisst':
                            # noinspection PyUnboundLocalVariable
                            logging.info(
                                "LISST Sample %d Metadata processed, Particle histogram in progress" % (psampleid,))
                            appli.part.lisst_sample_import.GenerateRawHistogram(psampleid)
                            self.UpdateProgress(100 * (nbr_done + 0.7) / nbr,
                                                "Detailed histogram of profile %s  processed, CTD histogram in progress"
                                                % (sample['profileid']))

                        if prj.instrumtype in ('uvp5', 'uvp6', 'lisst'):
                            appli.part.common_sample_import.ImportCTD(psampleid, self.param.user_name,
                                                                      self.param.user_email)
                            self.UpdateProgress(100 * (nbr_done + 0.95) / nbr,
                                                "CTD of profile %s  processed" % (sample['profileid']))

                    result = appli.part.prj.ComputeHistoDet(psampleid, prj.instrumtype)
                    logging.info(result)
                    result = appli.part.prj.ComputeHistoRed(psampleid)
                    logging.info(result)
                    if prj.projid is not None:  # on essaye de matcher que si on a un projet Ecotaxa
                        appli.part.prj.ComputeZooMatch(psampleid, prj.projid)
                        appli.part.prj.ComputeZooHisto(psampleid, prj.instrumtype)

                    nbr_done += 1

        partdatabase.ComputeOldestSampleDateOnProject()
        self.task.taskstate = "Done"
        self.UpdateProgress(100, "Processing done")
        # self.task.taskstate="Error"
        # self.UpdateProgress(10,"Test Error")

    # noinspection DuplicatedCode
    def QuestionProcess(self):
        server_root = Path(app.config['SERVERLOADAREA'])
        txt = "<h1>Particle ZooScan folder Importation Task</h1>"
        errors = []
        txt += "<h3>Task Creation</h3>"
        prj = db.session.query(partdatabase.part_projects).filter_by(pprojid=gvg("p")).first()
        if prj is None:
            return PrintInCharte(ErrorFormat("This project doesn't exists"))
        if prj.instrumtype not in LstInstrumType:
            return PrintInCharte(
                ErrorFormat("Instrument type '%s' not in list : %s" % (prj.instrumtype, ','.join(LstInstrumType))))
        g.prjtitle = prj.ptitle
        g.prjprojid = prj.pprojid
        # g.prjowner=Prj.owneridrel.name
        dossier_uvp_path = server_root / prj.rawfolder
        self.param.DossierUVP = dossier_uvp_path.as_posix()

        txt = ""
        # TODO gestion sécurité
        # if Prj.CheckRight(2)==False:
        #     return PrintInCharte("ACCESS DENIED for this project");
        self.param.pprojid = gvg("p")
        dbsample = database.GetAssoc("""
            select profileid,psampleid,filename,stationid,firstimage,lastimg,lastimgused,comment,histobrutavailable
              ,(select count(*) from part_histopart_det where psampleid=s.psampleid) nbrlinedet
              ,(select count(*) from part_histopart_reduit where psampleid=s.psampleid) nbrlinereduit
              ,(select count(*) from part_histocat where psampleid=s.psampleid) nbrlinetaxo
            from part_samples s
            where pprojid=%s""" % (self.param.pprojid,))

        if prj.instrumtype == 'uvp6remote':
            fichier_header_name = "remote server"
            rsf = uvp6remote_sample_import.RemoteServerFetcher(int(self.param.pprojid))
            try:
                samples = rsf.GetServerFiles()
            except Exception as E:
                return PrintInCharte(
                    ErrorFormat(f"Error while retrieving remote file list {E} on {prj.remote_url}")
                    + f"<br><br><a href='/part/prj/{prj.pprojid}'>back on project page</a>"
                )
            # print(Samples)
            for SampleName, Sample in samples.items():
                r = {'profileid': SampleName, 'filename': Sample['files']['LPM'], 'psampleid': None}
                if r['profileid'] in dbsample:
                    r['psampleid'] = dbsample[r['profileid']]['psampleid']
                    r['histobrutavailable'] = dbsample[r['profileid']]['histobrutavailable']
                    r['nbrlinedet'] = dbsample[r['profileid']]['nbrlinedet']
                    r['nbrlinereduit'] = dbsample[r['profileid']]['nbrlinereduit']
                    r['nbrlinetaxo'] = dbsample[r['profileid']]['nbrlinetaxo']
                self.param.profilelistinheader.append(r)
                self.param.profilelistinheader = sorted(self.param.profilelistinheader, key=lambda x: x['profileid'])
        else:
            dir_name = dossier_uvp_path.name
            m = re.search(R"([^_]+)_(.*)", dir_name)
            if m is None or m.lastindex != 2:
                return PrintInCharte(ErrorFormat("Directory doesn't have standard format : xxx_yyyy"))

            fichier_header = dossier_uvp_path / "meta" / (m.group(1) + "_header_" + m.group(2) + ".txt")
            fichier_header_name = fichier_header.as_posix()

            if not fichier_header.exists():
                return PrintInCharte(ErrorFormat("Header file doens't exists pas :" + fichier_header_name))
            else:
                # print("ouverture de " + FichierHeader)
                with open(fichier_header_name, encoding="latin_1") as FichierHeaderHandler:
                    f = csv.DictReader(FichierHeaderHandler, delimiter=';')
                    for r in f:
                        # noinspection PyTypeChecker
                        r['psampleid'] = None
                        if r['profileid'] in dbsample:
                            r['psampleid'] = dbsample[r['profileid']]['psampleid']
                            r['histobrutavailable'] = dbsample[r['profileid']]['histobrutavailable']
                            r['nbrlinedet'] = dbsample[r['profileid']]['nbrlinedet']
                            r['nbrlinereduit'] = dbsample[r['profileid']]['nbrlinereduit']
                            r['nbrlinetaxo'] = dbsample[r['profileid']]['nbrlinetaxo']
                        self.param.profilelistinheader.append(r)
                        # self.param.profilelistinheader[r['profileid']]=r
                    # Tri par 4eme colonne, profileid
                    self.param.profilelistinheader = sorted(self.param.profilelistinheader,
                                                            key=lambda x: x['profileid'])

        if gvp('starttask') == "Y":
            self.param.ProcessOnlyMetadata = (gvp('onlymeta', 'N') == 'Y')
            self.param.user_name = current_user.name
            self.param.user_email = current_user.email
            for f in request.form:
                self.param.profiletoprocess[request.form.get(f)] = "Y"

            if len(self.param.profiletoprocess) == 0:
                errors.append("No sample to process selected")
            if len(errors) > 0:
                for e in errors:
                    flash(e, "error")
            else:
                return self.StartTask(self.param)
        else:  # valeurs par default
            if len(self.param.profilelistinheader) == 0:
                return PrintInCharte(ErrorFormat(f"No sample available in file {fichier_header_name}"))
            # print("%s"%(self.param.profilelistinheader))
        return render_template('task/uvpzooscanimport_create.html', header=txt, data=self.param,
                               ServerPath=gvp("ServerPath"), TxtTaxoMap=gvp("TxtTaxoMap"))

    def GetDoneExtraAction(self):
        # si le status est demandé depuis le monitoring ca veut dire que l'utilisateur est devant,
        # on efface donc la tache et on lui propose d'aller sur la classif manuelle
        prj_id = self.param.pprojid
        time.sleep(1)
        DoTaskClean(self.task.id)
        return """<a href='/part/prj/{0}' class='btn btn-primary btn-sm'  role=button>Go to Project page</a> """.format(
            prj_id)
