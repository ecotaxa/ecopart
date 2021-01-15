from os.path import dirname, realpath
from pathlib import Path
from appli import database,g,db
from appli.part import database as dbpart,uvp6remote_sample_import
from appli.tasks import taskmanager
import pytest,logging,os,re
from appli import appli
from flask_login import login_user
from sqlalchemy import Table, text
import subprocess
import runtask
from pytest_httpserver import HTTPServer
from werkzeug.wrappers import Response
import requests
from ftplib import FTP
from pytest_localftpserver.plugin import PytestLocalFTPServer


HERE = Path(dirname(realpath(__file__)))
DATA_DIR = (HERE / ".." /  ".." / "data").resolve()


@pytest.fixture
def app():
    with appli.app.app_context():
        g.db = None
        yield appli.app

# Loggue un user, mais doit être fait après la création du contexte de test
def LogUser(email):
    login_user(db.session.query(database.users).filter_by(email=email).first())

def GetLastTaskID():
    return database.GetAll("select max(id) maxid from temp_tasks")[0]['maxid']

class TaskInstance:
    def __init__(self, app, ClassName, GetParams="", PostParams=None, Login='admin'):
        if PostParams is None:
            PostParams = dict()
        self.app=app
        self.ClassName = ClassName
        self.GetParams = GetParams
        self.PostParams = PostParams
        self.Login = Login
        self.ctx=app.test_request_context(f"/Task/Create/{ClassName}?{GetParams}",
                                      data=PostParams)
        self.TaskID=None
    def __enter__(self):
        self.ctx.__enter__()
        Previoustaskid = GetLastTaskID()
        LogUser(self.Login)
        self.app.PythonExecutable="PYTESTDRIVEN"
        taskmanager.TaskCreateRouter(self.ClassName)
        self.TaskID= GetLastTaskID()
        if self.TaskID== Previoustaskid:
            pytest.fail("Taks Not correctly created")
        return self

    def RunTask(self):
        runtask.RunTask(self.TaskID,LogLevel=logging.getLogger().level)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ctx.__exit__(exc_type, exc_val, exc_tb)


# noinspection DuplicatedCode
def dump_table(out, a_table: db.Model, where,skipcol=()):
    base_table: Table = a_table.__table__
    cols = [a_col.name for a_col in base_table.columns]
    pk = [a_pk_col.name for a_pk_col in base_table.primary_key]
    res = db.session.execute(base_table.select().where(text(where)).order_by(*pk))
    print(f"====================================\n{str(base_table)}\n====================================\n", file=out)
    for a_row in res:
        vals = []
        for col, col_val in zip(cols, a_row):
            if col_val is not None and col not in skipcol:
                vals.append("%s=%s" % (col, repr(col_val)))
        ln = "%s(%s)" % (base_table, ",".join(vals))
        print(ln, file=out)

# with open("testdump.txt", "w") as fd:
#     dump_table(fd,dbpart.part_histopart_reduit,"psampleid=6",skipcol=('psampleid'))

def ShowOnWinmerge(File1,File2):
    cmd = f'"C:\\Program Files\\WinMerge\\WinMergeU.exe" "{File1}" "{File2}"'
    # print(cmd)
    subprocess.call(cmd)

def check_sampleTypeAkeyValues(psampleid, CompareBiovolumePart=True, CompareZoo=True, NbrImage=1, Coeff=1.0, CompareBiovolumeZoo=True):
    """On teste des valeurs clés du sample, les # & BV des 2 premières classe et le watervolume"""
    sql = """select sum(watervolume) swatervolume,sum(class17) sclass17,sum(biovol17*watervolume) sbiovol17 
        ,sum(class18) sclass18 ,sum(biovol18*watervolume) sbiovol18
    from part_histopart_det t where psampleid=%s"""
    res = database.GetRow(sql, [psampleid])
    assert res['swatervolume'] == pytest.approx(339*NbrImage)
    # le rel est utile pour les coeff 0.8 qui sur des valeur entières provoque des perte de particules entière à la génération,
    # donc tolérence de 1% dans ces cas là
    assert res['sclass17'] == pytest.approx(75150*NbrImage*Coeff,rel=0.01 if Coeff!=1 else 0)
    assert res['sclass18'] == pytest.approx(20100*NbrImage*Coeff,rel=0.01 if Coeff!=1 else 0)
    if CompareBiovolumePart:
        assert res['sbiovol17'] == pytest.approx(3.139335*NbrImage*Coeff,rel=0.01 if Coeff!=1 else 1E-6)
        assert res['sbiovol18'] == pytest.approx(1.915367*NbrImage*Coeff,rel=0.01 if Coeff!=1 else 1E-6)
    if CompareZoo:
        sql="""select  classif_id, sum(watervolume)  swatervolume, sum(nbr)  snbr , sum(totalbiovolume) stotalbiovolume
        from part_histocat  where psampleid=%s    group by classif_id"""
        res = database.GetAssoc(sql, [psampleid])
        assert res[11762]['snbr'] == 100
        assert res[85036]['snbr'] == 500
        assert res[85037]['snbr'] == 500
        assert res[85057]['snbr'] == 1000
        assert res[85076]['snbr'] == 1000
        if CompareBiovolumeZoo:
            assert res[11762]['stotalbiovolume'] == pytest.approx(204.2602)
            assert res[85036]['stotalbiovolume'] == pytest.approx(1202.503)
            assert res[85037]['stotalbiovolume'] == pytest.approx(835.4788)
            assert res[85057]['stotalbiovolume'] == pytest.approx(959.6036)
            assert res[85076]['stotalbiovolume'] == pytest.approx(941.7783)

def check_CtdValues(psampleid:int,ctdtype:int):
    sql = """select sum(chloro_fluo) schloro_fluo,sum(depth_salt_water) sdepth_salt_water
    from part_ctd t where psampleid=%s"""
    res = database.GetRow(sql, [psampleid])
    if ctdtype==1:
        assert res['schloro_fluo'] == pytest.approx(59.02659)
        assert res['sdepth_salt_water'] == pytest.approx(125067.93)
    elif ctdtype == 2:
        assert res['schloro_fluo'] == pytest.approx(75.9722)
        assert res['sdepth_salt_water'] == pytest.approx(509406.79)
    else:
        pytest.fail(f"Invalid ctdtype:{ctdtype}")


# noinspection SqlResolve
def clean_existing_projectdata(pprojid:int):
    for tbl in ('part_histopart_reduit','part_histopart_det','part_histocat','part_histocat_lst','part_histocat','part_ctd'):
        database.ExecSQL(f"delete from {tbl} where psampleid in (select part_samples.psampleid from part_samples where pprojid={pprojid})")
    database.ExecSQL(f"delete from part_samples where pprojid={pprojid}")


# noinspection DuplicatedCode
def test_import_uvp6_uvpapp(app,caplog,tmpdir):
    caplog.set_level(logging.DEBUG)  # pour mise au point
    caplog.set_level(logging.CRITICAL) # pour execution très silencieuse
    part_project = db.session.query(dbpart.part_projects).filter_by(ptitle="EcoPart TU Project UVP 6 from UVP APP").first()
    if part_project is None:
        pytest.fail("UVPAPP Project Missing")
    pprojid=part_project.pprojid
    clean_existing_projectdata(pprojid)
    with TaskInstance(app,"TaskPartZooscanImport", GetParams=f"p={part_project.pprojid}", PostParams={"new_1": "sample01","new_2": "sample02","new_3": "sample03","new_4": "sampleT1","new_5": "sampleT2","new_6": "sampleT3","starttask": "Y"}) as T:
        print(f"TaskID={T.TaskID}")
        T.RunTask()
        ExcludedCols=[f'biovol{i:02d}' for i in range (1,46)] # Les biovolumes ne sont pas calculés dans le modèle.
        ExcludedCols.append('psampleid')
        part_project_ref = db.session.query(dbpart.part_projects).filter_by(ptitle="EcoPart TU Project UVP 2 Precomputed").first()
        if part_project_ref is None:
            pytest.fail("BRU Ref Project Missing")
        Sample1_ref=db.session.query(dbpart.part_samples).filter_by(pprojid=part_project_ref.pprojid,profileid="sample01").first()
        Sample1=db.session.query(dbpart.part_samples).filter_by(pprojid=pprojid,profileid="sample01").first()
        SampleT1=db.session.query(dbpart.part_samples).filter_by(pprojid=pprojid,profileid="sampleT1").first()
        Sample2 = db.session.query(dbpart.part_samples).filter_by(pprojid=pprojid, profileid="sample02").first()
        SampleT2 = db.session.query(dbpart.part_samples).filter_by(pprojid=pprojid, profileid="sampleT2").first()
        Sample3=db.session.query(dbpart.part_samples).filter_by(pprojid=pprojid,profileid="sample03").first()
        SampleT3=db.session.query(dbpart.part_samples).filter_by(pprojid=pprojid,profileid="sampleT3").first()

        reffile=tmpdir.join("reffile.txt")
        datafile=tmpdir.join("datafile.txt")
        with open(reffile, "w") as fd:
            dump_table(fd, dbpart.part_histopart_reduit, f"psampleid={Sample1_ref.psampleid}", skipcol=ExcludedCols)
            dump_table(fd, dbpart.part_histopart_det, f"psampleid={Sample1_ref.psampleid}", skipcol=ExcludedCols)
        with open(datafile, "w") as fd:
            dump_table(fd, dbpart.part_histopart_reduit, f"psampleid={Sample1.psampleid}", skipcol=ExcludedCols)
            dump_table(fd, dbpart.part_histopart_det, f"psampleid={Sample1.psampleid}", skipcol=ExcludedCols)
        cmpresult=reffile.read() ==  datafile.read() # en cas d'ecart evite d'afficher un mega message d'erreur, plutot activer winmerge
        if not cmpresult: ShowOnWinmerge(reffile, datafile)
        assert cmpresult
        for sampleid in (Sample1.psampleid,SampleT1.psampleid):
            check_sampleTypeAkeyValues(sampleid)
        for sampleid in (Sample2.psampleid,SampleT2.psampleid):
            check_sampleTypeAkeyValues(sampleid, CompareZoo=False, NbrImage=2, Coeff=1.2)
        for sampleid in (Sample3.psampleid,SampleT3.psampleid):
            check_sampleTypeAkeyValues(sampleid, CompareZoo=False, NbrImage=3, Coeff=0.8)
        check_CtdValues(Sample2.psampleid,1)
        check_CtdValues(Sample3.psampleid, 2)


# noinspection DuplicatedCode
def test_import_uvp5_BRU(app,caplog,tmpdir):
    caplog.set_level(logging.DEBUG)  # pour mise au point
    caplog.set_level(logging.CRITICAL) # pour execution très silencieuse
    part_project = db.session.query(dbpart.part_projects).filter_by(ptitle="EcoPart TU Project UVP 5 pour load BRU").first()
    if part_project is None:
        pytest.fail("BRU Project Missing")
    pprojid=part_project.pprojid
    clean_existing_projectdata(pprojid)
    with TaskInstance(app,"TaskPartZooscanImport", GetParams=f"p={part_project.pprojid}", PostParams={"new_1": "sample01","new_2": "sample02","new_3": "sample03","starttask": "Y"}) as T:
        print(f"TaskID={T.TaskID}")
        T.RunTask()
        ExcludedCols=[f'biovol{i:02d}' for i in range (1,46)] # Les biovolumes ne sont pas calculés dans le modèle.
        ExcludedCols.append('psampleid')
        ExcludedCols.append('datetime') # les projets UVP5 ne gèrent pas cette colonne historiquement.
        part_project_ref = db.session.query(dbpart.part_projects).filter_by(ptitle="EcoPart TU Project UVP 2 Precomputed").first()
        if part_project_ref is None:
            pytest.fail("BRU Ref Project Missing")
        Sample1_ref=db.session.query(dbpart.part_samples).filter_by(pprojid=part_project_ref.pprojid,profileid="sample01").first()
        Sample1=db.session.query(dbpart.part_samples).filter_by(pprojid=pprojid,profileid="sample01").first()

        reffile=tmpdir.join("reffile.txt")
        datafile=tmpdir.join("datafile.txt")
        with open(reffile, "w") as fd:
            dump_table(fd, dbpart.part_histopart_reduit, f"psampleid={Sample1_ref.psampleid}", skipcol=ExcludedCols)
            dump_table(fd, dbpart.part_histopart_det, f"psampleid={Sample1_ref.psampleid}", skipcol=ExcludedCols)
        with open(datafile, "w") as fd:
            dump_table(fd, dbpart.part_histopart_reduit, f"psampleid={Sample1.psampleid}", skipcol=ExcludedCols)
            dump_table(fd, dbpart.part_histopart_det, f"psampleid={Sample1.psampleid}", skipcol=ExcludedCols)


        cmpresult=reffile.read() ==  datafile.read() # en cas d'ecart evite d'afficher un mega message d'erreur, plutot activer winmerge
        if not cmpresult: ShowOnWinmerge(reffile, datafile)
        assert cmpresult
        check_sampleTypeAkeyValues(Sample1.psampleid)
        Sample2=db.session.query(dbpart.part_samples).filter_by(pprojid=pprojid,profileid="sample02").first()
        Sample3=db.session.query(dbpart.part_samples).filter_by(pprojid=pprojid,profileid="sample03").first()
        check_CtdValues(Sample2.psampleid,1)
        check_CtdValues(Sample3.psampleid, 2)

# noinspection DuplicatedCode
def test_import_uvp5_BRU1(app,caplog,tmpdir):
    caplog.set_level(logging.DEBUG)  # pour mise au point
    caplog.set_level(logging.CRITICAL) # pour execution très silencieuse
    part_project = db.session.query(dbpart.part_projects).filter_by(ptitle="EcoPart TU Project UVP 5 pour load BRU1").first()
    if part_project is None:
        pytest.fail("BRU1 Project Missing")
    pprojid=part_project.pprojid
    clean_existing_projectdata(pprojid)
    with TaskInstance(app,"TaskPartZooscanImport", GetParams=f"p={part_project.pprojid}", PostParams={"new_1": "sample01","new_2": "sample02","new_3": "sample03","starttask": "Y"}) as T:
        print(f"TaskID={T.TaskID}")
        T.RunTask()
        ExcludedCols=[f'biovol{i:02d}' for i in range (1,46)] # Les biovolumes ne sont pas calculés dans le modèle.
        ExcludedCols.append('psampleid')
        ExcludedCols.append('datetime') # les projets UVP5 ne gèrent pas cette colonne historiquement.
        part_project_ref = db.session.query(dbpart.part_projects).filter_by(ptitle="EcoPart TU Project UVP 2 Precomputed").first()
        if part_project_ref is None:
            pytest.fail("BRU Ref Project Missing")
        Sample1_ref=db.session.query(dbpart.part_samples).filter_by(pprojid=part_project_ref.pprojid,profileid="sample01").first()
        Sample1=db.session.query(dbpart.part_samples).filter_by(pprojid=pprojid,profileid="sample01").first()

        reffile=tmpdir.join("reffile.txt")
        datafile=tmpdir.join("datafile.txt")
        with open(reffile, "w") as fd:
            dump_table(fd, dbpart.part_histopart_reduit, f"psampleid={Sample1_ref.psampleid}", skipcol=ExcludedCols)
            dump_table(fd, dbpart.part_histopart_det, f"psampleid={Sample1_ref.psampleid}", skipcol=ExcludedCols)
        with open(datafile, "w") as fd:
            dump_table(fd, dbpart.part_histopart_reduit, f"psampleid={Sample1.psampleid}", skipcol=ExcludedCols)
            dump_table(fd, dbpart.part_histopart_det, f"psampleid={Sample1.psampleid}", skipcol=ExcludedCols)


        cmpresult=reffile.read() ==  datafile.read() # en cas d'ecart evite d'afficher un mega message d'erreur, plutot activer winmerge
        if not cmpresult: ShowOnWinmerge(reffile, datafile)
        assert cmpresult
        check_sampleTypeAkeyValues(Sample1.psampleid)
        Sample2=db.session.query(dbpart.part_samples).filter_by(pprojid=pprojid,profileid="sample02").first()
        Sample3=db.session.query(dbpart.part_samples).filter_by(pprojid=pprojid,profileid="sample03").first()
        check_CtdValues(Sample2.psampleid,1)
        check_CtdValues(Sample3.psampleid, 2)

def test_import_lisst(app,caplog,tmpdir):
    caplog.set_level(logging.DEBUG)  # pour mise au point
    caplog.set_level(logging.CRITICAL) # pour execution très silencieuse
    part_project = db.session.query(dbpart.part_projects).filter_by(ptitle="EcoPart TU Project LISST").first()
    if part_project is None:
        pytest.fail("LISST Project Missing")
    pprojid=part_project.pprojid
    clean_existing_projectdata(pprojid)
    with TaskInstance(app,"TaskPartZooscanImport", GetParams=f"p={part_project.pprojid}", PostParams={"new_1": "sample01","new_2": "sample02","new_3": "sample03","starttask": "Y"}) as T: # on importe pas les temporels car ils ne sont pas correctement traités
        print(f"TaskID={T.TaskID}")
        T.RunTask()
        Sample1=db.session.query(dbpart.part_samples).filter_by(pprojid=pprojid,profileid="sample01").first()
        # On controle le total biovolume avec quelques PB
        #  sur le lisst on a pas les watervolume associés on fait donc la some des concentrations (qui dans l'abosolu n'as pas de sens
        #  puisqu'il y a le même nombre de ligne dans l'histograme
        # les classe du LISST ne sont pas les même il y a des mécanisme de ventilation proportionnelle dans les classe EcoPart
        # il faut donc regrouper certaines classes pour les comparer avec un import UVP
        sql = """select sum(biovol17) biovol17raw
                        ,sum(biovol18+biovol19+biovol20) biovol18_20raw
                        ,sum(biovol22) biovol22raw
                        ,sum(biovol23+biovol24) biovol2324raw        
        from part_histopart_det t where psampleid=%s"""
        res = database.GetRow(sql, [Sample1.psampleid])
        assert res['biovol17raw'] == pytest.approx(2.7781733)
        assert res['biovol18_20raw'] == pytest.approx(2.2831353)
        assert res['biovol22raw'] == pytest.approx(3.1642698)
        assert res['biovol2324raw'] == pytest.approx(39.27267)
        Sample2=db.session.query(dbpart.part_samples).filter_by(pprojid=pprojid,profileid="sample02").first()
        Sample3=db.session.query(dbpart.part_samples).filter_by(pprojid=pprojid,profileid="sample03").first()
        check_CtdValues(Sample2.psampleid,1)
        check_CtdValues(Sample3.psampleid, 2)


@pytest.fixture
def httpserver_listen_address():
    return "127.0.0.1", 5050

def HttpServeurStaticHandler(req)->Response:
    if req.path.endswith('/'):
        directory=DATA_DIR/req.path[1:-1]
        result=""
        for fichier in directory.glob("*"):
            result += f"<a href='{fichier.name}'>{fichier.name}</a><br>"
            # print(fichier.name)
        return Response(result)
    Fichier=DATA_DIR/req.path[1:]
    return Response(Fichier.read_text())

# noinspection DuplicatedCode
def test_import_uvp_remote_lambda_http(app,caplog,tmpdir,httpserver: HTTPServer):
    caplog.set_level(logging.DEBUG)  # pour mise au point
    caplog.set_level(logging.CRITICAL) # pour execution très silencieuse
    part_project = db.session.query(dbpart.part_projects).filter_by(ptitle="EcoPart TU Project UVP Remote Lambda HTTP").first()
    if part_project is None:
        pytest.fail("UVPAPP Project Missing")
    pprojid=part_project.pprojid
    clean_existing_projectdata(pprojid)
    httpserver.expect_request("/TestDuServeurHTTP/").respond_with_data("OK permanent")
    httpserver.expect_request(re.compile("^/")).respond_with_handler(HttpServeurStaticHandler)
    # test des fonction qui emulent le serveur HTTP
    assert requests.get("http://localhost:5050/TestDuServeurHTTP/").text == "OK permanent"
    assert requests.get("http://localhost:5050/tu1_uvp6remotelambda/").text.startswith("<a")
    assert requests.get("http://localhost:5050/tu1_uvp6remotelambda/sample01_UVPSN_DEPTH_BLACK.txt").text.startswith("DATE_TIME\t")
    # print(httpserver.url_for("/tu1_uvp6remotelambda/"))

    RSF = uvp6remote_sample_import.RemoteServerFetcher(pprojid)
    Samples = RSF.GetServerFiles()
    # print(Samples)
    assert 'sample01' in Samples # test de la récupération de la liste des fichiers
    assert len(Samples)==6
    # return

    with TaskInstance(app,"TaskPartZooscanImport", GetParams=f"p={part_project.pprojid}", PostParams={"starttask": "Y"}) as T:
        print(f"TaskID={T.TaskID}")
        T.RunTask()
        ExcludedCols=[f'biovol{i:02d}' for i in range (1,46)] # Les biovolumes ne sont pas calculés dans le modèle.
        ExcludedCols.append('psampleid')
        ExcludedCols.extend([f'class{i:02d}' for i in range (1,17)])
        ExcludedCols.extend([f'class{i:02d}' for i in range(35, 46)])
        part_project_ref = db.session.query(dbpart.part_projects).filter_by(ptitle="EcoPart TU Project UVP 2 Precomputed").first()
        if part_project_ref is None:
            pytest.fail("BRU Ref Project Missing")
        Sample1_ref=db.session.query(dbpart.part_samples).filter_by(pprojid=part_project_ref.pprojid,profileid="sample01").first()
        Sample1=db.session.query(dbpart.part_samples).filter_by(pprojid=pprojid,profileid="sample01").first()
        SampleT1=db.session.query(dbpart.part_samples).filter_by(pprojid=pprojid,profileid="sampleT1").first()
        Sample2 = db.session.query(dbpart.part_samples).filter_by(pprojid=pprojid, profileid="sample02").first()
        SampleT2 = db.session.query(dbpart.part_samples).filter_by(pprojid=pprojid, profileid="sampleT2").first()
        Sample3=db.session.query(dbpart.part_samples).filter_by(pprojid=pprojid,profileid="sample03").first()
        SampleT3=db.session.query(dbpart.part_samples).filter_by(pprojid=pprojid,profileid="sampleT3").first()

        reffile=tmpdir.join("reffile.txt")
        datafile=tmpdir.join("datafile.txt")
        with open(reffile, "w") as fd:
            dump_table(fd, dbpart.part_histopart_reduit, f"psampleid={Sample1_ref.psampleid}", skipcol=ExcludedCols)
            dump_table(fd, dbpart.part_histopart_det, f"psampleid={Sample1_ref.psampleid}", skipcol=ExcludedCols)
        with open(datafile, "w") as fd:
            dump_table(fd, dbpart.part_histopart_reduit, f"psampleid={Sample1.psampleid}", skipcol=ExcludedCols)
            dump_table(fd, dbpart.part_histopart_det, f"psampleid={Sample1.psampleid}", skipcol=ExcludedCols)
        cmpresult=reffile.read() ==  datafile.read() # en cas d'ecart evite d'afficher un mega message d'erreur, plutot activer winmerge
        if not cmpresult: ShowOnWinmerge(reffile, datafile)
        assert cmpresult
        for sampleid in (Sample1.psampleid,SampleT1.psampleid):
            check_sampleTypeAkeyValues(sampleid, CompareBiovolumePart=False, CompareBiovolumeZoo=False)
        for sampleid in (Sample2.psampleid,SampleT2.psampleid):
            check_sampleTypeAkeyValues(sampleid, CompareBiovolumePart=False, CompareZoo=False, NbrImage=2, Coeff=1.2)
        for sampleid in (Sample3.psampleid,SampleT3.psampleid):
            check_sampleTypeAkeyValues(sampleid, CompareBiovolumePart=False, CompareZoo=False, NbrImage=3, Coeff=0.8)

os.environ["FTP_USER"] = "MyUser"
os.environ["FTP_PASS"] = "MyPassword"
os.environ["FTP_PORT"] = "21"
os.environ["FTP_HOME"] = DATA_DIR.as_posix()
# noinspection DuplicatedCode
def test_import_uvp_remote_lambda_ftp(app,caplog,tmpdir,ftpserver:PytestLocalFTPServer):
    assert isinstance(ftpserver, PytestLocalFTPServer)
    assert ftpserver.uses_TLS is False
    # print(ftpserver.anon_root)
    # print(ftpserver.get_login_data())
    # test du bon fonctionnement du serveur FTP
    ftp = FTP()
    ftp.connect("127.0.0.1")
    ftp.login("MyUser","MyPassword")
    ftp.cwd('tu1_uvp6remotelambda')
    lstfichiers=ftp.nlst()
    # print(lstfichiers)
    assert "sample01_UVPSN_DEPTH_BLACK.txt" in lstfichiers
    ftp.close()
    # return

    # Test de la fonction Remote FTP, l'ensemble des test est commun à la version FTP, seule la récupératind des fichiers
    # est différente
    caplog.set_level(logging.DEBUG)  # pour mise au point
    caplog.set_level(logging.CRITICAL) # pour execution très silencieuse
    part_project = db.session.query(dbpart.part_projects).filter_by(ptitle="EcoPart TU Project UVP Remote Lambda FTP").first()
    if part_project is None:
        pytest.fail("UVPAPP Project Missing")
    pprojid=part_project.pprojid
    clean_existing_projectdata(pprojid)
    RSF = uvp6remote_sample_import.RemoteServerFetcher(pprojid)
    Samples = RSF.GetServerFiles()
    # print(Samples)
    assert 'sample01' in Samples # test de la récupération de la liste des fichiers
    assert len(Samples)==6
    # return

    with TaskInstance(app,"TaskPartZooscanImport", GetParams=f"p={part_project.pprojid}", PostParams={"starttask": "Y"}) as T:
        print(f"TaskID={T.TaskID}")
        T.RunTask()
        ExcludedCols=[f'biovol{i:02d}' for i in range (1,46)] # Les biovolumes ne sont pas calculés dans le modèle.
        ExcludedCols.append('psampleid')
        ExcludedCols.extend([f'class{i:02d}' for i in range (1,17)])
        ExcludedCols.extend([f'class{i:02d}' for i in range(35, 46)])
        part_project_ref = db.session.query(dbpart.part_projects).filter_by(ptitle="EcoPart TU Project UVP 2 Precomputed").first()
        if part_project_ref is None:
            pytest.fail("BRU Ref Project Missing")
        Sample1_ref=db.session.query(dbpart.part_samples).filter_by(pprojid=part_project_ref.pprojid,profileid="sample01").first()
        Sample1=db.session.query(dbpart.part_samples).filter_by(pprojid=pprojid,profileid="sample01").first()
        SampleT1=db.session.query(dbpart.part_samples).filter_by(pprojid=pprojid,profileid="sampleT1").first()
        Sample2 = db.session.query(dbpart.part_samples).filter_by(pprojid=pprojid, profileid="sample02").first()
        SampleT2 = db.session.query(dbpart.part_samples).filter_by(pprojid=pprojid, profileid="sampleT2").first()
        Sample3=db.session.query(dbpart.part_samples).filter_by(pprojid=pprojid,profileid="sample03").first()
        SampleT3=db.session.query(dbpart.part_samples).filter_by(pprojid=pprojid,profileid="sampleT3").first()

        reffile=tmpdir.join("reffile.txt")
        datafile=tmpdir.join("datafile.txt")
        with open(reffile, "w") as fd:
            dump_table(fd, dbpart.part_histopart_reduit, f"psampleid={Sample1_ref.psampleid}", skipcol=ExcludedCols)
            dump_table(fd, dbpart.part_histopart_det, f"psampleid={Sample1_ref.psampleid}", skipcol=ExcludedCols)
        with open(datafile, "w") as fd:
            dump_table(fd, dbpart.part_histopart_reduit, f"psampleid={Sample1.psampleid}", skipcol=ExcludedCols)
            dump_table(fd, dbpart.part_histopart_det, f"psampleid={Sample1.psampleid}", skipcol=ExcludedCols)
        cmpresult=reffile.read() ==  datafile.read() # en cas d'ecart evite d'afficher un mega message d'erreur, plutot activer winmerge
        if not cmpresult: ShowOnWinmerge(reffile, datafile)
        assert cmpresult
        for sampleid in (Sample1.psampleid,SampleT1.psampleid):
            check_sampleTypeAkeyValues(sampleid, CompareBiovolumePart=False, CompareBiovolumeZoo=False)
        for sampleid in (Sample2.psampleid,SampleT2.psampleid):
            check_sampleTypeAkeyValues(sampleid, CompareBiovolumePart=False, CompareZoo=False, NbrImage=2, Coeff=1.2)
        for sampleid in (Sample3.psampleid,SampleT3.psampleid):
            check_sampleTypeAkeyValues(sampleid, CompareBiovolumePart=False, CompareZoo=False, NbrImage=3, Coeff=0.8)


