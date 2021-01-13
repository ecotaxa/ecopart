from os.path import dirname, realpath,join
from pathlib import Path
import sys,logging,re,csv,configparser
from appli import database,app,g,db
import appli.part.prj as common_sample_import
from appli.part import database as dbpart
from appli.part.database import part_samples
from sqlalchemy import text
from gendb.UVPRemoteLambdaFileMaker import GenerateUVPRemoteLambdaFolder
from gendb.ZooProjectGeneratorTypeA import ZooProjectGeneratorTypeA
from gendb.PartProjectGeneratorTypeA import PartProjectGeneratorTypeA
from gendb.PartProjectGeneratorTypeUVP6 import PartProjectGeneratorTypeUVP6
from gendb.UVP5FileMaker import GenerateUVP5Folder
from gendb.UVPAppFileMaker import GenerateUVPAppFolder
from gendb.LISSTFileMaker import GenerateLISSTFolder


HERE = Path(dirname(realpath(__file__)))

# Il n'est pas necessaire d'étentre le sys.path si on a mis l'application dans le projet via settings/project structure/Add Content root dans PyCharm car il le fait pour nous
#APPROOT=realpath(join(HERE,"..", "..","..", "py"))
#print(APPROOT)
# sys.path.extend([APPROOT])
#print(sys.path)


import manage
import appli

logging.basicConfig( format='%(asctime)s %(filename)s: %(message)s',level=logging.DEBUG)
# logging.info("Hello")
# exit(0)

# e=db.get_engine()

if '_tu' not in appli.app.config['DB_DATABASE']:
    print("Generation of database cas occur only on _tu database !!!!\nGeneration ABORTED")
    exit(1)
logging.info("Initialize Database")
# Recré la structure de la base de données avec les roles & le user 1 Admin
manage.CreateDB(SkipConfirmation=True,UseExistingDatabase=True)
with app.app_context():# Création d'un contexte pour utiliser les fonction GetAll,ExecSQL
    g.db = None
    logging.info("Import Taxonomy File")
    SourceTaxoFile = realpath(join(HERE, "..","..", "data", "taxonomy.tsv"))
    sql = "copy taxonomy(id, parent_id, name, id_source, display_name, lastupdate_datetime, id_instance, rename_to, source_url, source_desc, creator_email, creation_datetime, nbrobj, nbrobjcum) from '" + SourceTaxoFile + "'"
    database.ExecSQL(sql)
    logging.info("Taxonomy imported")
    # db.session.execute("SET synchronous_commit TO OFF;") # aucun gain
    # crée des projet Zoo
    Prj=ZooProjectGeneratorTypeA()
    Prj.Generate("EcoPart TU Zoo Project 1")

    # Creation de projets particules
    PartPrj = PartProjectGeneratorTypeA()
    PartPrj.Generate("EcoPart TU Project UVP 1")

    PartPrj = PartProjectGeneratorTypeA()
    PartPrj.Generate("EcoPart TU Project UVP 2 Precomputed")
    for S in part_samples.query.filter_by(pprojid=PartPrj.pprojid) :
        common_sample_import.ComputeHistoRed(S.psampleid,'uvp5')
        common_sample_import.ComputeZooMatch(S.psampleid,PartPrj.Zooprojid)
    db.session.commit() # Requis car sinon cette transaction ne voit pas les modifications faites en SQL
    # db.get_engine().echo=True # Permet d'activer l'echo mais en double exemplaire
    # logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG) # autre moyen d'activer l'echo
    # 3 methodes alternatives pour parcourir des samples avec une condition is not null
    # for S in database.GetAll("select psampleid from part_samples where sampleid is not null and pprojid=%(pprojid)s",
    #                              {'pprojid': PartPrj.pprojid}):
    #    common_sample_import.ComputeZooHisto(S['psampleid'], 'uvp5')
    # for S in part_samples.query.filter_by(pprojid=PartPrj.pprojid).filter(part_samples.sampleid != None): # Marche aussi
    for S in part_samples.query.filter_by(pprojid=PartPrj.pprojid).filter(text("sampleid is not null")):
            common_sample_import.ComputeZooHisto(S.psampleid,'uvp5')
    logging.info("Detailled & Zoo Computed")
# pour voir le résultat du projet N°2 computed, doit ête identique à PartProjectTU1Graph.png
# http://127.0.0.2:5002/part/?MapN=&MapW=&MapE=&MapS=&filt_fromdate=&filt_todate=&filt_instrum=&filt_proftype=&filt_uproj=2&gpr=cl6&gpr=cl7&gpr=cl8&gpd=cl17&gpd=cl18&gpd=cl19&gpd=cl20&gpd=cl22&gpd=cl23&filt_depthmin=&filt_depthmax=&XScale=I&TimeScale=R&taxolb=1&taxolb=85036&taxolb=85037&taxolb=11762&taxolb=84960&taxochild=1



    GenerateUVP5Folder(SrcProjectTitle="EcoPart TU Project UVP 2 Precomputed"
                                     ,TargetProjectTitle="EcoPart TU Project UVP 5 pour load BRU"
                                     ,DirName="tu1_uvp5bru")

    GenerateUVP5Folder(SrcProjectTitle="EcoPart TU Project UVP 2 Precomputed"
                                     ,TargetProjectTitle="EcoPart TU Project UVP 5 pour load BRU1"
                                     ,DirName="tu1_uvp5bru1"
                                     ,BRUFormat="bru1")


    PartPrj = PartProjectGeneratorTypeUVP6()
    PartPrj.Generate("EcoPart TU Project UVP6 Ref")

    GenerateUVPAppFolder(SrcProjectTitle="EcoPart TU Project UVP6 Ref"
                                         , TargetProjectTitle="EcoPart TU Project UVP 6 from UVP APP"
                                         , DirName="tu1_uvp6uvpapp")

    # On importe les données car c'est requis pour générer les données du LISST
    part_project = dbpart.part_projects.query.filter_by(ptitle="EcoPart TU Project UVP 6 from UVP APP").first()
    if part_project is None:
        raise Exception("UVPAPP Project Missing")
    from tests.test_import import TaskInstance
    with TaskInstance(app,"TaskPartZooscanImport", GetParams=f"p={part_project.pprojid}", PostParams={"new_1": "sample01","new_2": "sample02","new_3": "sample03","new_4": "sampleT1","new_5": "sampleT2","new_6": "sampleT3","starttask": "Y"}) as T:
        print(f"TaskID={T.TaskID}")
        T.RunTask()


    GenerateLISSTFolder(SrcProjectTitle="EcoPart TU Project UVP 6 from UVP APP" # pas le ref car on a besoin des Bv
                                     ,TargetProjectTitle="EcoPart TU Project LISST"
                                     ,DirName="tu1_lisst")

    GenerateUVPRemoteLambdaFolder(SrcProjectTitle="EcoPart TU Project UVP 6 from UVP APP"
                                  , TargetProjectTitle="EcoPart TU Project UVP Remote Lambda HTTP"
                                  , DirName="tu1_uvp6remotelambda")
