import logging
import math
import re
import typing
from datetime import datetime, timedelta

from part_app.app import db
from part_app.database import part_projects, part_samples
from part_app.funcs.common_sample_import import ToFloat


class PartProjectGeneratorTypeGeoMosaic:
    def __init__(self):
        self.Prj: typing.Optional[part_projects] = None
        self.pprojid = None
        self.Zooprojid = None

    def Generate(self, Title, OwnerID=1):
        self.Prj = part_projects()
        self.Prj.ptitle = Title
        self.Prj.ownerid = OwnerID
        # self.Zooprojid = db.session.query(database.Projects).filter_by(title="EcoPart TU Zoo Project 1").first().projid
        # self.Prj.projid = self.Zooprojid
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
        Data = (
        (85.0768600, 132.3311500), (85.5176800, 115.4626300), (85.5093500, 115.4714700), (86.0912400, 118.0621400),
        (86.0946500, 118.0876800), (85.4467400, 120.5734100), (85.4422000, 120.2409000), (86.0974500, 116.5151400),
        (86.4072300, 112.5884200),
        (86.4076100, 112.3745500), (86.4056100, 115.5983000), (86.4056100, 115.5983000), (86.4067300, 115.5802800),
        (86.4789400, 116.5683600),
        (86.4867100, 116.4675200), (86.4867100, 116.4675200), (86.5378200, 115.4447500), (86.5981000, 115.2616600),
        (87.0810700, 114.3519900),
        (87.0829900, 114.2858100), (87.1002600, 113.0893200), (87.1019500, 113.0100500), (87.3313100, 102.0458900),
        (87.3340000, 101.5414100),
        (87.32176, 99.42094), (87.2697900, 94.1046900), (87.2697900, 94.1046900), (87.2679500, 94.0531300),
        (87.2679500, 94.0531300),
        (87.2679500, 94.0531300), (87.2872600, 96.1223700), (87.28446, 96.21435), (87.2844600, 96.2143500),
        (87.3573000, 94.0491500),
        (87.3604500, 94.0272200), (87.3828000, 93.4549900), (88.2165600, 69.3554900), (88.2236000, 69.1057100),
        (88.2847200, 67.0214500),
        (88.2894400, 66.5179800), (88.0605900, 29.3804200), (88.04641, 27.17615), (87.33849, 22.04777),
        (87.0889, 17.25743),
        (87.0793, 17.08266), (83.23511, 9.06694), (81.56617, 9.23474), (81.57816, 9.54707), (81.57492, 9.54501),
        (81.55858, 9.49648),
        (81.52885, 9.29697), (81.49729, 9.10883), (81.47946, 8.58826), (81.46283, 8.53503), (81.45874, 8.51781),
        (81.44948, 8.37506),
        (81.40337, 7.38464), (81.40275, 7.35064), (81.40285, 7.32123), (81.40332, 7.29477), (81.40647, 7.22098),
        (81.40714, 7.20301),
        (81.40744, 7.18617), (81.40779, 7.16581), (81.40959, 7.09364), (81.41077, 7.06977), (81.41191, 7.05388),
        (81.41834, 7.00545),
        (81.42082, 6.59668), (81.42307, 6.59146), (81.42448, 6.5343), (81.42376, 6.51427), (81.42512, 6.42217),
        (81.42628, 6.41192),
        (81.3736, 3.31024), (81.336, 2.36322), (81.33448, 2.36344), (81.30138, 2.20911), (81.2887, 2.07203),
        (81.27717, 1.46134),
        (81.14553, 0.18664), (81.14075, 0.18337), (80.55062, -0.0112), (80.38564, -0.31676), (80.36977, -0.32749),
        (80.28342, -0.34171),
        (80.23347, -0.33235), (80.22467, -0.3317), (80.15188, -0.38605), (79.59998, -0.38352), (79.49821, -1.40044),
        (79.12351, -2.39642),
        (79.06979, -2.32401), (78.35226, -1.36709), (79.5364, -3.46268), (88.17947, -34.38997), (88.56257, -35.41319))
        for i, d in enumerate(Data):
            self.GenerateSample(f"sample{i}", i, ConvTextDegreeToDecimalDegree(str(d[0])),
                                ConvTextDegreeToDecimalDegree(str(d[1])))

    def GenerateSample(self, SampleName, Hour, latitude, longitude) -> part_samples:
        Sample = part_samples()
        Sample.pprojid = self.Prj.pprojid
        Sample.profileid = SampleName
        Sample.firstimage = 1
        Sample.lastimg = 999999
        Sample.filename = "File" + SampleName
        Sample.latitude = latitude
        Sample.longitude = longitude
        Sample.sampledate = datetime(2019, 11, 21) + (
            timedelta(hours=Hour))  # utilisé pour faire un nom de fichier unique
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


def ConvTextDegreeToDecimalDegree(v, FloatAsDecimalDegree=True):
    """
    Converti une lattitude ou longitude texte en version floattante degrés decimaux.
    Format possibles :
    DD°MM SS
    DD.MMMMM : MMMMM = Minutes /100 donc compris entre 0.0 et 0.6 format historique UVP
    DD.FFFFF : FFFFF = Fractions de dégrés
    :param v: Input text
    :param FloatAsDecimalDegree: Si False notation historique, si True degrés décimaux
    :return:
    """
    m = re.search("(-?\d+)°(\d+) (\d+)", v)
    if m:  # donnée au format DDD°MM SSS
        parties = [float(x) for x in m.group(1, 2, 3)]
        parties[1] += parties[2] / 60  # on ajoute les secondes en fraction des minutes
        parties[0] += math.copysign(parties[1] / 60, parties[
            0])  # on ajoute les minutes en fraction des degrés avec le même signe que la partie dégrés
        return round(parties[0], 5)
    else:
        v = ToFloat(v)
        if FloatAsDecimalDegree:  # format degrée decimal, il faut juste convertir le texte en float.
            return v
        else:  # format historique la partie decimale etait exprimée en minutes
            f, i = math.modf(v)
            return round(i + (f / 0.6), 5)


if __name__ == "__main__":
    PartPrj = PartProjectGeneratorTypeGeoMosaic()
    PartPrj.Generate("Test Mosaic")
