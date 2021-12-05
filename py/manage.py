#
# EcoPart manage application
#
import os
import shutil
import sys

from flask import g
from flask_script import Manager

import part_app
import part_app.database as partdatabase
import part_app.funcs.common_sample_import as common_import
import part_app.funcs.histograms
import part_app.funcs.uvp6remote_sample_import as uvp6remote_sample_import
import part_app.views.prj as prj
from part_app.app import part_app, db
from part_app import db_utils
from part_app.db_utils import ExecSQL
from part_app.funcs.histograms import ComputeHistoDet, ComputeHistoRed, ComputeZooHisto
from part_app.remote import EcoTaxaInstance, log_in_ecotaxa

manager = Manager(part_app)


@manager.command
def dbdrop():
    db.drop_all()


@manager.command
def dbcreate():
    with part_app.app_context():  # Création d'un contexte pour utiliser les fonction GetAll,ExecSQL qui mémorisent
        g.db = None
        db.create_all()
        # from flask_migrate import stamp
        # stamp(revision='head')
        ExecSQL("""create view objects as select oh.*,ofi.*
        from obj_head oh left join obj_field ofi on oh.objid=ofi.objfid""")


@manager.command
def ResetDBSequence(cur=None):
    with part_app.app_context():  # Création d'un contexte pour utiliser les fonction GetAll,ExecSQL qui mémorisent
        g.db = None
        print("Start Sequence Reset")
        if cur is None:
            cur = db.session
        cur.execute("SELECT setval('seq_temp_tasks', (SELECT max(id) FROM temp_tasks), true)")
        cur.execute("SELECT setval('part_projects_pprojid_seq', (SELECT max(pprojid) FROM part_projects), true)")
        cur.execute("SELECT setval('part_samples_psampleid_seq', (SELECT max(psampleid) FROM part_samples), true)")
        print("Sequence Reset Done")


@manager.option('-u', '--UseExistingDatabase', dest='UseExistingDatabase', default=False,
                help="UseExistingDatabase True/False")
@manager.option('-s', '--SkipConfirmation', dest='SkipConfirmation', default=False,
                help="Skip remove confirmation True/False")
def CreateDB(UseExistingDatabase=False, SkipConfirmation=False):
    with part_app.app_context():  # Création d'un contexte pour utiliser les fonction GetAll,ExecSQL qui mémorisent
        g.db = None
        if UseExistingDatabase:
            print("You have specified the UseExistingDatabase option, "
                  "the database itself will be kept, but all its content will be removed")
        if not SkipConfirmation:
            if input("This operation will create a new empty DB.\n"
                     " If a database exists, it will DESTROY all existing data of the existing database.\n"
                     "Are you SURE ? Confirm by Y !").lower() != "y":
                print("Import Aborted !!!")
                exit()

        print("Configuration is Database:", part_app.config['DB_DATABASE'])
        print("Login: ", part_app.config['DB_USER'], "/", part_app.config['DB_PASSWORD'])
        print("Host: ", part_app.config['DB_HOST'])
        print("Port: ", part_app.config['DB_PORT'])
        import psycopg2

        if os.path.exists("vault"):
            print("Drop existing images")
            shutil.rmtree("vault")
            os.mkdir("vault")

        print("Connect Database")
        if UseExistingDatabase:
            conn = psycopg2.connect(user=part_app.config['DB_USER'], password=part_app.config['DB_PASSWORD'],
                                    host=part_app.config['DB_HOST'], port=part_app.config['DB_PORT'],
                                    database=part_app.config['DB_DATABASE'])
        else:
            # On se loggue en postgres pour dropper/creer les bases qui doit être déclaré trust dans hba_conf
            conn = psycopg2.connect(user='postgres', host=part_app.config['DB_HOST'], port=part_app.config['DB_PORT'])
        cur = conn.cursor()

        conn.set_session(autocommit=True)
        if UseExistingDatabase:
            print("Drop the existing public schema")
            sql = "DROP SCHEMA public cascade"
        else:
            print("Drop the existing database")
            sql = "DROP DATABASE IF EXISTS " + part_app.config['DB_DATABASE']
        cur.execute(sql)

        if UseExistingDatabase:
            print("Create the public schema")
            sql = "create schema public AUTHORIZATION " + part_app.config['DB_USER']
        else:
            print("Create the new database")
            sql = "create DATABASE " + part_app.config['DB_DATABASE'] + " WITH ENCODING='UTF8'  OWNER=" + \
                  part_app.config['DB_USER'] + \
                  " TEMPLATE=template0 LC_CTYPE='C' LC_COLLATE='C' CONNECTION LIMIT=-1 "
        cur.execute(sql)

        print("Create the Schema")
        dbcreate()
        print("Creation Done")


@manager.option('-p', '--projectid', dest='ProjectID', type=int, default=None, required=True,
                help="Particle project ID")
@manager.option('-w', '--what', dest='What', default=None, required=True,
                help="""What should be recomputed, a set of letter i.e : DRMTC
D : Compute detailed histogram 
R : Compute Reduced histogram
M : Match Ecotaxa sample
T : Compute taxonomy histogram
C : CTD import""")
@manager.option('-u', '--user', dest='User', default=None, help="User Name for CTD Import")
@manager.option('-e', '--email', dest='Email', default=None, help="Email for CTD Import")
@manager.option('-xu', '--ecotaxa-user', dest='ecotaxa_user', help="EcoTaxa username")
@manager.option('-xp', '--ecotaxa-pass', dest='ecotaxa_password', help="EcoTaxa password")
def RecomputePart(ProjectID, What, User, Email, ecotaxa_user, ecotaxa_password):
    cookie = log_in_ecotaxa(ecotaxa_user, ecotaxa_password)
    if cookie is None:
        print("EcoTaxa login failed")
        quit(-1)
    ecotaxa_if = EcoTaxaInstance(cookie)
    if 'C' in What:
        if User is None or Email is None:
            print("-u and -e options are required for CTD import")
            quit(-1)
    with part_app.app_context():  # Création d'un contexte pour utiliser les fonction GetAll,ExecSQL qui mémorisent
        g.db = None
        Prj = partdatabase.part_projects.query.filter_by(pprojid=ProjectID).first()
        Samples = db_utils.GetAll("select psampleid,profileid from part_samples where pprojid=(%s)", [ProjectID])
        for S in Samples:
            print("Processing particle sample %s:%s" % (S['psampleid'], S['profileid']))
            if 'D' in What:
                print("Det=", ComputeHistoDet(S['psampleid'], Prj.instrumtype))
            if 'R' in What:
                print("Red=", ComputeHistoRed(S['psampleid'], Prj.instrumtype))
            if 'M' in What:
                print("Match=", prj.ComputeZooMatch(ecotaxa_if, S['psampleid'], Prj.projid))
            if 'C' in What:
                print("CTD=", "Imported" if common_import.ImportCTD(S['psampleid'], User, Email) else 'CTD No file')
        Samples = db_utils.GetAll("select psampleid,profileid,sampleid from part_samples where pprojid=(%s)",
                                  [ProjectID])
        for S in Samples:
            if 'T' in What and S['sampleid']:
                print("Zoo for particle sample %s:%s=" % (S['psampleid'], S['profileid']),
                      ComputeZooHisto(ecotaxa_if, S['psampleid'], Prj.instrumtype))


@manager.command
def partpoolserver():
    with part_app.app_context():  # Création d'un contexte pour utiliser les fonction GetAll,ExecSQL qui mémorisent
        g.db = None
        Lst = db_utils.GetAll(
            """select pprojid,ptitle from part_projects where coalesce(remote_type,'')!='' and coalesce(remote_url,'')!='' """)
        for P in Lst:
            print("pollserver for project {pprojid} : {ptitle}".format(**P))
            try:
                RSF = uvp6remote_sample_import.RemoteServerFetcher(P['pprojid'])
                LstSampleID = RSF.FetchServerDataForProject([])
                if not LstSampleID:
                    continue
                for psampleid in LstSampleID:
                    print("uvp6remote Sample %d Metadata processed, Détailled histogram in progress" % (psampleid,))
                    uvp6remote_sample_import.GenerateParticleHistogram(psampleid)
                    print("Try to import CTD")
                    print(common_import.ImportCTD(psampleid, "Automatic", ""))
            except:
                print('Error : ' + str(sys.exc_info()))


if __name__ == "__main__":
    manager.run()
