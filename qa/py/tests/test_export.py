import bz2
import shutil
# noinspection PyUnresolvedReferences
import warnings
import logging
import os
import pytest
import re
import math
from os.path import dirname, realpath
from pathlib import Path

from Zoo_backend import BACKEND_PORT, kill_backend, launch_backend
from part_app import urls, app
from part_app.app import part_app, db, g
from part_app.database import part_projects
from utils import TaskInstance, ShowOnUIDiffApp, zoo_login
import zipfile

HERE = Path(dirname(realpath(__file__)))
DATA_DIR = (HERE / ".." / ".." / "data").resolve()
REF_EXPORT_DIR = (DATA_DIR / "ref_export")

# Les tests supposent que les data à importer sont là, dans le répertoire "qa/data" qui est indiqué dans les projets
app.ServerLoadArea = (HERE / '../../..').resolve()
app.VaultRootDir = (HERE / '../../vault').resolve()


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


@pytest.fixture
def part_project_uvpapp():
    part_project = db.session.query(part_projects).filter_by(
        ptitle="EcoPart TU Project UVP 6 from UVP APP").first()
    if part_project is None:
        pytest.fail("UVPAPP Project Missing")
    return part_project


@pytest.fixture
def part_project_uvpbru():
    part_project = db.session.query(part_projects).filter_by(
        ptitle="EcoPart TU Project UVP 5 pour load BRU").first()
    if part_project is None:
        pytest.fail("UVP BRU Project Missing")
    return part_project


@pytest.fixture
def part_project_uvpremotelambdahttp():
    part_project = db.session.query(part_projects).filter_by(
        ptitle="EcoPart TU Project UVP Remote Lambda HTTP").first()
    if part_project is None:
        pytest.fail("UVP remote lambda HTTP Project Missing")
    return part_project


def SupprimeDateTime(nomfichier):
    redatetime = re.compile(r"_\d+_\d{2}_\d{2}")
    return redatetime.sub("", nomfichier)


def SupprimeDateTimeRB(nomfichier):
    redatetime = re.compile(rb"_\d+_\d{2}_\d{2}")
    return redatetime.sub(rb"", nomfichier)


# Utile pour le timestamp du dernier recalcul histogramme taxo dans le summary
def SupprimeTimestampRB(texte):
    redatetime = re.compile(rb"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+")
    return redatetime.sub(rb"", texte)


def SupprimeCreateTime(data):
    recreatetime = re.compile(rb"<CreateTime>[^<]+</CreateTime>")
    return recreatetime.sub(rb"", data)


def SupprimerColFromTSV(data: bytes, colname: bytes):
    lignes = data.split(b'\n')
    colindex = -1
    for i, l in enumerate(lignes):
        cols = l.split(b'\t')
        if i == 0:
            if colname in cols:
                colindex = cols.index(colname)
        elif colindex >= 0 and len(cols) > colindex:
            cols[colindex] = b""
        lignes[i] = b'\t'.join(cols)
    return b'\n'.join(lignes)


def checkCompareTSVorODV(data_ref, data_gen, separator_regex=b'\t|;'):
    """
        Comparaison entre deux jeux de données, TSV ou ODV.
    """
    lignes_r = data_ref.split(b'\n')
    lignes_g = data_gen.split(b'\n')
    if len(lignes_r) != len(lignes_g):
        return ["%d lignes en ref, %d en gen" % (len(lignes_r), len(lignes_g))]
    problems = []
    line_num = 1
    for (row_r, row_g) in zip(lignes_r, lignes_g):
        cols_r = re.split(separator_regex, row_r)
        cols_g = re.split(separator_regex, row_g)
        if len(cols_r) != len(cols_g):
            problems.append("lne %d : %d colonnes en ref, %d en gen" % (line_num, len(cols_r), len(cols_g)))
        else:
            lasts = (False,)*(len(cols_r)-1)+(True,)
            for (col_r, col_g, last) in zip(cols_r, cols_g, lasts):
                try:
                    float_r, float_g = (float(col_r), float(col_g))
                    if not math.isclose(float_r, float_g):
                        problems.append("lne %d : flt %s (ref) <> %s (gen)" % (line_num, col_r, col_g))
                except ValueError:
                    # pas des chiffres, on compare l'égalité des texte
                    if last:
                        # La 'ref' (dans qa/data) a été générée sous Windows, auquel cas les lignes se finissent par \r\n, et pas la 'gen'
                        # _mais_ quelquefois, la 'gen' aussi finit par '\r\n', car les fichiers proviennent du vault où ils ont
                        # simplement été copiés.
                        col_r = col_r.rstrip()
                        col_g = col_g.rstrip()
                    if col_r != col_g:
                        if b'\xc2' not in col_g:
                            problems.append("lne %d : txt %s (ref) <> %s (gen)" % (line_num, col_r, col_g))
        line_num += 1
        if len(problems) > 100:
            problems.append("Arrêt après 100")
            break
    return problems


def isBZ2(file: Path) -> bool:
    if file.exists():
        with file.open('rb') as f:
            if f.read(2) == b'BZ':
                return True
    return False


def extractZipOrBz2(filename: Path, targetdir: Path):
    if isBZ2(filename):
        with bz2.open(filename) as rf, open(targetdir / filename.name[:-4], "wb") as rawtargetfile:
            shutil.copyfileobj(rf, rawtargetfile)
    else:
        with zipfile.ZipFile(filename, 'r') as z:
            z.extractall(targetdir)


def check_compare_zip(refzip: Path, resultzip: Path, tmpdir: str, dirsuffix: str):
    tmpdir_path = Path(tmpdir)
    tmpdir_path_ref = tmpdir_path / (dirsuffix + "ref")
    if tmpdir_path_ref.exists():
        shutil.rmtree(tmpdir_path_ref.as_posix())
    tmpdir_path_ref.mkdir()
    tmpdir_path_result = tmpdir_path / (dirsuffix + "result")
    if tmpdir_path_result.exists():
        shutil.rmtree(tmpdir_path_result.as_posix())
    tmpdir_path_result.mkdir()
    extractZipOrBz2(refzip, tmpdir_path_ref)
    extractZipOrBz2(resultzip, tmpdir_path_result)
    # with zipfile.ZipFile(refzip, 'r') as z:
    #     z.extractall(tmpdir_path_ref.as_posix())
    # with zipfile.ZipFile(resultzip, 'r') as z:
    #     z.extractall(tmpdir_path_result.as_posix())
    liste_fichier_ref = {SupprimeDateTime(f.name): f.name for f in tmpdir_path_ref.glob('*')}
    liste_fichier_result = {SupprimeDateTime(f.name): f.name for f in tmpdir_path_result.glob('*')}
    assert len(liste_fichier_ref) >= len(liste_fichier_result), \
        "Nombre de fichier qui ne correspond pas entre la ref et le result"
    for nomfichier, nomfichierfull in liste_fichier_result.items():
        assert (nomfichier in liste_fichier_ref), f"Fichier {nomfichier} dans le resultat seulement"
        ref_filename = tmpdir_path_ref / liste_fichier_result[nomfichier]
        with open(ref_filename, "rb") as fref:
            data_ref = SupprimeCreateTime(fref.read())
        result_filename = tmpdir_path_result / nomfichierfull
        with open(tmpdir_path_result / nomfichierfull, "rb") as fresult:
            data_result = SupprimeCreateTime(fresult.read())
        cmpresult = checkCompareTSVorODV(data_ref, data_result)
        if len(cmpresult) > 0:
            ShowOnUIDiffApp(ref_filename, result_filename)
        assert cmpresult == []


def check_zip_with_ref(refdirname: str, task, tmpfilename: str, FTPExportAreaFolter: Path = None):
    """
        Vérification d'un zip produit par l'export, en utilisant une référence.
    """
    ref_dir = REF_EXPORT_DIR / refdirname
    liste_fichier_ref = {SupprimeDateTime(f.name): f.name for f in ref_dir.glob('*')}
    # print(liste_fichier_ref)
    if FTPExportAreaFolter:
        # On a pas l'information du nom de fichier mais il est de la forme task_xx_
        target_file_prefix = "task_%d_" % task.task.id
        nom_fichier_zip = "Fichier manquant dans FTP export area"
        for f in FTPExportAreaFolter.glob(target_file_prefix + "*"):
            nom_fichier_zip = f
    else:
        nom_fichier_zip = os.path.join(task.GetWorkingDir(), task.GetResultFile())
    with zipfile.ZipFile(nom_fichier_zip, 'r') as z:
        liste_fichier_zip = z.namelist()
        # Comparaison des noms de fichiers avant de comparer leur contenu
        ref_fichiers = set(liste_fichier_ref)
        actu_fichiers = set([SupprimeDateTime(f) for f in liste_fichier_zip])
        manquants = ref_fichiers.difference(actu_fichiers)
        en_trop = actu_fichiers.difference(ref_fichiers)
        assert len(manquants) == 0, "Fichiers manquants dans le zip: %s" % str(manquants)
        if len(en_trop) > 0:
            logging.warning("Fichiers en trop dans le zip: %s", str(en_trop))
        # assert len(liste_fichier_zip) >= len(liste_fichier_ref), \
        #     "Nombre de fichier qui ne correspond pas entre le zip et ref"
        for nomfichier in z.namelist():
            # print(nomfichier)
            nomfichierref = SupprimeDateTime(nomfichier)
            assert (nomfichierref in liste_fichier_ref), f"Fichier {nomfichierref} dans le zip seulement"
            nomfichierrefreel = liste_fichier_ref[nomfichierref]
            if nomfichierref.lower().endswith(".zip"):
                z.extract(nomfichier)
                check_compare_zip(ref_dir / nomfichierrefreel, Path(nomfichier), task.GetWorkingDir(), nomfichier[:-4])
            else:
                with open(ref_dir / nomfichierrefreel, "rb") as fref:
                    data_ref = SupprimeCreateTime(fref.read())

                with z.open(nomfichier, "r") as fgen:
                    data_gen = SupprimeCreateTime(fgen.read())
                if 'metadata_sum' in nomfichierref:
                    data_ref = SupprimeTimestampRB(SupprimeDateTimeRB(data_ref))
                    data_gen = SupprimeTimestampRB(SupprimeDateTimeRB(data_gen))
                if 'ZOO_raw' in nomfichierref or 'metadata_sum' in nomfichierref:
                    data_ref = SupprimerColFromTSV(data_ref, b'psampleid')
                    data_gen = SupprimerColFromTSV(data_gen, b'psampleid')
                cmpresult = checkCompareTSVorODV(data_ref, data_gen)
                if len(cmpresult) != 0:
                    # /!\ lorsque la comparaison échoue, la _totalité_ des fichiers originaux
                    # est exposée dans l'application de diff.
                    # Les différence NUMERIQUES gommées dans checkCompareTSVorODV _vont_ apparaître dans cet appli,
                    # alors qu'elle ne sont pas la cause de l'échec du test.
                    # E.g. Si sur 1000 lignes, 999 sont OK en utilisant la règle d'arrondi, mais qu'il
                    # manque un \t sur la ligne restante, les 1000 lignes seront affichées.
                    tmp_file = os.path.join(task.GetWorkingDir(), tmpfilename + "_" + nomfichier)
                    ref_tmp_file = os.path.join(task.GetWorkingDir(), 'ref_' + tmpfilename + "_" + nomfichier)
                    with open(tmp_file, "wb") as ftmp:
                        ftmp.write(data_gen)
                    with open(ref_tmp_file, "wb") as ftmp:
                        ftmp.write(data_ref)
                    ShowOnUIDiffApp(ref_tmp_file, tmp_file)
                assert cmpresult == []


# noinspection DuplicatedCode
def test_export_odv_reduit_multi(app, caplog,
                                 part_project_uvpapp, part_project_uvpbru, part_project_uvpremotelambdahttp):
    caplog.set_level(logging.DEBUG)  # pour mise au point
    # caplog.set_level(logging.CRITICAL)  # pour execution très silencieuse
    with TaskInstance(app, "TaskPartExport",
                      GetParams=f"filt_uproj={part_project_uvpapp.pprojid}&filt_uproj={part_project_uvpbru.pprojid}"
                                f"&filt_uproj={part_project_uvpremotelambdahttp.pprojid}",
                      post_params={'what': 'RED', 'fileformat': 'ODV', "starttask": "Y"}) as T:
        print(f"TaskID={T.TaskID}")
        T.RunTask()
        task = T.LoadTask()
        check_zip_with_ref("odv_reduit_multi", task, "tmpfile.odv")


def test_export_tsv_reduit_multi(app, caplog,
                                 part_project_uvpapp, part_project_uvpbru, part_project_uvpremotelambdahttp):
    caplog.set_level(logging.DEBUG)  # pour mise au point
    # caplog.set_level(logging.CRITICAL)  # pour execution très silencieuse
    # warnings.simplefilter("error", UserWarning) # transforme les warning en exception pour mieux les traquer
    with TaskInstance(app, "TaskPartExport",
                      GetParams=f"filt_uproj={part_project_uvpapp.pprojid}&filt_uproj={part_project_uvpbru.pprojid}"
                                f"&filt_uproj={part_project_uvpremotelambdahttp.pprojid}",
                      post_params={'what': 'RED', 'fileformat': 'TSV', "starttask": "Y"}) as T:
        print(f"TaskID={T.TaskID}")
        T.RunTask()
        task = T.LoadTask()
        check_zip_with_ref("tsv_reduit_multi", task, "tmpfile.tsv")


def test_export_tsvagg_reduit_multi(app, caplog,
                                    part_project_uvpapp, part_project_uvpbru, part_project_uvpremotelambdahttp):
    caplog.set_level(logging.DEBUG)  # pour mise au point
    caplog.set_level(logging.CRITICAL)  # pour execution très silencieuse
    with TaskInstance(app, "TaskPartExport",
                      GetParams=f"filt_uproj={part_project_uvpapp.pprojid}&filt_uproj={part_project_uvpbru.pprojid}"
                                f"&filt_uproj={part_project_uvpremotelambdahttp.pprojid}",
                      post_params={'what': 'RED', 'fileformat': 'TSV', 'aggregatefilesr': 'Y', "starttask": "Y"}) as T:
        print(f"TaskID={T.TaskID}")
        T.RunTask()
        task = T.LoadTask()
        check_zip_with_ref("tsvagg_reduit_multi", task, "tmpfile.tsv")


def test_export_odv_det_multi(app, caplog,
                              part_project_uvpapp, part_project_uvpbru, part_project_uvpremotelambdahttp):
    caplog.set_level(logging.DEBUG)  # pour mise au point
    caplog.set_level(logging.CRITICAL)  # pour execution très silencieuse
    with TaskInstance(app, "TaskPartExport",
                      GetParams=f"filt_uproj={part_project_uvpapp.pprojid}&filt_uproj={part_project_uvpbru.pprojid}"
                                f"&filt_uproj={part_project_uvpremotelambdahttp.pprojid}",
                      post_params={'what': 'DET', 'fileformatd': 'ODV', "starttask": "Y"}) as T:
        print(f"TaskID={T.TaskID}")
        T.RunTask()
        task = T.LoadTask()
        check_zip_with_ref("odv_det_multi", task, "tmpfile.odv")


def test_export_odv_det_multiExclNotLiving(app, caplog,
                                           part_project_uvpapp, part_project_uvpbru, part_project_uvpremotelambdahttp):
    caplog.set_level(logging.DEBUG)  # pour mise au point
    caplog.set_level(logging.CRITICAL)  # pour execution très silencieuse
    with TaskInstance(app, "TaskPartExport",
                      GetParams=f"filt_uproj={part_project_uvpapp.pprojid}&filt_uproj={part_project_uvpbru.pprojid}"
                                f"&filt_uproj={part_project_uvpremotelambdahttp.pprojid}",
                      post_params={'what': 'DET', 'fileformatd': 'ODV', "excludenotlivingd": "Y",
                                   "starttask": "Y"}) as T:
        print(f"TaskID={T.TaskID}")
        T.RunTask()
        task = T.LoadTask()
        check_zip_with_ref("odv_det_multiExclNotLiving", task, "tmpfile.odv")


def test_export_tsv_det_multi(app, caplog,
                              part_project_uvpapp, part_project_uvpbru, part_project_uvpremotelambdahttp):
    caplog.set_level(logging.DEBUG)  # pour mise au point
    caplog.set_level(logging.CRITICAL)  # pour execution très silencieuse
    # warnings.simplefilter("error", UserWarning) # transforme les warning en exception pour mieux les traquer
    with TaskInstance(app, "TaskPartExport",
                      GetParams=f"filt_uproj={part_project_uvpapp.pprojid}&filt_uproj={part_project_uvpbru.pprojid}"
                                f"&filt_uproj={part_project_uvpremotelambdahttp.pprojid}",
                      post_params={'what': 'DET', 'fileformat': 'TSV', "starttask": "Y"}) as T:
        print(f"TaskID={T.TaskID}")
        T.RunTask()
        task = T.LoadTask()
        check_zip_with_ref("tsv_det_multi", task, "tmpfile.tsv")


def test_export_tsvagg_det_multi(app, caplog,
                                 part_project_uvpapp, part_project_uvpbru, part_project_uvpremotelambdahttp):
    caplog.set_level(logging.DEBUG)  # pour mise au point
    caplog.set_level(logging.CRITICAL)  # pour execution très silencieuse
    # warnings.simplefilter("error", UserWarning) # transforme les warning en exception pour mieux les traquer
    with TaskInstance(app, "TaskPartExport",
                      GetParams=f"filt_uproj={part_project_uvpapp.pprojid}&filt_uproj={part_project_uvpbru.pprojid}"
                                f"&filt_uproj={part_project_uvpremotelambdahttp.pprojid}",
                      post_params={'what': 'DET', 'fileformat': 'TSV', 'aggregatefilesd': 'Y', "starttask": "Y"}) as T:
        print(f"TaskID={T.TaskID}")
        T.RunTask()
        task = T.LoadTask()
        check_zip_with_ref("tsvagg_det_multi", task, "tmpfile.tsv")


def test_export_raw_multi(app, caplog,
                          part_project_uvpapp, part_project_uvpbru, part_project_uvpremotelambdahttp):
    caplog.set_level(logging.DEBUG)  # pour mise au point
    # caplog.set_level(logging.CRITICAL)  # pour execution très silencieuse
    # warnings.simplefilter("error", UserWarning) # transforme les warning en exception pour mieux les traquer
    with TaskInstance(app, "TaskPartExport",
                      GetParams=f"filt_uproj={part_project_uvpapp.pprojid}&filt_uproj={part_project_uvpbru.pprojid}"
                                f"&filt_uproj={part_project_uvpremotelambdahttp.pprojid}",
                      post_params={'what': 'RAW', "starttask": "Y"}) as T:
        print(f"TaskID={T.TaskID}")
        T.RunTask()
        task = T.LoadTask()
        check_zip_with_ref("raw_multi", task, "tmpfile.tsv")


def test_export_raw_multiExclNotLiving(app, caplog,
                                       part_project_uvpapp, part_project_uvpbru, part_project_uvpremotelambdahttp):
    caplog.set_level(logging.DEBUG)  # pour mise au point
    caplog.set_level(logging.CRITICAL)  # pour execution très silencieuse
    # warnings.simplefilter("error", UserWarning) # transforme les warning en exception pour mieux les traquer
    with TaskInstance(app, "TaskPartExport",
                      GetParams=f"filt_uproj={part_project_uvpapp.pprojid}&filt_uproj={part_project_uvpbru.pprojid}"
                                f"&filt_uproj={part_project_uvpremotelambdahttp.pprojid}",
                      post_params={'what': 'RAW', "excludenotlivingr": "Y", "starttask": "Y"}) as T:
        print(f"TaskID={T.TaskID}")
        T.RunTask()
        task = T.LoadTask()
        check_zip_with_ref("raw_multiExclNotLiving", task, "tmpfile.tsv")


def test_export_raw_multiIncludeNotV(app, caplog,
                                     part_project_uvpapp, part_project_uvpbru, part_project_uvpremotelambdahttp):
    caplog.set_level(logging.DEBUG)  # pour mise au point
    caplog.set_level(logging.CRITICAL)  # pour execution très silencieuse
    # warnings.simplefilter("error", UserWarning) # transforme les warning en exception pour mieux les traquer
    with TaskInstance(app, "TaskPartExport",
                      GetParams=f"filt_uproj={part_project_uvpapp.pprojid}&filt_uproj={part_project_uvpbru.pprojid}"
                                f"&filt_uproj={part_project_uvpremotelambdahttp.pprojid}",
                      post_params={'what': 'RAW', "includenotvalidatedr": "Y", "starttask": "Y"}) as T:
        print(f"TaskID={T.TaskID}")
        T.RunTask()
        task = T.LoadTask()
        check_zip_with_ref("raw_multiIncludeNotV", task, "tmpfile.tsv")


def test_export_odv_reduit_multi_onftparea(app, caplog, tmpdir,
                                           part_project_uvpapp, part_project_uvpbru, part_project_uvpremotelambdahttp):
    caplog.set_level(logging.DEBUG)  # pour mise au point
    caplog.set_level(logging.CRITICAL)  # pour execution très silencieuse
    with TaskInstance(app, "TaskPartExport",
                      GetParams=f"filt_uproj={part_project_uvpapp.pprojid}&filt_uproj={part_project_uvpbru.pprojid}"
                                f"&filt_uproj={part_project_uvpremotelambdahttp.pprojid}",
                      post_params={'what': 'RED', 'fileformat': 'ODV', "putfileonftparea": "Y", "starttask": "Y"}) as T:
        print(f"TaskID={T.TaskID}")
        # on deplace la zone FTP dans le dossier temporaire
        app.config['FTPEXPORTAREA'] = tmpdir
        ftpexportarea = Path(app.config['FTPEXPORTAREA'])
        T.RunTask()
        task = T.LoadTask()
        check_zip_with_ref("odv_reduit_multi", task, "tmpfile.odv", FTPExportAreaFolter=ftpexportarea)
