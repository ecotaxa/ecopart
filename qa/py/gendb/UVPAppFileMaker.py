from os.path import dirname, realpath,join
from pathlib import Path
from appli import database,app,g,db
from appli.part import PartDetClassLimit
from appli.tasks.importcommon import calcpixelfromesd_aa_exp
from appli.part.uvp_sample_import import GetPathForRawHistoFile
from appli.part.database import part_samples,part_histopart_det,part_projects
import bz2, sys,logging,re,csv,configparser,zipfile
from datetime import timedelta
from sqlalchemy.orm.session import make_transient

HERE = Path(dirname(realpath(__file__)))



def GenerateUVPAppFolder(SrcProjectTitle,TargetProjectTitle, DirName):
    with app.app_context():  # Création d'un contexte pour utiliser les fonction GetAll,ExecSQL
        g.db = None
        part_project=part_projects.query.filter_by(ptitle=SrcProjectTitle).first()
        originalpprojid=part_project.pprojid
        db.session.expunge(part_project)  # expunge the object from session
        make_transient(part_project)
        part_project.pprojid=None
        part_project.ptitle=TargetProjectTitle
        part_project.rawfolder="qa/data/"+DirName
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
        EcodataDirPath = FullDirPath / "ecodata"
        if not EcodataDirPath.exists():
            EcodataDirPath.mkdir()
        with HeaderFilePath.open("w", newline='') as HeaderFile:
            fieldnames="cruise;ship;filename;profileid;bottomdepth;ctdrosettefilename;latitude;longitude;firstimage;volimage;aa;exp;dn;winddir;windspeed;seastate;nebuloussness;comment;endimg;yoyo;stationid;pixelsize".split(';')
            w = csv.DictWriter(HeaderFile, delimiter=';', fieldnames=fieldnames )
            w.writeheader()
            for S in part_samples.query.filter_by(pprojid=originalpprojid):
                filename= S.sampledate.strftime('%Y%m%d%H%M%S')
                HeaderRow={'cruise': "TestCruise","ship":"Testship",'profileid': S.profileid,
                            'filename': filename,
                            'latitude': S.latitude,'longitude': S.longitude,'firstimage':S.firstimage,'endimg':S.lastimg,
                            'aa': S.acq_aa,'exp': S.acq_exp,'volimage': S.acq_volimage,'pixelsize':0.088
                            }
                w.writerow(HeaderRow)
                SampleFolderPath= EcodataDirPath / ("%s"%S.profileid)
                if not SampleFolderPath.exists():
                    SampleFolderPath.mkdir()
                MetadataFilePath = SampleFolderPath / ("metadata.ini")
                write_config = configparser.ConfigParser()
                write_config.add_section("HW_CONF")
                write_config.set("HW_CONF", "Aa", str(S.acq_aa))
                write_config.set("HW_CONF", "Exp", str(S.acq_exp))
                write_config.set("HW_CONF", "Gain", "6")
                write_config.set("HW_CONF", "Shutter", "2")
                write_config.set("HW_CONF", "Threshold", "0")
                write_config.set("HW_CONF", "Pressure offset", "999.000")
                for (k,v) in {'Acquisition_mode':'1','Baud_Rate':'2','Black_level':'1','Calibration_date':'20190207',
'Camera_ref':'002','Correction_table_activation':'1','Default_acquisition_configuration':'ACQ_ROV','Delay_after_power_up_on_time_mode':'0','IP_adress':'192.168.0.128','Image_volume':'0.630','Last_parameters_modification':'201904050247',
'Light_ref':'002','Minimum_remaining_memory_for_thumbnail_saving':'2000','Operator_email':'l.picheral','Pixel_Size':'73',
'Pressure_sensor_ref':'169559','Storage_capacity':'393819','Time_between_lighting_power_up_and_trigger':'150',
'Time_between_lighting_trigger_and_acquisition':'250'}.items() :
                    write_config.set("HW_CONF", k, v)

                write_config.add_section("ACQ_CONF")
                write_config.set("ACQ_CONF", "Vignetting_lower_limit_size", "700")
                write_config.set("ACQ_CONF", "Limit_lpm_detection_size", "70")
                for (k, v) in {"Acquisition_frequency":"2.000","Analog_output_activation":"0","Appendices_ratio":"2.0",
"Blocs_per_PT":"1","Configuration_name":"ACQ_ROV","Embedded_recognition":"0","Frames_per_bloc":"1","Gain_for_analog_out":"1000",
"Image_nb_for_smoothing":"10","Interval_for_mesuring_background_noise":"50",
"Maximal_internal_temperature":"40","Minimum_object_number":"0","Operator_email":"l.picheral","PT_mode":"2",
"Pressure_difference_for_auto_stop":"0","Pressure_for_auto_start":"0","Result_sending":"1","Save_images":"2",
"Save_synthetic_data_for_delayed_request":"1"}.items() :
                    write_config.set("ACQ_CONF", k, v)

                write_config.add_section("sample_metadata")
                for title in ('cruise','ship','filename','profileid','bottomdepth','ctdrosettefilename','latitude','longitude','firstimage','dn','winddir','windspeed','seastate','nebuloussness','comment','endimg','yoyo','stationid','sampletype','integrationtime','argoid'):
                    write_config.set("sample_metadata", title, str(HeaderRow.get(title,"")))
                write_config.set("sample_metadata", "sampledatetime", filename[:8]+"-"+filename[8:])
                with MetadataFilePath.open('w') as hdr:
                    print('Generate %s'%MetadataFilePath)
                    write_config.write(hdr)
                PartFilePath=SampleFolderPath / ("particules.csv")
                with PartFilePath.open('w',newline='') as PartFile:
                    PartFile.write("""HW_CONF,002,1,ACQ_ROV,0,002,1,150,250,169559,999.000,393819,2000,2,192.168.0.128,1,400,14,1,339,1.4389,73,0.630,20190207,201904050247,l.picheral,64,80.6,102,128,161,203,256,323,406,512,645,813,1020,1290,1630,2050,2580,3250,4100;

ACQ_CONF,ACQ_ROV,2,2.000,1,1,0,0,1,1,70,2,700,2.0,50,10,0,1000,0,40,l.picheral,0,393714;
""")

                    for H in part_histopart_det.query.filter_by(psampleid=S.psampleid):
                        NbrImage =int(round (H.watervolume/S.acq_volimage))
                        # format des lignes de données YYYYMMDD-HHIISS,depth,Temperature,Flash (0 ou 1): Données particules
                        # Données particules sont des quartets de valeurs séparées par des virgules
                        # TailleEnPixel,Nbr,MoyenneGris,EcartTypeGris
                        # Les quartets sont séparés entre eux par des ;
                        for noimg in range(NbrImage):
                            PartDatas=[]
                            for classe in range(1, 45):
                                NbrClasse = getattr(H, 'class%02d' % classe)
                                if NbrClasse is None:
                                    continue
                                Nbr = int(NbrClasse/NbrImage)
                                if noimg==0: #l'image 0 s'ajuste quand la division entière provoque un reste"
                                    Nbr=NbrClasse-(NbrImage-1)*Nbr
                                ESDMm = (PartDetClassLimit[classe - 1] + PartDetClassLimit[classe]) / 2
                                Area = int(calcpixelfromesd_aa_exp(ESDMm, S.acq_aa, S.acq_exp))
                                PartDatas.append(f"{Area},{Nbr},30,3")
                            LineDate=H.datetime+timedelta(seconds=noimg)
                            PartFile.write("%s,%s,18.5,1:%s\r\n"%(
                                LineDate.strftime('%Y%m%d-%H%M%S'),H.depth,";".join(PartDatas)
                            ))
                # Les fichiers sont générés, on les mets dans le .zip
                PartZipFilePath = SampleFolderPath / (f"{S.profileid}_Particule.zip")
                with zipfile.ZipFile(PartZipFilePath, "w", allowZip64=True, compression=zipfile.ZIP_DEFLATED) as zf:
                    zf.write(MetadataFilePath,"metadata.ini")
                    zf.write(PartFilePath,"particules.csv")




if __name__ == "__main__":
    GenerateUVPAppFolder(SrcProjectTitle="EcoPart TU Project UVP 2 Precomputed"
                                     ,TargetProjectTitle="EcoPart TU Project UVP 6 from UVP APP"
                                     ,DirName="tu1_uvp6uvpapp")