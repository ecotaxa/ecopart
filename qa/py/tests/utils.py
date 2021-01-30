import pytest
import runtask
from flask_login import login_user
from appli.tasks import taskmanager
from appli import database, db
import logging
from sqlalchemy import Table, text
import subprocess

# Loggue un user, mais doit être fait après la création du contexte de test
def LogUser(email):
    login_user(db.session.query(database.users).filter_by(email=email).first())


def GetLastTaskID():
    return database.GetAll("select max(id) maxid from temp_tasks")[0]['maxid']


class TaskInstance:
    def __init__(self, app, ClassName, GetParams="", post_params=None, Login='admin'):
        if post_params is None:
            post_params = dict()
        self.app = app
        self.ClassName = ClassName
        self.GetParams = GetParams
        self.PostParams = post_params
        self.Login = Login
        self.ctx = app.test_request_context(f"/Task/Create/{ClassName}?{GetParams}",
                                            data=post_params)
        self.TaskID = None

    def __enter__(self):
        self.ctx.__enter__()
        previoustaskid = GetLastTaskID()
        LogUser(self.Login)
        self.app.PythonExecutable = "PYTESTDRIVEN"
        taskmanager.TaskCreateRouter(self.ClassName)
        self.TaskID = GetLastTaskID()
        if self.TaskID == previoustaskid:
            pytest.fail("Taks Not correctly created")
        return self

    def RunTask(self):
        runtask.RunTask(self.TaskID, LogLevel=logging.getLogger().level)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ctx.__exit__(exc_type, exc_val, exc_tb)

    def LoadTask(self):
        return taskmanager.LoadTask(self.TaskID)

# noinspection DuplicatedCode
def dump_table(out, a_table: db.Model, where, skipcol=()):
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

def ShowOnWinmerge(File1, File2):
    cmd = f'"C:\\Program Files\\WinMerge\\WinMergeU.exe" "{File1}" "{File2}"'
    # print(cmd)
    subprocess.call(cmd)
