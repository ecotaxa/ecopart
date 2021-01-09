from os.path import dirname, realpath,join
from pathlib import Path
from appli import database,app,g,db
from appli.part import PartDetClassLimit
from appli.part.lisst_sample_import import BuildLISSTClass
from appli.tasks.importcommon import calcpixelfromesd_aa_exp
from appli.part.database import part_samples,part_histopart_det,part_projects
import bz2, sys,logging,re,csv,configparser,zipfile
from datetime import timedelta
from sqlalchemy.orm.session import make_transient

HERE = Path(dirname(realpath(__file__)))



def GenerateLISSTFolder(SrcProjectTitle,TargetProjectTitle, DirName):
    with app.app_context():  # Création d'un contexte pour utiliser les fonction GetAll,ExecSQL
        g.db = None
        part_project=part_projects.query.filter_by(ptitle=SrcProjectTitle).first()
        originalpprojid=part_project.pprojid
        db.session.expunge(part_project)  # expunge the object from session
        make_transient(part_project)
        part_project.pprojid=None
        part_project.ptitle=TargetProjectTitle
        part_project.rawfolder="qa/data/"+DirName
        part_project.instrumtype="lisst"
        part_project.projid=None # pas de projet zoo possible sur un projet LISST
        db.session.add(part_project)
        db.session.commit()
        m = re.search(R"([^_]+)_(.*)", DirName)
        FullDirPath=(HERE / '../../..' / part_project.rawfolder).resolve(False)
        if not FullDirPath.exists():
            FullDirPath.mkdir()
        MetaDirPath = FullDirPath / "meta"
        if not MetaDirPath.exists():
            MetaDirPath.mkdir()
        HeaderFilePath= MetaDirPath / (m.group(1) + "_header_" + m.group(2) + ".txt")
        WorkDirPath = FullDirPath / "work"
        if not WorkDirPath.exists():
            WorkDirPath.mkdir()
        with HeaderFilePath.open("w", newline='') as HeaderFile:
            fieldnames="cruise;ship;filename;profileid;bottomdepth;ctdrosettefilename;latitude;longitude;firstimage;volimage;aa;exp;dn;winddir;windspeed;seastate;nebuloussness;comment;endimg;yoyo;stationid;pixelsize;sampletype;integrationtime;kernel;zscat_filename;year".split(';')
            w = csv.DictWriter(HeaderFile, delimiter=';', fieldnames=fieldnames )
            w.writeheader()
            for S in part_samples.query.filter_by(pprojid=originalpprojid):
                filename= S.sampledate.strftime('%Y%m%d%H%M%S')
                HeaderRow={'cruise': "TestCruise","ship":"Testship",'profileid': S.profileid,
                            'filename': filename,'kernel':'spherical','zscat_filename':'Myzscat_filename','year':2020,
                            'latitude': S.latitude,'longitude': S.longitude,#'firstimage':S.firstimage,'endimg':S.lastimg,
                            # 'aa': S.acq_aa,'exp': S.acq_exp,'volimage': S.acq_volimage,'pixelsize':0.088,
                            'sampletype':'P' if S.organizedbydeepth else 'T', 'integrationtime':S.integrationtime
                            }
                w.writerow(HeaderRow)
                PartFilePath= WorkDirPath / (f"{S.filename}.asc")
                ClassesLisst=BuildLISSTClass('spherical')
                ClassLisstMap= {}
                with PartFilePath.open('w',newline='') as PartFile:
                    print(f'Generate {PartFilePath}' )
                    # aucun entête, 42 colonnes en TSV
                    # colonne [0 à 31] 32 classe
                    # colonne [36] = profondeur
                    for H in part_histopart_det.query.filter_by(psampleid=S.psampleid):
                        PartDatas=([0]*32)+([9999]*10)
                        PartDatas[36]=H.depth
                        for classe in range(1, 46): # 1->45
                            NbrClasse = getattr(H, 'biovol%02d' % classe)
                            if NbrClasse is None or NbrClasse ==0:
                                continue
                            ESDMm = (PartDetClassLimit[classe - 1] + PartDetClassLimit[classe]) / 2
                            if classe not in ClassLisstMap:
                                for i,C in enumerate(ClassesLisst):
                                    if ESDMm>=C[0] and  ESDMm<=C[1]:
                                        ClassLisstMap[classe]=i
                                        break
                            PartDatas[ClassLisstMap[classe]]+=NbrClasse
                        PartFile.write((" ".join(str(x) for x in PartDatas))+"\n")





if __name__ == "__main__":
    GenerateLISSTFolder(SrcProjectTitle="EcoPart TU Project UVP 6 from UVP APP" # pas le ref car on a besoin des Bv
                                     ,TargetProjectTitle="EcoPart TU Project LISST"
                                     ,DirName="tu1_lisst")