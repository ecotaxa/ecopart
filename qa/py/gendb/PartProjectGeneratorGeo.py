from appli import db
from appli.part import database
import typing, appli, math, logging
from datetime import datetime, timedelta


class PartProjectGeneratorTypeGeo:
    def __init__(self):
        self.Prj: typing.Optional[database.part_projects()] = None
        self.pprojid = None
        self.Zooprojid=None

    def Generate(self, Title, OwnerID=1):
        self.Prj = database.part_projects()
        self.Prj.ptitle = Title
        self.Prj.ownerid = OwnerID
        self.Zooprojid = db.session.query(appli.database.Projects).filter_by(title="EcoPart TU Zoo Project 1").first().projid
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
        for i in range(1,89):
            self.GenerateSample(f"sampleNE{i}",i, i*1.01,-46.1+1.01*i)
            self.GenerateSample(f"sampleSE{i}",i,-i*1.01,-46.1+1.01*i)
            self.GenerateSample(f"sampleNW{i}",i, i*1.01,-86.1-1.01*i)
            self.GenerateSample(f"sampleSW{i}", i, -i * 1.01, -86.1 - 1.01 * i)
            self.GenerateSample(f"sampleSW{i}", i, 30+i * 0.1,  4.01 * i)

    def GenerateSample(self, SampleName,Hour,latitude,longitude) -> database.part_samples:
        Sample = database.part_samples()
        Sample.pprojid = self.Prj.pprojid
        Sample.profileid = SampleName
        Sample.firstimage=1
        Sample.lastimg=999999
        Sample.filename = "File" + SampleName
        Sample.latitude = latitude
        Sample.longitude = longitude
        Sample.sampledate = datetime(2019, 11, 21)+(timedelta(hours=Hour)) # utilisé pour faire un nom de fichier unique
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
    PartPrj = PartProjectGeneratorTypeGeo()
    PartPrj.Generate("Test")
