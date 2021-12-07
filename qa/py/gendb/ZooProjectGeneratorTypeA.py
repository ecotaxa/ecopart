from gendb.ZooProjectGenerator import ZooProjectGenerator
from Zoo_DB import database
from part_app.app import db
from datetime import datetime, timedelta
import logging


# not-living>plastic>fiber   fiber<plastic
# not-living>detritus>fiber  fiber<detritus
# living>Eukaryota>Harosa>Rhizaria>Retaria>Polycystinea>Collodaria>solitaryblack
# living>Eukaryota>Harosa>Rhizaria>Retaria>Polycystinea>Collodaria>solitarygrey
# living>Eukaryota>Harosa>Rhizaria>Retaria>Acantharea
# living>Eukaryota>Opisthokonta>Holomycota>Fungi>Ascomycota>Pezizomycotina>Dothideomycetes>Aulographina
# Not validated
# living>Eukaryota>Archaeplastida>Viridiplantae>Chlorophyta>Ulvophyceae>Bryopsidales>Halimeda>Halimeda hederacea
from part_app.db_utils import GetAll


class ZooProjectGeneratorTypeA(ZooProjectGenerator):
    def __init__(self):
        super().__init__()

    def CreateSample(self, SampleName) -> database.Samples:
        Sample = database.Samples()
        Sample.projid = self.projid
        # C'est utilisé lors du match avec EcoPart
        Sample.orig_id = SampleName
        db.session.add(Sample)
        db.session.commit()
        # Creation d'une Acq unique pour le projet
        self.Acq = database.Acquisitions()
        # self.Acq.projid = self.projid
        self.Acq.acquisid = Sample.sampleid
        self.Acq.acq_sample_id = Sample.sampleid
        self.Acq.orig_id = 'Acq01'
        setattr(self.Acq, self.RevMapAcq['aa'], self.aa)
        setattr(self.Acq, self.RevMapAcq['exp'], self.exp)
        setattr(self.Acq, self.RevMapAcq['pixel'], self.pixel)
        setattr(self.Acq, self.RevMapAcq['volimage'], self.volimage)
        db.session.add(self.Acq)
        db.session.commit()
        self.Acquisid = self.Acq.acquisid

        return Sample

    def CreateOject(self, Sampleid, Taxo, Depth, DateTime, Area, Qualite='V'):
        objid = self.obj_seq_cache.next()
        Obj = database.Objects()
        Obj.objid = objid
        Obj.sampleid = Sampleid
        Obj.acquisid = Sampleid  # c'est les mêmes
        Obj.orig_id = "MyOrigID"
        Obj.acquisid = self.Acquisid
        Obj.classif_id = self.GetTaxoByName(Taxo)
        Obj.classif_qual = Qualite
        Obj.depth_min = Depth
        Obj.depth_max = Depth
        Obj.imgcount = 0
        Obj.objdate = DateTime.date()
        Obj.objtime = DateTime.time()
        # Obj= {'objid':objid # pour l'approche avec bulk_insert_mappings
        #     , 'projid':self.projid
        #     ,'sampleid':Sampleid
        #     ,'acquisid':self.Acquisid
        #     ,'classif_id':self.GetTaxoByName(Taxo)
        #     ,'classif_qual':Qualite
        #     ,'depth_min':Depth
        #     ,'depth_max': Depth
        #     ,'imgcount':0
        #     ,'objdate': DateTime.date()
        #     ,'objtime': DateTime.time()
        #  }
        self.bulk_obj.append(Obj)
        ObjF = {'objfid': objid, self.RevMapObj['area']: Area}
        # Todo calculer l'ESD et le BioVolume et les stocker pour simplifier les contrôles
        self.bulk_objF.append(ObjF)

    def Generate(self, Title, OwnerID=1, SamplePrefix=""):
        Prj = self.InitializeProject(Title, OwnerID)
        logging.info(f"Project {Prj.projid} : {Prj.title} Created")
        # On crée 2 samples ayant pour destin de matcher dans EcoPart
        for samplename in ("sample01", "sampleT1"):
            Sample = self.CreateSample(SamplePrefix + samplename)
            Sampleid = Sample.sampleid  # if faut memoriser les ID sinon ça fait un select à chaque fois qu'on le demande
            T0 = datetime(2019, 11, 21)
            for d in range(100):
                # Le time delta est de 4 heure car ça ne concerne que le sample T1 de uvp6
                self.CreateOject(Sampleid, "Acantharea", Depth=2 + d * 2,
                                 DateTime=T0 + timedelta(hours=4, seconds=d * 20)
                                 , Area=300 - d)
                self.CreateOject(Sampleid, "Halimeda hederacea", Depth=20 + d * 2,
                                 DateTime=T0 + timedelta(hours=4, seconds=d * 20), Area=300 - d, Qualite='N')
            for d in range(500):
                self.CreateOject(Sampleid, "solitaryblack", Depth=2 + d,
                                 DateTime=T0 + timedelta(hours=4, seconds=d * 20), Area=400 - (d // 2))
                self.CreateOject(Sampleid, "solitarygrey", Depth=2 + d,
                                 DateTime=T0 + timedelta(hours=4, seconds=d * 20), Area=300 - (d // 3))
            for d in range(1000):
                self.CreateOject(Sampleid, "fiber<plastic", Depth=2 + d * 0.5,
                                 DateTime=T0 + timedelta(hours=4, seconds=d * 20), Area=200 - (d // 10))
                self.CreateOject(Sampleid, "fiber<detritus", Depth=2 + d,
                                 DateTime=T0 + timedelta(hours=4, seconds=d * 20), Area=150)
            self.SaveBulkObjects()

        nbr = GetAll("""select count(*) nbr 
            from obj_head
            join acquisitions a on obj_head.acquisid = a.acquisid
            join samples s on a.acq_sample_id = s.sampleid 
            where projid=%(projid)s""", {'projid': self.projid})[0]['nbr']
        logging.info(f"Created {nbr} objects")
