from os.path import dirname, realpath,join
from pathlib import Path
from appli import database,app,g,db,gvp,gvg,request
from appli.part import database as dbpart
from appli.tasks import taskmanager
#from pytest_mock import mocker
import pytest,logging,os
import unittest.mock
from appli import appli
from flask_login import current_user,login_user
from sqlalchemy import Table, text
import subprocess
import runtask


HERE = Path(dirname(realpath(__file__)))
DATA_DIR = (HERE / ".." / "data").resolve()
DATA_DIR_tu1_uvp6uvpapp=DATA_DIR/"tu1_uvp6uvpapp"

@pytest.fixture
def app():
    with appli.app.app_context():
        g.db = None
        yield appli.app

# Loggue un user, mais doit être fait après la création du contexte de test
def LogUser(email):
    login_user(database.users.query.filter_by(email=email).first())

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

def evaluate_sampleTypeAkeyValues(psampleid):
    """On teste des valeurs clés du sample, les # & BV des 2 premières classe et le watervolume"""
    sql = """select sum(watervolume) swatervolume,sum(class17) sclass17,sum(biovol17*watervolume) sbiovol17 
        ,sum(class18) sclass18 ,sum(biovol18*watervolume) sbiovol18
    from part_histopart_det t where psampleid=%s"""
    res = database.GetRow(sql, [psampleid])
    assert res['swatervolume'] == pytest.approx(339)
    assert res['sclass17'] == pytest.approx(75150)
    assert res['sbiovol17'] == pytest.approx(3.139335)
    assert res['sclass18'] == pytest.approx(20100)
    assert res['sbiovol18'] == pytest.approx(1.915367)
    sql="""select  classif_id, sum(watervolume)  swatervolume, sum(nbr)  snbr , sum(totalbiovolume) stotalbiovolume
    from part_histocat  where psampleid=%s    group by classif_id"""
    res = database.GetAssoc(sql, [psampleid])
    assert res[11762]['snbr'] == 100
    assert res[11762]['stotalbiovolume'] == pytest.approx(204.2602)
    assert res[85036]['snbr'] == 500
    assert res[85036]['stotalbiovolume'] == pytest.approx(1202.503)
    assert res[85037]['snbr'] == 500
    assert res[85037]['stotalbiovolume'] == pytest.approx(835.4788)
    assert res[85057]['snbr'] == 1000
    assert res[85057]['stotalbiovolume'] == pytest.approx(959.6036)
    assert res[85076]['snbr'] == 1000
    assert res[85076]['stotalbiovolume'] == pytest.approx(941.7783)


def test_import_uvp6_uvpapp(app,caplog,tmpdir):
    caplog.set_level(logging.DEBUG)  # pour mise au point
    caplog.set_level(logging.CRITICAL) # pour execution très silencieuse
    part_project = dbpart.part_projects.query.filter_by(ptitle="EcoPart TU Project UVP 6 from UVP APP").first()
    if part_project is None:
        pytest.fail("UVPAPP Project Missing")
    pprojid=part_project.pprojid
    with TaskInstance(app,"TaskPartZooscanImport", GetParams=f"p={part_project.pprojid}", PostParams={"new_1": "sample01","new_2": "sample02","new_3": "sample03","new_4": "sampleT1","new_5": "sampleT2","new_6": "sampleT3","starttask": "Y"}) as T:
        print(f"TaskID={T.TaskID}")
        T.RunTask()
        ExcludedCols=[f'biovol{i:02d}' for i in range (1,46)] # Les biovolumes ne sont pas calculés dans le modèle.
        ExcludedCols.append('psampleid')
        part_project_ref = dbpart.part_projects.query.filter_by(ptitle="EcoPart TU Project UVP 2 Precomputed").first()
        if part_project_ref is None:
            pytest.fail("BRU Ref Project Missing")
        Sample1_ref=dbpart.part_samples.query.filter_by(pprojid=part_project_ref.pprojid,profileid="sample01").first()
        Sample1=dbpart.part_samples.query.filter_by(pprojid=pprojid,profileid="sample01").first()
        SampleT1=dbpart.part_samples.query.filter_by(pprojid=pprojid,profileid="sampleT1").first()

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
            evaluate_sampleTypeAkeyValues(sampleid)


def test_import_uvp5_BRU(app,caplog,tmpdir):
    caplog.set_level(logging.DEBUG)  # pour mise au point
    caplog.set_level(logging.CRITICAL) # pour execution très silencieuse
    part_project = dbpart.part_projects.query.filter_by(ptitle="EcoPart TU Project UVP 5 pour load BRU").first()
    if part_project is None:
        pytest.fail("BRU Project Missing")
    pprojid=part_project.pprojid
    with TaskInstance(app,"TaskPartZooscanImport", GetParams=f"p={part_project.pprojid}", PostParams={"new_1": "sample01","new_2": "sample02","new_3": "sample03","starttask": "Y"}) as T:
        print(f"TaskID={T.TaskID}")
        T.RunTask()
        ExcludedCols=[f'biovol{i:02d}' for i in range (1,46)] # Les biovolumes ne sont pas calculés dans le modèle.
        ExcludedCols.append('psampleid')
        ExcludedCols.append('datetime') # les projets UVP5 ne gèrent pas cette colonne historiquement.
        part_project_ref = dbpart.part_projects.query.filter_by(ptitle="EcoPart TU Project UVP 2 Precomputed").first()
        if part_project_ref is None:
            pytest.fail("BRU Ref Project Missing")
        Sample1_ref=dbpart.part_samples.query.filter_by(pprojid=part_project_ref.pprojid,profileid="sample01").first()
        Sample1=dbpart.part_samples.query.filter_by(pprojid=pprojid,profileid="sample01").first()

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
        evaluate_sampleTypeAkeyValues(Sample1.psampleid)

def test_import_uvp5_BRU1(app,caplog,tmpdir):
    caplog.set_level(logging.DEBUG)  # pour mise au point
    caplog.set_level(logging.CRITICAL) # pour execution très silencieuse
    part_project = dbpart.part_projects.query.filter_by(ptitle="EcoPart TU Project UVP 5 pour load BRU1").first()
    if part_project is None:
        pytest.fail("BRU1 Project Missing")
    pprojid=part_project.pprojid
    with TaskInstance(app,"TaskPartZooscanImport", GetParams=f"p={part_project.pprojid}", PostParams={"new_1": "sample01","new_2": "sample02","new_3": "sample03","starttask": "Y"}) as T:
        print(f"TaskID={T.TaskID}")
        T.RunTask()
        ExcludedCols=[f'biovol{i:02d}' for i in range (1,46)] # Les biovolumes ne sont pas calculés dans le modèle.
        ExcludedCols.append('psampleid')
        ExcludedCols.append('datetime') # les projets UVP5 ne gèrent pas cette colonne historiquement.
        part_project_ref = dbpart.part_projects.query.filter_by(ptitle="EcoPart TU Project UVP 2 Precomputed").first()
        if part_project_ref is None:
            pytest.fail("BRU Ref Project Missing")
        Sample1_ref=dbpart.part_samples.query.filter_by(pprojid=part_project_ref.pprojid,profileid="sample01").first()
        Sample1=dbpart.part_samples.query.filter_by(pprojid=pprojid,profileid="sample01").first()

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
        evaluate_sampleTypeAkeyValues(Sample1.psampleid)

def test_import_lisst(app,caplog,tmpdir):
    caplog.set_level(logging.DEBUG)  # pour mise au point
    caplog.set_level(logging.CRITICAL) # pour execution très silencieuse
    part_project = dbpart.part_projects.query.filter_by(ptitle="EcoPart TU Project LISST").first()
    if part_project is None:
        pytest.fail("LISST Project Missing")
    pprojid=part_project.pprojid
    with TaskInstance(app,"TaskPartZooscanImport", GetParams=f"p={part_project.pprojid}", PostParams={"new_1": "sample01","new_2": "sample02","new_3": "sample03","starttask": "Y"}) as T: # on importe pas les temporels car ils ne sont pas correctement traités
        print(f"TaskID={T.TaskID}")
        T.RunTask()
        Sample1=dbpart.part_samples.query.filter_by(pprojid=pprojid,profileid="sample01").first()
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




