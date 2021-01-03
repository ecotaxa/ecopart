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
    return database.GetAll("select max(id) id from temp_tasks")[0]['id']

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
        import runtask
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


def test_import_uvp6_uvpapp(app,caplog,tmpdir):
    caplog.set_level(logging.DEBUG)  # pour mise au point
    caplog.set_level(logging.CRITICAL) # pour execution très silencieuse
    part_project = dbpart.part_projects.query.filter_by(ptitle="EcoPart TU Project UVP 6 from UVP APP").first()
    part_project_ref = dbpart.part_projects.query.filter_by(ptitle="EcoPart TU Project UVP 2 Precomputed").first()
    if part_project is None:
        pytest.fail("UVPAPP Project Missing")
    if part_project_ref is None:
        pytest.fail("UVPAPP Ref Project Missing")
    with TaskInstance(app,"TaskPartZooscanImport", GetParams=f"p={part_project.pprojid}", PostParams={"new_1": "sample01","new_2": "sample02","new_3": "sample03","starttask": "Y"}) as T:
        print(f"TaskID={T.TaskID}")
        T.RunTask()
        ExcludedCols=[f'biovol{i:02d}' for i in range (1,46)] # Les biovolumes ne sont pas calculés dans le modèle.
        ExcludedCols.append('psampleid')
        part_project = dbpart.part_projects.query.filter_by(ptitle="EcoPart TU Project UVP 6 from UVP APP").first()
        part_project_ref = dbpart.part_projects.query.filter_by(ptitle="EcoPart TU Project UVP 2 Precomputed").first()
        Sample1_ref=dbpart.part_samples.query.filter_by(pprojid=part_project_ref.pprojid,profileid="sample01").first()
        Sample1=dbpart.part_samples.query.filter_by(pprojid=part_project.pprojid,profileid="sample01").first()

        reffile=tmpdir.join("reffile.txt")
        datafile=tmpdir.join("datafile.txt")
        # TODO pouvoir transmettre un nom de fichier et pas forcement un file
        with open(reffile, "w") as fd:
            dump_table(fd, dbpart.part_histopart_reduit, f"psampleid={Sample1_ref.psampleid}", skipcol=ExcludedCols)
            dump_table(fd, dbpart.part_histopart_det, f"psampleid={Sample1_ref.psampleid}", skipcol=ExcludedCols)
        with open(datafile, "w") as fd:
            dump_table(fd, dbpart.part_histopart_reduit, f"psampleid={Sample1.psampleid}", skipcol=ExcludedCols)
            dump_table(fd, dbpart.part_histopart_det, f"psampleid={Sample1.psampleid}", skipcol=ExcludedCols)


        cmpresult=reffile.read() ==  datafile.read() # en cas d'ecart evite d'afficher un mega message d'erreur, plutot activer winmerge
        if not cmpresult: ShowOnWinmerge(reffile, datafile)
        assert cmpresult

def test_import_uvp5_BRU(app,caplog,tmpdir):
    caplog.set_level(logging.DEBUG)  # pour mise au point
    caplog.set_level(logging.CRITICAL) # pour execution très silencieuse
    part_project = dbpart.part_projects.query.filter_by(ptitle="EcoPart TU Project UVP 5 pour load BRU").first()
    part_project_ref = dbpart.part_projects.query.filter_by(ptitle="EcoPart TU Project UVP 2 Precomputed").first()
    if part_project is None:
        pytest.fail("BRU Project Missing")
    if part_project_ref is None:
        pytest.fail("BRU Ref Project Missing")
    with TaskInstance(app,"TaskPartZooscanImport", GetParams=f"p={part_project.pprojid}", PostParams={"new_1": "sample01","new_2": "sample02","new_3": "sample03","starttask": "Y"}) as T:
        print(f"TaskID={T.TaskID}")
        T.RunTask()
        ExcludedCols=[f'biovol{i:02d}' for i in range (1,46)] # Les biovolumes ne sont pas calculés dans le modèle.
        ExcludedCols.append('psampleid')
        ExcludedCols.append('datetime') # les projets UVP5 ne gèrent pas cette colonne historiquement.
        part_project = dbpart.part_projects.query.filter_by(ptitle="EcoPart TU Project UVP 5 pour load BRU").first()
        part_project_ref = dbpart.part_projects.query.filter_by(ptitle="EcoPart TU Project UVP 2 Precomputed").first()
        Sample1_ref=dbpart.part_samples.query.filter_by(pprojid=part_project_ref.pprojid,profileid="sample01").first()
        Sample1=dbpart.part_samples.query.filter_by(pprojid=part_project.pprojid,profileid="sample01").first()

        reffile=tmpdir.join("reffile.txt")
        datafile=tmpdir.join("datafile.txt")
        # TODO pouvoir transmettre un nom de fichier et pas forcement un file
        with open(reffile, "w") as fd:
            dump_table(fd, dbpart.part_histopart_reduit, f"psampleid={Sample1_ref.psampleid}", skipcol=ExcludedCols)
            dump_table(fd, dbpart.part_histopart_det, f"psampleid={Sample1_ref.psampleid}", skipcol=ExcludedCols)
        with open(datafile, "w") as fd:
            dump_table(fd, dbpart.part_histopart_reduit, f"psampleid={Sample1.psampleid}", skipcol=ExcludedCols)
            dump_table(fd, dbpart.part_histopart_det, f"psampleid={Sample1.psampleid}", skipcol=ExcludedCols)


        cmpresult=reffile.read() ==  datafile.read() # en cas d'ecart evite d'afficher un mega message d'erreur, plutot activer winmerge
        if not cmpresult: ShowOnWinmerge(reffile, datafile)
        assert cmpresult

