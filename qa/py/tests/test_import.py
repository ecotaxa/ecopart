from os.path import dirname, realpath,join
from pathlib import Path
from appli import database,app,g,db,gvp,gvg,request
from appli.tasks import taskmanager
#from pytest_mock import mocker
import pytest,logging
import unittest.mock
from appli import appli
from flask_login import current_user,login_user

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

def test_import_uvp6_uvpapp(app,capsys,caplog):
    caplog.set_level(logging.DEBUG)  # pour mise au point
    caplog.set_level(logging.CRITICAL) # pour execution très silencieuse
    with TaskInstance(app,"TaskPartZooscanImport", GetParams="p=5", PostParams={"new_1": "sample01","new_2": "sample02","new_3": "sample03","starttask": "Y"}) as T:
        # print("TaskID={T.TaskID}")
        T.RunTask()
