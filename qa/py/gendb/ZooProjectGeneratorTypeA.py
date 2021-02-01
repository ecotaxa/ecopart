from  gendb.ZooProjectGenerator import ZooProjectGenerator
from appli import db, database
from datetime import datetime,timedelta
import logging

# not-living>plastic>fiber   fiber<plastic
# not-living>detritus>fiber  fiber<detritus
# living>Eukaryota>Harosa>Rhizaria>Retaria>Polycystinea>Collodaria>solitaryblack
# living>Eukaryota>Harosa>Rhizaria>Retaria>Polycystinea>Collodaria>solitarygrey
# living>Eukaryota>Harosa>Rhizaria>Retaria>Acantharea
# living>Eukaryota>Opisthokonta>Holomycota>Fungi>Ascomycota>Pezizomycotina>Dothideomycetes>Aulographina
# Not validated
# living>Eukaryota>Archaeplastida>Viridiplantae>Chlorophyta>Ulvophyceae>Bryopsidales>Halimeda>Halimeda hederacea

class ZooProjectGeneratorTypeA(ZooProjectGenerator):
    def __init__(self):
        super().__init__()

    def CreateSample(self,SampleName)->database.Samples:
        Sample=database.Samples()
        Sample.projid=self.projid
        Sample.orig_id=SampleName
        db.session.add(Sample)
        db.session.commit()
        return Sample

    def CreateOject(self,Sampleid,Taxo,Depth,DateTime,Area,Qualite='V'):
        objid = self.obj_seq_cache.next()
        Obj=database.Objects()
        Obj.objid=objid
        Obj.projid=self.projid
        Obj.sampleid=Sampleid
        Obj.acquisid=self.Acquisid
        Obj.classif_id=self.GetTaxoByName(Taxo)
        Obj.classif_qual=Qualite
        Obj.depth_min=Depth
        Obj.depth_max = Depth
        Obj.imgcount=0
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
        ObjF={'objfid':objid,self.RevMapObj['area']:Area}
        # Todo calculer l'ESD et le BioVolume et les stocker pour simplifier les contrôles
        self.bulk_objF.append(ObjF)

    def Generate(self,Title,OwnerID=1,SamplePrefix="") :
        Prj=self.InitializeProject(Title,OwnerID)
        logging.info(f"Project {Prj.projid} : {Prj.title} Created")
        for samplename in ("sample01","sampleT1"):
            Sample=self.CreateSample(SamplePrefix+samplename)
            Sampleid=Sample.sampleid # if faut memoriser les ID sinon ça fait un select à chaque fois qu'on le demande
            T0=datetime(2019,11,21)
            for d in range(100):
                # Le time delta est de 4 heure car ça ne concerne que le sample T1 de uvp6
                self.CreateOject(Sampleid,"Acantharea",Depth=2+d*2,DateTime=T0+timedelta(hours=4,seconds=d*20)
                                 ,Area=300-d)
                self.CreateOject(Sampleid, "Halimeda hederacea", Depth=20 + d * 2,
                                 DateTime=T0 + timedelta(hours=4, seconds=d * 20), Area=300 - d,Qualite='N')
            for d in range(500):
                self.CreateOject(Sampleid,"solitaryblack",Depth=2+d,DateTime=T0+timedelta(hours=4,seconds=d*20),Area=400-(d//2))
                self.CreateOject(Sampleid,"solitarygrey" ,Depth=2+d , DateTime=T0 + timedelta(hours=4,seconds=d*20),Area=300 - (d // 3))
            for d in range(1000):
                self.CreateOject(Sampleid,"fiber<plastic",Depth=2+d*0.5,DateTime=T0+timedelta(hours=4,seconds=d*20),Area=200-(d // 10))
                self.CreateOject(Sampleid,"fiber<detritus",Depth=2+d,DateTime=T0+timedelta(hours=4,seconds=d*20),Area=150)
            self.SaveBulkObjects()

        nbr=database.GetAll("select count(*) nbr from obj_head where projid=%(projid)s",{'projid':self.projid})[0]['nbr']
        logging.info(f"Created {nbr} objects")






