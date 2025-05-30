from os.path import dirname, realpath
from pathlib import Path
from part_app.app import part_app, g, db
from part_app.database import part_samples, part_histopart_det, part_projects
import csv
from datetime import timedelta
# noinspection PyProtectedMember
from sqlalchemy.orm.session import make_transient

from part_app.db_utils import GetAll

HERE = Path(dirname(realpath(__file__)))


# noinspection DuplicatedCode
def GenerateUVPRemoteLambdaFolder(SrcProjectTitle, TargetProjectTitle, DirName):
    # Clonage d'un projet existant en bidouillant les data
    with part_app.app_context():  # Création d'un contexte pour utiliser les fonction GetAll,ExecSQL
        g.db = None
        part_project = db.session.query(part_projects).filter_by(ptitle=SrcProjectTitle).first()
        originalpprojid = part_project.pprojid
        db.session.expunge(part_project)  # expunge the object from session
        make_transient(part_project)
        part_project.pprojid = None
        part_project.ptitle = TargetProjectTitle
        part_project.rawfolder = "qa/data/" + DirName
        part_project.instrumtype = "uvp6remote"
        part_project.remote_url = "http://127.0.0.1:5050"
        part_project.remote_directory = "tu1_uvp6remotelambda"
        part_project.remote_type = 'TSV LOV'
        projet_zoo_ref = part_project.projid
        part_project.projid = None  # pas de projet Zoo sur les remote
        db.session.add(part_project)
        db.session.commit()
        FullDirPath = (HERE / '../../..' / part_project.rawfolder).resolve(False)
        if not FullDirPath.exists():
            FullDirPath.mkdir()
        for S in db.session.query(part_samples).filter_by(pprojid=originalpprojid):
            filenamePrefix = f"{S.profileid.replace('uvpapp', 'lambda')}_UVPSN_" + (
                'DEPTH' if S.organizedbydeepth else 'TIME')
            metaFilePath = FullDirPath / (filenamePrefix + '_META.txt')
            lpmFilePath = FullDirPath / (filenamePrefix + '_LPM.txt')
            blackFilePath = FullDirPath / (filenamePrefix + '_BLACK.txt')
            taxo2FilePath = FullDirPath / (filenamePrefix + '_TAXO2.txt')
            with metaFilePath.open("w", newline='') as metaFile, \
                    lpmFilePath.open("w", newline='') as lpmFile, \
                    blackFilePath.open("w", newline='') as blackFile:
                metaFile.write(f"""Camera_ref	000010LP
Acquisition_mode	0
Default_acquisition_configuration	UNDEFINED
Delay_after_power_up_on_time_mode	0
Light_ref	000010VE
Correction_table_activation	1
Time_between_lighting_power_up_and_trigger	150
Time_between_lighting_trigger_and_acquisition	250
Pressure_sensor_ref	192422
Pressure_offset	1.000
Storage_capacity	393819
Minimum_remaining_memory_for_thumbnail_saving	10000
Baud_Rate	2
IP_adress	192.168.0.128
Black_level	0
Shutter	284
Gain	6
Threshold	21
Aa	{S.acq_aa}
Exp	{S.acq_exp}
Pixel_Size	73
Image_volume	{S.acq_volimage}
Calibration_date	20190724
Last_parameters_modification	201910091317
Operator_email	marc.picheral@obs-vlfr.fr
Lower_limit_size_class_1	40.3
Lower_limit_size_class_2	50.8
Lower_limit_size_class_3	64
Lower_limit_size_class_4	80.6
Lower_limit_size_class_5	102
Lower_limit_size_class_6	128
Lower_limit_size_class_7	161
Lower_limit_size_class_8	203
Lower_limit_size_class_9	256
Lower_limit_size_class_10	323
Lower_limit_size_class_11	406
Lower_limit_size_class_12	512
Lower_limit_size_class_13	645
Lower_limit_size_class_14	813
Lower_limit_size_class_15	1020
Lower_limit_size_class_16	1290
Lower_limit_size_class_17	1630
Lower_limit_size_class_18	2050
""")
                # On ajoute les eventuelles classif taxo
                LstClassif = GetAll(f"""select distinct classif_id 
                        from obj_head
                        join acquisitions a on obj_head.acquisid = a.acquisid
                        join samples s on a.acq_sample_id = s.sampleid 
                        where projid={projet_zoo_ref} and classif_qual='V'
                        order by 1""")
                DictLstClassif = {v['classif_id']: i + 1 for i, v in enumerate(LstClassif)}
                for k, v in DictLstClassif.items():
                    metaFile.write(f"category_name_{v}\t{k}\n")
                print("Generate " + metaFilePath.as_posix())
                LPMCols = ['DATE_TIME', 'PRES_decibar', 'LATITUDE_decimal_degree', 'LONGITUDE_decimal_degree',
                           'IMAGE_NUMBER_PARTICLES'
                    , 'TEMP_PARTICLES']
                for i in range(18):
                    LPMCols.append(f"NB_SIZE_SPECTRA_PARTICLES_class_{i + 1}")
                for i in range(18):
                    LPMCols.append(f"GREY_SIZE_SPECTRA_PARTICLES_class_{i + 1}")
                wlpmFile = csv.DictWriter(lpmFile, delimiter='\t', fieldnames=LPMCols)
                wlpmFile.writeheader()
                wblackFile = csv.DictWriter(blackFile, delimiter='\t', fieldnames=LPMCols)
                wblackFile.writeheader()
                print("Get part_histopart_det from sample %d (%s) and generate more" % (S.psampleid, S.profileid))
                for H in db.session.query(part_histopart_det).filter_by(psampleid=S.psampleid):
                    # TODO
                    if H.datetime is None:
                        print("No datetime in %s line %s, skipping" %(S.profileid, H.lineno))
                        continue
                    NbrImage = int(round(H.watervolume / S.acq_volimage))
                    for noimg in range(NbrImage):
                        LineDate = H.datetime + timedelta(seconds=noimg)
                        PartDatas = {'DATE_TIME': LineDate.strftime('%Y%m%dT%H%M%S'), 'PRES_decibar': H.depth
                            , 'LATITUDE_decimal_degree': S.latitude, 'LONGITUDE_decimal_degree': S.longitude
                            , 'IMAGE_NUMBER_PARTICLES': 1, 'TEMP_PARTICLES': 13.5}
                        for classe in range(1, 19):  # 1->18
                            NbrClasse = int(getattr(H, 'class%02d' % (16 + classe)))
                            Nbr = int(NbrClasse / NbrImage)
                            if noimg == 0:  # l'image 0 s'ajuste quand la division entière provoque un reste"
                                Nbr = NbrClasse - (NbrImage - 1) * Nbr
                            PartDatas[f"NB_SIZE_SPECTRA_PARTICLES_class_{classe}"] = Nbr
                            PartDatas[f"GREY_SIZE_SPECTRA_PARTICLES_class_{classe}"] = 55 + noimg
                        wlpmFile.writerow(PartDatas)
                # ON GENERE LE FICHIER ZOO TAXO2.txt
                TAxoCols = ['DATE_TIME', 'PRES_decibar', 'IMAGE_NUMBER_PLANKTON']
                for i in range(40):
                    TAxoCols.append(f"NB_PLANKTON_cat_{i + 1}")
                    TAxoCols.append(f"SIZE_PLANKTON_cat_{i + 1}")
                lst = GetAll("""select classif_id,depth,datetime,watervolume,nbr,avgesd,totalbiovolume 
                                from part_histocat where psampleid=(%s)  order by 1,2,3""", [S.psampleid])
                if len(lst) > 0:
                    with taxo2FilePath.open("w", newline='') as taxo2File:
                        wtaxo2File = csv.DictWriter(taxo2File, delimiter='\t', fieldnames=TAxoCols)
                        wtaxo2File.writeheader()
                        for r in lst:
                            if r['watervolume'] is None:
                                print("No watervolume in %s, skipping" % str(r))
                                continue
                            # TODO
                            # if r['watervolume'] is None:
                            #    continue
                            # ce n'est pas exactement le bon format car il n'y a qu'un categorie par ligne
                            data = {'DATE_TIME': r['datetime'].strftime('%Y%m%dT%H%M%S') if r['datetime'] else None
                                , 'PRES_decibar': r['depth'] or 10  # il faut forcement une profondeur à l'import
                                    }
                            NbrImage = int(round(r['watervolume'] / S.acq_volimage))
                            data['IMAGE_NUMBER_PLANKTON'] = NbrImage
                            NoCat = DictLstClassif[r['classif_id']]
                            data[f"NB_PLANKTON_cat_{NoCat}"] = r['nbr']
                            data[f"SIZE_PLANKTON_cat_{NoCat}"] = r['avgesd']
                            wtaxo2File.writerow(data)


# noinspection DuplicatedCode
def GenerateUVPRemoteLambdaFTPProject(SrcProjectTitle, TargetProjectTitle, DirName):
    with part_app.app_context():  # Création d'un contexte pour utiliser les fonction GetAll,ExecSQL
        g.db = None
        part_project = db.session.query(part_projects).filter_by(ptitle=SrcProjectTitle).first()
        db.session.expunge(part_project)  # expunge the object from session
        make_transient(part_project)
        part_project.pprojid = None
        part_project.ptitle = TargetProjectTitle
        part_project.rawfolder = "qa/data/" + DirName
        part_project.instrumtype = "uvp6remote"
        part_project.remote_url = "127.0.0.1"
        part_project.remote_user = "MyUser"
        part_project.remote_password = "MyPassword"
        part_project.remote_directory = "tu1_uvp6remotelambda"
        part_project.remote_type = 'TSV LOV'
        part_project.projid = None  # pas de projet Zoo sur les remote
        db.session.add(part_project)
        db.session.commit()


if __name__ == "__main__":
    GenerateUVPRemoteLambdaFolder(SrcProjectTitle="EcoPart TU Project UVP 6 from UVP APP"
                                  , TargetProjectTitle="EcoPart TU Project UVP Remote Lambda TEST"
                                  , DirName="tu1_uvp6remotelambda")
    # GenerateUVPRemoteLambdaFTPProject( SrcProjectTitle="EcoPart TU Project UVP Remote Lambda TEST"
    #                                  ,TargetProjectTitle="EcoPart TU Project UVP Remote Lambda FTP"
    #                                  ,DirName="tu1_uvp6remotelambda")
