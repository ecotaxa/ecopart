import logging
import os
import subprocess

import pytest
import psycopg2.extras
from sqlalchemy import Table, text
from werkzeug.http import dump_cookie

import runtask
from part_app.app import db, part_app
from part_app.db_utils import GetAll
from part_app.remote import ECOTAXA_COOKIE, log_in_ecotaxa
from part_app.tasks import taskmanager

all_tokens = {}


def GetLastTaskID():
    return GetAll("select max(id) maxid from temp_tasks")[0]['maxid']


class TaskInstance:
    def __init__(self, app, ClassName, GetParams="", post_params=None, Login='admin'):
        if post_params is None:
            post_params = dict()
        self.app = part_app
        self.ClassName = ClassName
        self.GetParams = GetParams
        self.PostParams = post_params
        # Injection du token dans la request
        token = all_tokens[Login]
        header = dump_cookie(ECOTAXA_COOKIE, token)
        self.ctx = self.app.test_request_context(f"/Task/Create/{ClassName}?{GetParams}",
                                                 environ_base={'HTTP_COOKIE': header},
                                                 data=post_params)
        self.TaskID = None

    def __enter__(self):
        self.ctx.__enter__()
        previoustaskid = GetLastTaskID()
        self.app.PythonExecutable = "PYTESTDRIVEN"
        taskmanager.TaskCreateRouter(self.ClassName)
        self.TaskID = GetLastTaskID()
        if self.TaskID == previoustaskid:
            pytest.fail("Task Not correctly created")
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
    if os.name == 'nt':
        cmd = f'"C:\\Program Files\\WinMerge\\WinMergeU.exe" "{File1}" "{File2}"'
    else:
        cmd = f'"meld" "{File1}" "{File2}"'
    # print(cmd)
    subprocess.call(cmd, shell=True)


def zoo_login(user, password):
    token = log_in_ecotaxa(user, password)
    all_tokens[user] = token
    return token


def GetRow(sql, params=None, debug=False, cursor_factory=psycopg2.extras.DictCursor, doXSSEscape=False):
    res = GetAll(sql, params, debug, cursor_factory)
    if len(res) == 0:
        raise Exception("database.GetRow not enough rows on %s %s" % (sql, params))
    if len(res) > 1:
        raise Exception("database.GetRow too many rows on %s %s" % (sql, params))
    return res[0]
