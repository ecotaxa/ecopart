import logging
import os
import pytest
import re
import requests
from ftplib import FTP
from os.path import dirname, realpath
from pathlib import Path
from pytest_httpserver import HTTPServer
from pytest_localftpserver.plugin import PytestLocalFTPServer
from werkzeug.wrappers import Response
from Zoo_backend import BACKEND_PORT, kill_backend, launch_backend
from part_app import urls, app
from part_app.app import part_app, db, g
from part_app.database import part_projects, part_histopart_reduit, part_samples, part_histopart_det
from data_taxohisto import data_taxho_histo_sample1, data_taxho_histo_sampleT1
from part_app.db_utils import GetAssoc, ExecSQL
from part_app.funcs.uvp6remote_sample_import import RemoteServerFetcher
from utils import TaskInstance, dump_table, ShowOnWinmerge, zoo_login, GetRow

HERE = Path(dirname(realpath(__file__)))
DATA_DIR = (HERE / ".." / ".." / "data").resolve()

# Les tests supposent que les data à importer sont là, dans le répertoire "qa/data" qui est indiqué dans les projets
app.ServerLoadArea = (HERE / '../../..').resolve()


@pytest.fixture
def app():
    launch_backend()
    urls.BACKEND_API_PORT[0] = BACKEND_PORT
    token = zoo_login("admin", "nimda")
    assert token is not None
    with part_app.app_context():
        g.db = None
        yield part_app
        kill_backend()


def check_sampleTypeAkeyValues(psampleid, CompareBiovolumePart=True, CompareZoo=True, NbrImage=1, Coeff=1.0,
                               CompareBiovolumeZoo=True):
    """On teste des valeurs clés du sample, les # & BV des 2 premières classe et le watervolume"""
    sql = """select sum(watervolume) swatervolume,sum(class17) sclass17,sum(biovol17*watervolume) sbiovol17 
        ,sum(class18) sclass18 ,sum(biovol18*watervolume) sbiovol18
    from part_histopart_det t where psampleid=%s"""
    res = GetRow(sql, [psampleid])
    assert res['swatervolume'] == pytest.approx(339 * NbrImage)
    # le rel est utile pour les coeff 0.8 qui sur des valeur entières provoque des perte de particules entière
    # à la génération,donc tolérence de 1% dans ces cas là
    assert res['sclass17'] == pytest.approx(75150 * NbrImage * Coeff, rel=0.01 if Coeff != 1 else 0)
    assert res['sclass18'] == pytest.approx(20100 * NbrImage * Coeff, rel=0.01 if Coeff != 1 else 0)
    if CompareBiovolumePart:
        assert res['sbiovol17'] == pytest.approx(3.139335 * NbrImage * Coeff, rel=0.01 if Coeff != 1 else 1E-6)
        assert res['sbiovol18'] == pytest.approx(1.915367 * NbrImage * Coeff, rel=0.01 if Coeff != 1 else 1E-6)
    if CompareZoo:
        sql = """
        select  classif_id, sum(watervolume)  swatervolume, sum(nbr)  snbr , sum(totalbiovolume) stotalbiovolume
        from part_histocat  where psampleid=%s    group by classif_id"""
        res = GetAssoc(sql, [psampleid])
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


# noinspection DuplicatedCode
def check_ZooSample1(psampleid: int):
    dataraw = GetAssoc("""select concat(classif_id,'/',lineno) cle,depth,watervolume,nbr,avgesd,totalbiovolume
            from part_histocat
            where psampleid=(%s)""", [psampleid])
    data = {k: {c: v[c] for c in ('depth', 'watervolume', 'nbr', 'avgesd', 'totalbiovolume')} for k, v in
            dataraw.items()}
    # print(data) # pour génerer la variable ref
    ref = data_taxho_histo_sample1
    assert len(ref) == len(data)
    for k, r in ref.items():
        assert r['depth'] == pytest.approx(data[k]['depth'])
        assert r['watervolume'] == pytest.approx(data[k]['watervolume'])
        assert r['nbr'] == pytest.approx(data[k]['nbr'])
        assert r['avgesd'] == pytest.approx(data[k]['avgesd'])
        assert r['totalbiovolume'] == pytest.approx(data[k]['totalbiovolume'])


# noinspection DuplicatedCode
def check_ZooSampleT1(psampleid: int):
    dataraw = GetAssoc("""
            select concat(classif_id,'/',lineno) cle,depth,datetime,watervolume,nbr,avgesd,totalbiovolume
            from part_histocat
            where psampleid=(%s)""", [psampleid])
    data = {k: {c: v[c] for c in ('depth', 'datetime', 'watervolume', 'nbr', 'avgesd', 'totalbiovolume')} for k, v in
            dataraw.items()}
    # print(data) # pour génerer la variable ref
    ref = data_taxho_histo_sampleT1
    assert len(ref) == len(data)
    for k, r in ref.items():
        if r['depth'] is None:
            assert data[k]['depth'] is None
        else:
            assert r['depth'] == pytest.approx(data[k]['depth'])
        assert r['datetime'] == data[k]['datetime']
        assert r['watervolume'] == pytest.approx(data[k]['watervolume'])
        assert r['nbr'] == pytest.approx(data[k]['nbr'])
        assert r['avgesd'] == pytest.approx(data[k]['avgesd'])
        assert r['totalbiovolume'] == pytest.approx(data[k]['totalbiovolume'])


# def test_temp(app):
#     with app.app_context():  # Création d'un contexte pour utiliser les fonction GetAll,ExecSQL qui mémorisent
#         g.db = None
#         check_ZooSample1(573)
#         # check_ZooSampleT1(570)


def check_CtdValues(psampleid: int, ctdtype: int):
    sql = """select sum(chloro_fluo) schloro_fluo,sum(depth_salt_water) sdepth_salt_water
    from part_ctd t where psampleid=%s"""
    res = GetRow(sql, [psampleid])
    if ctdtype == 1:
        assert res['schloro_fluo'] == pytest.approx(59.02659)
        assert res['sdepth_salt_water'] == pytest.approx(125067.93)
    elif ctdtype == 2:
        assert res['schloro_fluo'] == pytest.approx(75.9722)
        assert res['sdepth_salt_water'] == pytest.approx(509406.79)
    else:
        pytest.fail(f"Invalid ctdtype:{ctdtype}")


# noinspection SqlResolve
def clean_existing_projectdata(pprojid: int):
    for tbl in ('part_histopart_reduit', 'part_histopart_det', 'part_histocat', 'part_histocat_lst',
                'part_histocat', 'part_ctd'):
        ExecSQL(f"""delete from {tbl} 
                        where psampleid in (select part_samples.psampleid 
                                            from part_samples 
                                            where pprojid={pprojid})""")
    ExecSQL(f"delete from part_samples where pprojid={pprojid}")


# noinspection DuplicatedCode
def test_import_uvp6_uvpapp(app, caplog, tmpdir):
    caplog.set_level(logging.DEBUG)  # pour mise au point
    caplog.set_level(logging.CRITICAL)  # pour execution très silencieuse
    part_project = db.session.query(part_projects).filter_by(
        ptitle="EcoPart TU Project UVP 6 from UVP APP").first()
    if part_project is None:
        pytest.fail("UVPAPP Project Missing")
    pprojid = part_project.pprojid
    clean_existing_projectdata(pprojid)
    with TaskInstance(app, "TaskPartZooscanImport", GetParams=f"p={part_project.pprojid}",
                      post_params={"new_1": "uvpappsample01", "new_2": "uvpappsample02", "new_3": "uvpappsample03",
                                   "new_4": "uvpappsampleT1", "new_5": "uvpappsampleT2", "new_6": "uvpappsampleT3",
                                   "starttask": "Y"}) as T:
        print(f"TaskID={T.TaskID}")
        T.RunTask()
        excluded_cols = [f'biovol{i:02d}' for i in range(1, 46)]  # Les biovolumes ne sont pas calculés dans le modèle.
        excluded_cols.append('psampleid')
        part_project_ref = db.session.query(part_projects).filter_by(
            ptitle="EcoPart TU Project UVP 2 Precomputed").first()
        if part_project_ref is None:
            pytest.fail("BRU Ref Project Missing")
        sample1_ref = db.session.query(part_samples).filter_by(pprojid=part_project_ref.pprojid,
                                                                      profileid="sample01").first()
        sample1 = db.session.query(part_samples).filter_by(pprojid=pprojid, profileid="uvpappsample01").first()
        sample_t1 = db.session.query(part_samples).filter_by(pprojid=pprojid, profileid="uvpappsampleT1").first()
        sample2 = db.session.query(part_samples).filter_by(pprojid=pprojid, profileid="uvpappsample02").first()
        sample_t2 = db.session.query(part_samples).filter_by(pprojid=pprojid, profileid="uvpappsampleT2").first()
        sample3 = db.session.query(part_samples).filter_by(pprojid=pprojid, profileid="uvpappsample03").first()
        sample_t3 = db.session.query(part_samples).filter_by(pprojid=pprojid, profileid="uvpappsampleT3").first()

        reffile = tmpdir.join("reffile.txt")
        datafile = tmpdir.join("datafile.txt")
        with open(reffile, "w") as fd:
            dump_table(fd, part_histopart_reduit, f"psampleid={sample1_ref.psampleid}", skipcol=excluded_cols)
            dump_table(fd, part_histopart_det, f"psampleid={sample1_ref.psampleid}", skipcol=excluded_cols)
        with open(datafile, "w") as fd:
            dump_table(fd, part_histopart_reduit, f"psampleid={sample1.psampleid}", skipcol=excluded_cols)
            dump_table(fd, part_histopart_det, f"psampleid={sample1.psampleid}", skipcol=excluded_cols)
        # en cas d'ecart evite d'afficher un mega message d'erreur, plutot activer winmerge
        cmpresult = reffile.read() == datafile.read()
        if not cmpresult:
            ShowOnWinmerge(reffile, datafile)
        assert cmpresult
        for sampleid in (sample1.psampleid, sample_t1.psampleid):
            check_sampleTypeAkeyValues(sampleid)
        for sampleid in (sample2.psampleid, sample_t2.psampleid):
            check_sampleTypeAkeyValues(sampleid, CompareZoo=False, NbrImage=2, Coeff=1.2)
        for sampleid in (sample3.psampleid, sample_t3.psampleid):
            check_sampleTypeAkeyValues(sampleid, CompareZoo=False, NbrImage=3, Coeff=0.8)
        check_CtdValues(sample2.psampleid, 1)
        check_CtdValues(sample3.psampleid, 2)
        check_ZooSample1(sample1.psampleid)
        check_ZooSampleT1(sample_t1.psampleid)


# noinspection DuplicatedCode
def test_import_uvp5_BRU(app, caplog, tmpdir):
    caplog.set_level(logging.DEBUG)  # pour mise au point
    caplog.set_level(logging.CRITICAL)  # pour execution très silencieuse
    part_project = db.session.query(part_projects).filter_by(
        ptitle="EcoPart TU Project UVP 5 pour load BRU").first()
    if part_project is None:
        pytest.fail("BRU Project Missing")
    pprojid = part_project.pprojid
    clean_existing_projectdata(pprojid)
    with TaskInstance(app, "TaskPartZooscanImport", GetParams=f"p={part_project.pprojid}",
                      post_params={"new_1": "brusample01", "new_2": "brusample02", "new_3": "brusample03",
                                   "starttask": "Y"}) as T:
        print(f"TaskID={T.TaskID}")
        T.RunTask()
        excluded_cols = [f'biovol{i:02d}' for i in range(1, 46)]  # Les biovolumes ne sont pas calculés dans le modèle.
        excluded_cols.append('psampleid')
        excluded_cols.append('datetime')  # les projets UVP5 ne gèrent pas cette colonne historiquement.
        part_project_ref = db.session.query(part_projects).filter_by(
            ptitle="EcoPart TU Project UVP 2 Precomputed").first()
        if part_project_ref is None:
            pytest.fail("BRU Ref Project Missing")
        sample1_ref = db.session.query(part_samples).filter_by(pprojid=part_project_ref.pprojid,
                                                                      profileid="sample01").first()
        sample1 = db.session.query(part_samples).filter_by(pprojid=pprojid, profileid="brusample01").first()

        reffile = tmpdir.join("reffile.txt")
        datafile = tmpdir.join("datafile.txt")
        with open(reffile, "w") as fd:
            dump_table(fd, part_histopart_reduit, f"psampleid={sample1_ref.psampleid}", skipcol=excluded_cols)
            dump_table(fd, part_histopart_det, f"psampleid={sample1_ref.psampleid}", skipcol=excluded_cols)
        with open(datafile, "w") as fd:
            dump_table(fd, part_histopart_reduit, f"psampleid={sample1.psampleid}", skipcol=excluded_cols)
            dump_table(fd, part_histopart_det, f"psampleid={sample1.psampleid}", skipcol=excluded_cols)
        # en cas d'ecart evite d'afficher un mega message d'erreur, plutot activer winmerge
        cmpresult = reffile.read() == datafile.read()
        if not cmpresult:
            ShowOnWinmerge(reffile, datafile)
        assert cmpresult
        check_sampleTypeAkeyValues(sample1.psampleid)
        sample2 = db.session.query(part_samples).filter_by(pprojid=pprojid, profileid="brusample02").first()
        sample3 = db.session.query(part_samples).filter_by(pprojid=pprojid, profileid="brusample03").first()
        check_CtdValues(sample2.psampleid, 1)
        check_CtdValues(sample3.psampleid, 2)
        check_ZooSample1(sample1.psampleid)


# noinspection DuplicatedCode
def test_import_uvp5_BRU1(app, caplog, tmpdir):
    caplog.set_level(logging.DEBUG)  # pour mise au point
    caplog.set_level(logging.CRITICAL)  # pour execution très silencieuse
    part_project = db.session.query(part_projects).filter_by(
        ptitle="EcoPart TU Project UVP 5 pour load BRU1").first()
    if part_project is None:
        pytest.fail("BRU1 Project Missing")
    pprojid = part_project.pprojid
    clean_existing_projectdata(pprojid)
    with TaskInstance(app, "TaskPartZooscanImport", GetParams=f"p={part_project.pprojid}",
                      post_params={"new_1": "bru1sample01", "new_2": "bru1sample02", "new_3": "bru1sample03",
                                   "starttask": "Y"}) as T:
        print(f"TaskID={T.TaskID}")
        T.RunTask()
        excluded_cols = [f'biovol{i:02d}' for i in range(1, 46)]  # Les biovolumes ne sont pas calculés dans le modèle.
        excluded_cols.append('psampleid')
        excluded_cols.append('datetime')  # les projets UVP5 ne gèrent pas cette colonne historiquement.
        part_project_ref = db.session.query(part_projects).filter_by(
            ptitle="EcoPart TU Project UVP 2 Precomputed").first()
        if part_project_ref is None:
            pytest.fail("BRU Ref Project Missing")
        sample1_ref = db.session.query(part_samples).filter_by(pprojid=part_project_ref.pprojid,
                                                                      profileid="sample01").first()
        sample1 = db.session.query(part_samples).filter_by(pprojid=pprojid, profileid="bru1sample01").first()

        reffile = tmpdir.join("reffile.txt")
        datafile = tmpdir.join("datafile.txt")
        with open(reffile, "w") as fd:
            dump_table(fd, part_histopart_reduit, f"psampleid={sample1_ref.psampleid}", skipcol=excluded_cols)
            dump_table(fd, part_histopart_det, f"psampleid={sample1_ref.psampleid}", skipcol=excluded_cols)
        with open(datafile, "w") as fd:
            dump_table(fd, part_histopart_reduit, f"psampleid={sample1.psampleid}", skipcol=excluded_cols)
            dump_table(fd, part_histopart_det, f"psampleid={sample1.psampleid}", skipcol=excluded_cols)
        # en cas d'ecart evite d'afficher un mega message d'erreur, plutot activer winmerge
        cmpresult = reffile.read() == datafile.read()
        if not cmpresult:
            ShowOnWinmerge(reffile, datafile)
        assert cmpresult
        check_sampleTypeAkeyValues(sample1.psampleid)
        sample2 = db.session.query(part_samples).filter_by(pprojid=pprojid, profileid="bru1sample02").first()
        sample3 = db.session.query(part_samples).filter_by(pprojid=pprojid, profileid="bru1sample03").first()
        check_CtdValues(sample2.psampleid, 1)
        check_CtdValues(sample3.psampleid, 2)
        check_ZooSample1(sample1.psampleid)


# noinspection DuplicatedCode
def test_import_lisst(app, caplog, tmpdir):
    caplog.set_level(logging.DEBUG)  # pour mise au point
    caplog.set_level(logging.CRITICAL)  # pour execution très silencieuse
    part_project = db.session.query(part_projects).filter_by(ptitle="EcoPart TU Project LISST").first()
    if part_project is None:
        pytest.fail("LISST Project Missing")
    pprojid = part_project.pprojid
    clean_existing_projectdata(pprojid)
    with TaskInstance(app, "TaskPartZooscanImport", GetParams=f"p={part_project.pprojid}",
                      # on importe pas les temporels car ils ne sont pas correctement traités
                      post_params={"new_1": "lisstsample01", "new_2": "lisstsample02", "new_3": "lisstsample03",
                                   "starttask": "Y"}) as T:
        print(f"TaskID={T.TaskID}")
        T.RunTask()
        sample1 = db.session.query(part_samples).filter_by(pprojid=pprojid, profileid="lisstsample01").first()
        # On controle le total biovolume avec quelques PB
        #  sur le lisst on a pas les watervolume associés on fait donc la some des concentrations (qui dans l'abosolu
        #  n'as pas de sens puisqu'il y a le même nombre de ligne dans l'histograme
        # les classe du LISST ne sont pas les même il y a des mécanisme de ventilation proportionnelle dans les classe
        # EcoPart il faut donc regrouper certaines classes pour les comparer avec un import UVP
        sql = """select sum(biovol17) biovol17raw
                        ,sum(biovol18+biovol19+biovol20) biovol18_20raw
                        ,sum(biovol22) biovol22raw
                        ,sum(biovol23+biovol24) biovol2324raw        
        from part_histopart_det t where psampleid=%s"""
        res = GetRow(sql, [sample1.psampleid])
        assert res['biovol17raw'] == pytest.approx(2.7781733)
        assert res['biovol18_20raw'] == pytest.approx(2.2831353)
        assert res['biovol22raw'] == pytest.approx(3.1642698)
        assert res['biovol2324raw'] == pytest.approx(39.27267)
        sample2 = db.session.query(part_samples).filter_by(pprojid=pprojid, profileid="lisstsample02").first()
        sample3 = db.session.query(part_samples).filter_by(pprojid=pprojid, profileid="lisstsample03").first()
        check_CtdValues(sample2.psampleid, 1)
        check_CtdValues(sample3.psampleid, 2)


# @pytest.fixture
# def httpserver_listen_address():
#     return "127.0.0.1", 5050


def HttpServeurStaticHandler(req) -> Response:
    if req.path.endswith('/'):
        directory = DATA_DIR / req.path[1:-1]
        result = ""
        for fichier in directory.glob("*"):
            result += f"<a href='{fichier.name}'>{fichier.name}</a><br>"
            # print(fichier.name)
        return Response(result)
    fichier = DATA_DIR / req.path[1:]
    return Response(fichier.read_text())


# noinspection DuplicatedCode
def test_import_uvp_remote_lambda_http(app, caplog, tmpdir, httpserver: HTTPServer):
    caplog.set_level(logging.DEBUG)  # pour mise au point
    caplog.set_level(logging.CRITICAL)  # pour execution très silencieuse
    part_project = db.session.query(part_projects).filter_by(
        ptitle="EcoPart TU Project UVP Remote Lambda HTTP").first()
    if part_project is None:
        pytest.fail("UVPAPP Project Missing")
    pprojid = part_project.pprojid
    clean_existing_projectdata(pprojid)
    httpserver.expect_request("/TestDuServeurHTTP/").respond_with_data("OK permanent")
    httpserver.expect_request(re.compile("^/")).respond_with_handler(HttpServeurStaticHandler)
    # test des fonction qui emulent le serveur HTTP
    assert requests.get("http://localhost:5050/TestDuServeurHTTP/").text == "OK permanent"
    assert requests.get("http://localhost:5050/tu1_uvp6remotelambda/").text.startswith("<a")
    assert requests.get("http://localhost:5050/tu1_uvp6remotelambda/lambdasample01_UVPSN_DEPTH_BLACK.txt") \
        .text.startswith("DATE_TIME\t")
    # print(httpserver.url_for("/tu1_uvp6remotelambda/"))

    rsf = RemoteServerFetcher(pprojid)
    samples = rsf.GetServerFiles()
    # print(Samples)
    assert 'lambdasample01' in samples  # test de la récupération de la liste des fichiers
    assert len(samples) == 6
    # return

    with TaskInstance(app, "TaskPartZooscanImport", GetParams=f"p={part_project.pprojid}",
                      post_params={"starttask": "Y"}) as T:
        print(f"TaskID={T.TaskID}")
        T.RunTask()
        excluded_cols = [f'biovol{i:02d}' for i in range(1, 46)]  # Les biovolumes ne sont pas calculés dans le modèle.
        excluded_cols.append('psampleid')
        excluded_cols.extend([f'class{i:02d}' for i in range(1, 17)])
        excluded_cols.extend([f'class{i:02d}' for i in range(35, 46)])
        part_project_ref = db.session.query(part_projects).filter_by(
            ptitle="EcoPart TU Project UVP 2 Precomputed").first()
        if part_project_ref is None:
            pytest.fail("BRU Ref Project Missing")
        sample1_ref = db.session.query(part_samples).filter_by(pprojid=part_project_ref.pprojid,
                                                                      profileid="sample01").first()
        sample1 = db.session.query(part_samples).filter_by(pprojid=pprojid, profileid="lambdasample01").first()
        sample_t1 = db.session.query(part_samples).filter_by(pprojid=pprojid, profileid="lambdasampleT1").first()
        sample2 = db.session.query(part_samples).filter_by(pprojid=pprojid, profileid="lambdasample02").first()
        sample_t2 = db.session.query(part_samples).filter_by(pprojid=pprojid, profileid="lambdasampleT2").first()
        sample3 = db.session.query(part_samples).filter_by(pprojid=pprojid, profileid="lambdasample03").first()
        sample_t3 = db.session.query(part_samples).filter_by(pprojid=pprojid, profileid="lambdasampleT3").first()

        reffile = tmpdir.join("reffile.txt")
        datafile = tmpdir.join("datafile.txt")
        with open(reffile, "w") as fd:
            dump_table(fd, part_histopart_reduit, f"psampleid={sample1_ref.psampleid}", skipcol=excluded_cols)
            dump_table(fd, part_histopart_det, f"psampleid={sample1_ref.psampleid}", skipcol=excluded_cols)
        with open(datafile, "w") as fd:
            dump_table(fd, part_histopart_reduit, f"psampleid={sample1.psampleid}", skipcol=excluded_cols)
            dump_table(fd, part_histopart_det, f"psampleid={sample1.psampleid}", skipcol=excluded_cols)
        # en cas d'ecart evite d'afficher un mega message d'erreur, plutot activer winmerge
        cmpresult = reffile.read() == datafile.read()
        if not cmpresult:
            ShowOnWinmerge(reffile, datafile)
        assert cmpresult
        for sampleid in (sample1.psampleid, sample_t1.psampleid):
            check_sampleTypeAkeyValues(sampleid, CompareBiovolumePart=False, CompareBiovolumeZoo=False)
        for sampleid in (sample2.psampleid, sample_t2.psampleid):
            check_sampleTypeAkeyValues(sampleid, CompareBiovolumePart=False, CompareZoo=False, NbrImage=2, Coeff=1.2)
        for sampleid in (sample3.psampleid, sample_t3.psampleid):
            check_sampleTypeAkeyValues(sampleid, CompareBiovolumePart=False, CompareZoo=False, NbrImage=3, Coeff=0.8)


os.environ["FTP_USER"] = "MyUser"
os.environ["FTP_PASS"] = "MyPassword"
os.environ["FTP_PORT"] = "21"
os.environ["FTP_HOME"] = DATA_DIR.as_posix()


# noinspection DuplicatedCode
def test_import_uvp_remote_lambda_ftp(app, caplog, tmpdir, ftpserver: PytestLocalFTPServer):
    assert isinstance(ftpserver, PytestLocalFTPServer)
    assert ftpserver.uses_TLS is False
    # print(ftpserver.anon_root)
    # print(ftpserver.get_login_data())
    # test du bon fonctionnement du serveur FTP
    ftp = FTP()
    ftp.connect("127.0.0.1")
    ftp.login("MyUser", "MyPassword")
    ftp.cwd('tu1_uvp6remotelambda')
    lstfichiers = ftp.nlst()
    # print(lstfichiers)
    assert "lambdasample01_UVPSN_DEPTH_BLACK.txt" in lstfichiers
    ftp.close()
    # return

    # Test de la fonction Remote FTP, l'ensemble des test est commun à la version FTP, seule la récupératind des
    # fichiers est différente
    caplog.set_level(logging.DEBUG)  # pour mise au point
    caplog.set_level(logging.CRITICAL)  # pour execution très silencieuse
    part_project = db.session.query(part_projects).filter_by(
        ptitle="EcoPart TU Project UVP Remote Lambda FTP").first()
    if part_project is None:
        pytest.fail("UVPAPP Project Missing")
    pprojid = part_project.pprojid
    clean_existing_projectdata(pprojid)
    rsf = RemoteServerFetcher(pprojid)
    samples = rsf.GetServerFiles()
    # print(Samples)
    assert 'lambdasample01' in samples  # test de la récupération de la liste des fichiers
    assert len(samples) == 6
    # return

    with TaskInstance(app, "TaskPartZooscanImport", GetParams=f"p={part_project.pprojid}",
                      post_params={"starttask": "Y"}) as T:
        print(f"TaskID={T.TaskID}")
        T.RunTask()
        excluded_cols = [f'biovol{i:02d}' for i in range(1, 46)]  # Les biovolumes ne sont pas calculés dans le modèle.
        excluded_cols.append('psampleid')
        excluded_cols.extend([f'class{i:02d}' for i in range(1, 17)])
        excluded_cols.extend([f'class{i:02d}' for i in range(35, 46)])
        part_project_ref = db.session.query(part_projects).filter_by(
            ptitle="EcoPart TU Project UVP 2 Precomputed").first()
        if part_project_ref is None:
            pytest.fail("BRU Ref Project Missing")
        sample1_ref = db.session.query(part_samples).filter_by(pprojid=part_project_ref.pprojid,
                                                                      profileid="sample01").first()
        sample1 = db.session.query(part_samples).filter_by(pprojid=pprojid, profileid="lambdasample01").first()
        sample_t1 = db.session.query(part_samples).filter_by(pprojid=pprojid, profileid="lambdasampleT1").first()
        sample2 = db.session.query(part_samples).filter_by(pprojid=pprojid, profileid="lambdasample02").first()
        sample_t2 = db.session.query(part_samples).filter_by(pprojid=pprojid, profileid="lambdasampleT2").first()
        sample3 = db.session.query(part_samples).filter_by(pprojid=pprojid, profileid="lambdasample03").first()
        sample_t3 = db.session.query(part_samples).filter_by(pprojid=pprojid, profileid="lambdasampleT3").first()

        reffile = tmpdir.join("reffile.txt")
        datafile = tmpdir.join("datafile.txt")
        with open(reffile, "w") as fd:
            dump_table(fd, part_histopart_reduit, f"psampleid={sample1_ref.psampleid}", skipcol=excluded_cols)
            dump_table(fd, part_histopart_det, f"psampleid={sample1_ref.psampleid}", skipcol=excluded_cols)
        with open(datafile, "w") as fd:
            dump_table(fd, part_histopart_reduit, f"psampleid={sample1.psampleid}", skipcol=excluded_cols)
            dump_table(fd, part_histopart_det, f"psampleid={sample1.psampleid}", skipcol=excluded_cols)
        # en cas d'ecart evite d'afficher un mega message d'erreur, plutot activer winmerge
        cmpresult = reffile.read() == datafile.read()
        if not cmpresult:
            ShowOnWinmerge(reffile, datafile)
        assert cmpresult
        for sampleid in (sample1.psampleid, sample_t1.psampleid):
            check_sampleTypeAkeyValues(sampleid, CompareBiovolumePart=False, CompareBiovolumeZoo=False)
        for sampleid in (sample2.psampleid, sample_t2.psampleid):
            check_sampleTypeAkeyValues(sampleid, CompareBiovolumePart=False, CompareZoo=False, NbrImage=2, Coeff=1.2)
        for sampleid in (sample3.psampleid, sample_t3.psampleid):
            check_sampleTypeAkeyValues(sampleid, CompareBiovolumePart=False, CompareZoo=False, NbrImage=3, Coeff=0.8)
