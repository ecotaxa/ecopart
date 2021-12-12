import logging
from os.path import dirname, realpath, join
from pathlib import Path

from sqlalchemy import text

# On importe le manage.py pour créer la DB. _Les DBs_ en fait car les définitions de EcoTaxa sont incluses
import manage
from Zoo_DB import database
# Replace EcoTaxaInstance
from Zoo_backend import kill_backend, BACKEND_PORT, launch_backend, generate_backend_conf
from gendb.LISSTFileMaker import GenerateLISSTFolder
from gendb.PartProjectGeneratorGeo import PartProjectGeneratorTypeGeo
from gendb.PartProjectGeneratorGeoMosaic import PartProjectGeneratorTypeGeoMosaic
from gendb.PartProjectGeneratorTypeA import PartProjectGeneratorTypeA
from gendb.PartProjectGeneratorTypeUVP6 import PartProjectGeneratorTypeUVP6
from gendb.UVP5FileMaker import GenerateUVP5Folder
from gendb.UVPAppFileMaker import GenerateUVPAppFolder
from gendb.UVPRemoteLambdaFileMaker import GenerateUVPRemoteLambdaFolder, GenerateUVPRemoteLambdaFTPProject
from gendb.ZooProjectGeneratorTypeA import ZooProjectGeneratorTypeA
# Si ces imports sont rouges dans pyCharm, mettre le répertoire contenant part_app et manage.py dans l'interpréteur
# du projet via settings/project structure/Add Content root
from part_app import app, urls
from part_app.app import part_app, db, g
from part_app.database import part_samples, part_projects
from part_app.db_utils import ExecSQL
from part_app.funcs.histograms import ComputeHistoRed, ComputeZooHisto
from part_app.remote import EcoTaxaInstance
from part_app.views.prj import ComputeZooMatch
from tests.utils import TaskInstance, zoo_login

HERE = Path(dirname(realpath(__file__)))

# Les tests supposent que les data à importer sont là, dans le répertoire "qa/data" qui est indiqué dans les projets
app.ServerLoadArea = (HERE / '../../..').resolve()
app.VaultRootDir = (HERE / '../../vault').resolve()


def main():
    logging.basicConfig(format='%(asctime)s %(filename)s: %(message)s', level=logging.DEBUG)

    db_database = part_app.config['DB_DATABASE']
    if not str(db.engine.url).endswith(db_database):
        print("SQLAlchemy has a different DB!")
        exit(-1)
    if '_tu' not in db_database:
        print("Generation of database can occur only on _tu database !!!!\nGeneration ABORTED")
        exit(-1)
    logging.info("Initialize Database")

    # Recrée la structure des bases de données (Zoo + Part)
    manage.CreateDB(SkipConfirmation=True, UseExistingDatabase=True)

    # La config EcoTaxa est +/- similaire à celle de EcoPart
    generate_backend_conf(part_app.config)
    # Il faut la config avant de lancer car le thread qui exécute les jobs se lance immédiatement
    launch_backend()

    with part_app.app_context():  # Création d'un contexte pour utiliser les fonction GetAll,ExecSQL
        g.db = None

        # On crée le user 1 qui est référencé, mais n'est pas dans EcoPart
        zoo_user = database.users(email="admin", name=database.AdministratorLabel, password="nimda", active=True)
        db.session.add(zoo_user)
        adm_role = database.roles(id=1, name=database.AdministratorLabel)
        db.session.add(adm_role)
        zoo_user.roles.append(adm_role)
        db.session.commit()
        #
        urls.BACKEND_API_PORT[0] = BACKEND_PORT
        token = zoo_login("admin", "nimda")
        assert token is not None
        ecotaxa_if = EcoTaxaInstance(token)

        logging.info("Import Taxonomy File")
        SourceTaxoFile = realpath(join(HERE, "..", "..", "data", "taxonomy.tsv"))
        sql = "copy taxonomy(id, parent_id, name, id_source, display_name, lastupdate_datetime, id_instance, rename_to, source_url, source_desc, creator_email, creation_datetime, nbrobj, nbrobjcum) from '" + SourceTaxoFile + "'"
        ExecSQL(sql)
        logging.info("Taxonomy imported")
        # db.session.execute("SET synchronous_commit TO OFF;") # aucun gain
        # création des projet Zoo, comme c'est un peu long et que ça ne change pas trés souvent, on les sauve
        FichierZooPrj = Path(realpath(join(HERE, "..", "..", "data", "ZooPrj.tsv")))
        FichierZooSample = Path(realpath(join(HERE, "..", "..", "data", "ZooSample.tsv")))
        FichierZooAcq = Path(realpath(join(HERE, "..", "..", "data", "ZooAcq.tsv")))
        FichierZooObjHead = Path(realpath(join(HERE, "..", "..", "data", "ZooObjHead.tsv")))
        FichierZooObjField = Path(realpath(join(HERE, "..", "..", "data", "ZooObjField.tsv")))
        if not FichierZooPrj.exists() or not FichierZooSample.exists() or not FichierZooAcq.exists() \
                or not FichierZooObjHead.exists() or not FichierZooObjField.exists():
            Prj = ZooProjectGeneratorTypeA()
            Prj.Generate("EcoPart TU Zoo Project 1")
            Prj.Generate("EcoPart TU Zoo Project for UVPAPP", SamplePrefix="uvpapp")
            Prj.Generate("EcoPart TU Zoo Project for BRU", SamplePrefix="bru")
            Prj.Generate("EcoPart TU Zoo Project for BRU1", SamplePrefix="bru1")
            # Pb de droits sous Linux
        #     ExecSQL("copy projects to '" + FichierZooPrj.as_posix() + "'")
        #     ExecSQL("copy samples to '" + FichierZooSample.as_posix() + "'")
        #     ExecSQL("copy acquisitions to '" + FichierZooAcq.as_posix() + "'")
        #     ExecSQL("copy obj_head to '" + FichierZooObjHead.as_posix() + "'")
        #     ExecSQL("copy obj_field to '" + FichierZooObjField.as_posix() + "'")
        # else:
        #     ExecSQL("copy projects from '" + FichierZooPrj.as_posix() + "'")
        #     ExecSQL("copy samples from '" + FichierZooSample.as_posix() + "'")
        #     ExecSQL("copy acquisitions from '" + FichierZooAcq.as_posix() + "'")
        #     ExecSQL("copy obj_head from '" + FichierZooObjHead.as_posix() + "'")
        #     ExecSQL("copy obj_field from '" + FichierZooObjField.as_posix() + "'")
        #     logging.info("Projets EcoTaxa Zoo imported from tsv")

        # Creation de projets particules
        PartPrj = PartProjectGeneratorTypeA()
        PartPrj.Generate("EcoPart TU Project UVP 1")

        PartPrj = PartProjectGeneratorTypeA()
        PartPrj.Generate("EcoPart TU Project UVP 2 Precomputed")

        db.session.commit()

        for S in db.session.query(part_samples).filter_by(pprojid=PartPrj.pprojid):
            ComputeHistoRed(S.psampleid)
            match_result, sampleid = ComputeZooMatch(ecotaxa_if, S.psampleid, PartPrj.Zooprojid)
            # Ca a l'air voulu que, par exemple, sample02 ne match pas dans EcoTaxa
            # assert "Matched" in match_result, match_result

        db.session.commit()  # Requis car sinon cette transaction ne voit pas les modifications faites en SQL
        # db.get_engine().echo=True # Permet d'activer l'echo mais en double exemplaire
        # logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG) # autre moyen d'activer l'echo
        # 3 methodes alternatives pour parcourir des samples avec une condition is not null
        # for S in database.GetAll("select psampleid from part_samples where sampleid is not null and pprojid=%(pprojid)s",
        #                              {'pprojid': PartPrj.pprojid}):
        #    common_sample_import.ComputeZooHisto(S['psampleid'], 'uvp5')
        # for S in part_samples.query.filter_by(pprojid=PartPrj.pprojid).filter(part_samples.sampleid != None): # Marche aussi
        for S in db.session.query(part_samples).filter_by(pprojid=PartPrj.pprojid).filter(text("sampleid is not null")):
            ComputeZooHisto(ecotaxa_if, S.psampleid, 'uvp5')
        logging.info("Detailled & Zoo Computed")
        # pour voir le résultat du projet N°2 computed, doit ête identique à PartProjectTU1Graph.png
        # http://127.0.0.2:5002/part/?MapN=&MapW=&MapE=&MapS=&filt_fromdate=&filt_todate=&filt_instrum=&filt_proftype=&filt_uproj=2&gpr=cl6&gpr=cl7&gpr=cl8&gpd=cl17&gpd=cl18&gpd=cl19&gpd=cl20&gpd=cl22&gpd=cl23&filt_depthmin=&filt_depthmax=&XScale=I&TimeScale=R&taxolb=1&taxolb=85036&taxolb=85037&taxolb=11762&taxolb=84960&taxochild=1

        GenerateUVP5Folder(SrcProjectTitle="EcoPart TU Project UVP 2 Precomputed",
                           TargetProjectTitle="EcoPart TU Project UVP 5 pour load BRU",
                           DirName="tu1_uvp5bru",
                           ZooProjectTitle="EcoPart TU Zoo Project for BRU",
                           SamplePrefix="bru")

        GenerateUVP5Folder(SrcProjectTitle="EcoPart TU Project UVP 2 Precomputed",
                           TargetProjectTitle="EcoPart TU Project UVP 5 pour load BRU1",
                           DirName="tu1_uvp5bru1",
                           BRUFormat="bru1",
                           ZooProjectTitle="EcoPart TU Zoo Project for BRU1",
                           SamplePrefix="bru1")

        PartPrj = PartProjectGeneratorTypeUVP6()
        PartPrj.Generate("EcoPart TU Project UVP6 Ref")

        GenerateUVPAppFolder(SrcProjectTitle="EcoPart TU Project UVP6 Ref",
                             TargetProjectTitle="EcoPart TU Project UVP 6 from UVP APP",
                             DirName="tu1_uvp6uvpapp",
                             ZooProjectTitle="EcoPart TU Zoo Project for UVPAPP")

        # On importe les données car c'est requis pour générer les données du LISST
        part_project = db.session.query(part_projects).filter_by(
            ptitle="EcoPart TU Project UVP 6 from UVP APP").first()
        if part_project is None:
            raise Exception("UVPAPP Project Missing")
        with TaskInstance(app, "TaskPartZooscanImport", GetParams=f"p={part_project.pprojid}",
                          post_params={"new_1": "uvpappsample01", "new_2": "uvpappsample02", "new_3": "uvpappsample03",
                                       "new_4": "uvpappsampleT1", "new_5": "uvpappsampleT2", "new_6": "uvpappsampleT3",
                                       "starttask": "Y"}) as T:
            print(f"TaskID={T.TaskID}")
            T.RunTask()

        GenerateLISSTFolder(SrcProjectTitle="EcoPart TU Project UVP 6 from UVP APP"  # pas le ref car on a besoin des Bv
                            , TargetProjectTitle="EcoPart TU Project LISST"
                            , DirName="tu1_lisst")

        GenerateUVPRemoteLambdaFolder(SrcProjectTitle="EcoPart TU Project UVP 6 from UVP APP"
                                      , TargetProjectTitle="EcoPart TU Project UVP Remote Lambda HTTP"
                                      , DirName="tu1_uvp6remotelambda")

        GenerateUVPRemoteLambdaFTPProject(SrcProjectTitle="EcoPart TU Project UVP Remote Lambda HTTP"
                                          , TargetProjectTitle="EcoPart TU Project UVP Remote Lambda FTP"
                                          , DirName="tu1_uvp6remotelambda")

        PartPrj = PartProjectGeneratorTypeGeo()
        PartPrj.Generate("Geo Sample on all the map")

        PartPrj = PartProjectGeneratorTypeGeoMosaic()
        PartPrj.Generate("Geo Sample from Mosaic")


if __name__ == '__main__':
    try:
        main()
    finally:
        kill_backend()
