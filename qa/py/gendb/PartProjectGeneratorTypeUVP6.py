#from gendb.ZooProjectGenerator import ZooProjectGenerator
from appli import db
from appli.part import database
import typing, appli, math, logging
from datetime import datetime, timedelta
from PartProjectGeneratorTypeA import PartProjectGeneratorTypeA

# Similaire au type A mais avec des sample de type Time en plus

class PartProjectGeneratorTypeUVP6(PartProjectGeneratorTypeA):
    def __init__(self):
        PartProjectGeneratorTypeA.__init__(self)

    def Generate(self, Title, OwnerID=1):
        PartProjectGeneratorTypeA.Generate(self, Title, OwnerID)
        Sample = self.GenerateSample("sampleT1",4)
        Sample.organizedbydeepth = False
        Sample.integrationtime=300 # temps d'intégration de 5 minutes soit 4 points puisquils séparés de 63sec chacuns
        # utilisé seulement pour l'aggregation dans les raw, les histograme sont toujours sur 1h
        # il faut cependant noter que du coup les histograme générés dans ce projet ne sont pas conforme
        # a ce qui pourrait sera réimporté car ici c'est une ligne toutes les 63sec alors qu'une fois reimporté
        # ça sera seulement 6 lignes (1/heure)
        db.session.commit()
        self.GenerateParticules(Sample)
        Sample = self.GenerateSample("sampleT2",5)
        Sample.organizedbydeepth = False
        Sample.integrationtime=300
        db.session.commit()
        self.GenerateParticules(Sample, Coeff=1.2,NbrImages=2)
        Sample = self.GenerateSample("sampleT3",6)
        Sample.organizedbydeepth = False
        Sample.integrationtime=300
        db.session.commit()
        self.GenerateParticules(Sample, Coeff=0.8,NbrImages=3)
        logging.info(f"Filled 3 Time Samples")



if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(filename)s: %(message)s', level=logging.DEBUG)
    PartPrj = PartProjectGeneratorTypeUVP6()
    PartPrj.Generate("Test")
