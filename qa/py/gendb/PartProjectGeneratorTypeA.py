from gendb.ZooProjectGenerator import ZooProjectGenerator
from appli import db
from appli.part import database
import typing, appli, math, logging
from datetime import datetime, timedelta


class PartProjectGeneratorTypeA:
    def __init__(self):
        self.Prj: typing.Optional[database.part_projects()] = None
        self.pprojid = None
        self.Zooprojid=None

    def Generate(self, Title, OwnerID=1):
        self.Prj = database.part_projects()
        self.Prj.ptitle = Title
        self.Prj.ownerid = OwnerID
        self.Zooprojid = appli.database.Projects.query.filter_by(title="EcoPart TU Zoo Project 1").first().projid
        self.Prj.projid = self.Zooprojid
        self.Prj.instrumtype = 'uvp5'
        self.Prj.op_name = 'My OP Name'
        self.Prj.op_email = 'opname@test.com'
        self.Prj.cs_name = 'My CS Name'
        self.Prj.cs_email = 'csname@test.com'
        self.Prj.do_name = 'My DO Name'
        self.Prj.do_email = 'doname@test.com'
        self.Prj.rawfolder = 'xxx'
        db.session.add(self.Prj)
        db.session.commit()
        self.pprojid = self.Prj.pprojid
        logging.info(f"Project {self.pprojid} created : {Title}")
        Sample = self.GenerateSample("sample01",1)
        self.GenerateParticules(Sample)
        Sample = self.GenerateSample("sample02",2)
        self.GenerateParticules(Sample, Coeff=1.2,NbrImages=2)
        Sample = self.GenerateSample("sample03",3)
        self.GenerateParticules(Sample, Coeff=0.8,NbrImages=3)
        logging.info(f"Filled 3 Samples")

    def GenerateParticules(self, Sample, Coeff=1,NbrImages=1):
        def Clean(x):
            if x <= 0:  # supprimer les negatif
                return 0
            return int(x * Coeff*NbrImages)  # applique le Coeff et arrondi à l'entier

        Histo = []
        for d in range(300):
            h = database.part_histopart_det()
            h.psampleid = Sample.psampleid
            h.datetime=Sample.sampledate+timedelta(seconds=63*d)
            h.lineno = d
            h.depth = d * 5 + 2.5  # c'est des tranche de 5 m
            h.watervolume = Sample.acq_volimage*NbrImages
            for i in range(1,46):
                setattr(h,f"class{i:02d}",0)
            # Classe reduite 6 = Det 16->18
            h.class17 = Clean(400 - d)
            h.class18 = Clean(200 - d)
            # Classe reduite 7 = Det 19->21
            h.class19 = Clean(10)
            if d < 20:
                h.class20 = Clean(20 - d)
            elif d == 40:
                h.class20 = Clean(15)
            else:
                h.class20 = 0
            # Classe reduite 8 = Det 22->24
            h.class22 = Clean(100 / (0.1 * (d + 30)))
            h.class23 = Clean(10 * math.log1p(301 - d))
            Histo.append(h)
        db.session.bulk_save_objects(Histo)  # permet de passer de 440ms à 230ms
        db.session.commit()

    def GenerateSample(self, SampleName,Hour) -> database.part_samples:
        Sample = database.part_samples()
        Sample.pprojid = self.Prj.pprojid
        Sample.profileid = SampleName
        Sample.firstimage=1
        Sample.lastimg=999999
        Sample.filename = "File" + SampleName
        Sample.latitude = 43.6543
        Sample.longitude = 7.3456
        Sample.sampledate = datetime(2019, 11, 21,Hour) # utilisé pour faire un nom de fichier unique
        Sample.instrumsn = "sn123456"
        Sample.organizedbydeepth = True
        # Même valeurs que dans le projet ecotaxa
        # Sample.acq_aa = 0.0043
        # Sample.acq_exp = 1.12
        # Autres valeurs pas forcement réalistes mais permet de générer des bru qui remplisses les classes 17 et +
#        Sample.acq_aa = 0.0006
        Sample.acq_aa = 0.0002
        Sample.acq_exp = 1.02
        Sample.acq_volimage = 1.13
        Sample.acq_depthoffset = 1.2
        Sample.acq_pixel = 0.088
        db.session.add(Sample)
        db.session.commit()
        return Sample


if __name__ == "__main__":
    PartPrj = PartProjectGeneratorTypeA()
    PartPrj.Generate("Test")
