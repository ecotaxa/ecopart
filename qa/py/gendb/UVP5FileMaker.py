from os.path import dirname, realpath,join
from pathlib import Path
from appli import database,app,g,db
from appli.part import PartDetClassLimit
from appli.tasks.importcommon import calcpixelfromesd_aa_exp
from appli.part.uvp_sample_import import GetPathForRawHistoFile
from appli.part.database import part_samples,part_histopart_det,part_projects
import bz2, sys,logging,re,csv,configparser
from sqlalchemy.orm.session import make_transient

HERE = Path(dirname(realpath(__file__)))


def GenerateRawFileForSample(UvpSample):
    DetHistoFile =GetPathForRawHistoFile(UvpSample.psampleid)
    with bz2.open(DetHistoFile, 'wt', newline='') as f:
        cf=csv.writer(f,delimiter='\t')
        cf.writerow(["depth","imgcount","area","nbr","greylimit1","greylimit2","greylimit3"])
        for Partition,PartitionContent in SegmentedData.items():
            for area,greydata in PartitionContent['area'].items():
                # if area in ('depth', 'time'): continue  # ces clés sont au même niveau que les area
                agreydata=np.asarray(greydata)
                # ça ne gère pas l'organisation temporelle des données
                cf.writerow([PartitionContent['depth'],PartitionContent['imgcount'],area,len(agreydata)
                                ,np.percentile(agreydata,25,interpolation='lower')
                                , np.percentile(agreydata, 50, interpolation='lower')
                                , np.percentile(agreydata, 75, interpolation='higher')]
                            )
    UvpSample.histobrutavailable=True
    db.session.commit()

def GenerateUVP5Folder(SrcProjectTitle,TargetProjectTitle, DirName):
    with app.app_context():  # Création d'un contexte pour utiliser les fonction GetAll,ExecSQL
        g.db = None
        part_project=part_projects.query.filter_by(ptitle=SrcProjectTitle).first()
        originalpprojid=part_project.pprojid
        db.session.expunge(part_project)  # expunge the object from session
        make_transient(part_project)
        part_project.pprojid=None
        part_project.ptitle=TargetProjectTitle
        part_project.rawfolder="qa/py/data/"+DirName
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
        RawDirPath = FullDirPath / "raw"
        if not RawDirPath.exists():
            RawDirPath.mkdir()
        with HeaderFilePath.open("w", newline='') as HeaderFile:
            fieldnames="cruise;ship;filename;profileid;bottomdepth;ctdrosettefilename;latitude;longitude;firstimage;volimage;aa;exp;dn;winddir;windspeed;seastate;nebuloussness;comment;endimg;yoyo;stationid;pixelsize".split(';')
            w = csv.DictWriter(HeaderFile, delimiter=';', fieldnames=fieldnames )
            w.writeheader()
            for S in part_samples.query.filter_by(pprojid=originalpprojid):
                filename= S.sampledate.strftime('%Y%m%d%H%M%S')
                w.writerow({'cruise': "TestCruise","ship":"Testship",'profileid': S.profileid,
                            'filename': filename,
                            'latitude': S.latitude,'longitude': S.longitude,'firstimage':S.firstimage,'endimg':S.lastimg,
                            'aa': S.acq_aa,'exp': S.acq_exp,'volimage': S.acq_volimage,'pixelsize':0.088
                            })
                HDRFolderPath= RawDirPath / ("HDR%s"%filename)
                if not HDRFolderPath.exists():
                    HDRFolderPath.mkdir()
                HDRFilePath = HDRFolderPath / ("HDR%s"%filename+".hdr")
                write_config = configparser.ConfigParser()
                write_config.add_section("General")
                write_config.set("General", "ShutterSpeed", "12")
                write_config.set("General", "Gain", "6")
                write_config.set("General", "TaskType", "2")
                write_config.set("General", "DiskType", "0")
                write_config.add_section("Processing")
                write_config.set("Processing", "SMzoo", "26")
                write_config.set("Processing", "SMbase", "0")
                write_config.set("Processing", "EraseBorderBlobs", "0")
                write_config.set("Processing", "Thresh", "21")
                write_config.add_section("Picture")
                write_config.set("Picture", "Choice", "1")
                write_config.set("Picture", "Ratio", "3")
                with HDRFilePath.open('w') as hdr:
                    print('Generate %s'%HDRFilePath)
                    write_config.write(hdr)
                DatFilePath=HDRFolderPath / ("HDR%s"%filename+".dat")
                BruFilePath = HDRFolderPath / ("HDR%s" % filename + ".bru")
                with DatFilePath.open('w',newline='') as DatFile,BruFilePath.open('w',newline='') as BruFile:
                    fieldnames="index;image;sensor data;nb blobs P-G;mean area P-G;mean grey P-G;nb blobs G;mean grey G".split(";")
                    wDat = csv.DictWriter(DatFile, delimiter=';', fieldnames=fieldnames )
                    wDat.writeheader()
                    BruFile.write("index;	image;	blob;	area;	meangrey;	xcenter;	ycenter;\r\n")
                    for H in part_histopart_det.query.filter_by(psampleid=S.psampleid):
                        NbrImage =int(round (H.watervolume/S.acq_volimage))
                        for noimg in range(NbrImage):
                            wDat.writerow({'index':H.lineno*NbrImage+noimg+1, #+1 car il ne faut pas l'index à 0
                                        "image":"Image%s"%(H.lineno*NbrImage+noimg),
                                       'sensor data':'%s*xx*yy'%(int(H.depth*10),),
                                       'nb blobs P-G':5,'mean area P-G':6,'mean grey P-G':7,
                                       'nb blobs G': 8, 'mean grey G': 9
                                       })
                        for classe in range(1,45):
                            Nbr=getattr(H,'class%02d'%classe)
                            if Nbr is None:
                                continue
                            Nbr=int(Nbr)
                            ESDMm=(PartDetClassLimit[classe-1]+PartDetClassLimit[classe])/2
                            Area=int(calcpixelfromesd_aa_exp(ESDMm,S.acq_aa,S.acq_exp))
                            for i in range(Nbr):
                                MeanGrey = 30 + (i%50)
                                BruFile.write(" %s;\tImgClass%s;%s;\t%s;\t%s;500;500\r\n"%(H.lineno*NbrImage+(i%NbrImage)+1,classe,i+1,Area,MeanGrey))


if __name__ == "__main__":
    GenerateUVP5Folder(SrcProjectTitle="EcoPart TU Project UVP 2 Precomputed"
                                     ,TargetProjectTitle="EcoPart TU Project UVP 5 pour load HDR"
                                     ,DirName="tu1_uvp5hdr")