from pathlib import Path
import numpy as np
import appli.part.database as partdatabase
import csv
import datetime
import io
import math
import zipfile
from appli import database
from appli import db, app, VaultRootDir, EncodeEqualList, CreateDirConcurrentlyIfNeeded
from appli.part import CTDFixedCol


# Purge les espace et converti le Nan en vide
def CleanValue(v):
    if type(v) != str:
        return v
    v = v.strip()
    if (v.lower() == 'nan') or (v.lower() == 'na'):
        v = ''
    if v.lower().find('inf') >= 0:
        v = ''
    return v


# retourne le flottant image de la chaine en faisant la conversion ou None
def ToFloat(value):
    if value == '':
        return None
    try:
        return float(value)
    except ValueError:
        return None


def GetTicks(max_val):
    if np.isnan(max_val):
        max_val = 100  # Arbitraire si max_val n'est pas valide
    if max_val < 1:
        max_val = 1
    step = math.pow(10, math.floor(math.log10(max_val)))
    if (max_val / step) < 3:
        step = step / 2
    return np.arange(0, max_val, step)


def GenerateReducedParticleHistogram(psampleid):
    """
    Génération de l'histogramme particulaire détaillé (45 classes) et réduit (15 classes)
    à partir de l'histogramme détaillé
    :param psampleid:
    :return:
    """
    if database.GetAll("select count(*) from part_histopart_det where psampleid=" + str(psampleid))[0][0] <= 0:
        return "<span style='color: red;'>Reduced Histogram can't be computer without Detailed histogram</span>"
    database.ExecSQL("delete from part_histopart_reduit where psampleid=" + str(psampleid))
    sql = """insert into part_histopart_reduit(psampleid, lineno, depth,datetime,  watervolume
    , class01, class02, class03, class04, class05, class06, class07, class08, class09, class10, class11, class12
    , class13, class14, class15
    , biovol01, biovol02, biovol03, biovol04, biovol05, biovol06, biovol07, biovol08, biovol09, biovol10, biovol11
    , biovol12, biovol13, biovol14, biovol15
    )
    select psampleid, lineno, depth,datetime,  watervolume,
            case when coalesce(class01,class02,class03) is not null 
                    then coalesce(class01,0)+coalesce(class02,0)+coalesce(class03,0) end as c1,
            case when coalesce(class04,class05,class06) is not null 
                    then coalesce(class04,0)+coalesce(class05,0)+coalesce(class06,0) end as c2,
            case when coalesce(class07,class08,class09) is not null 
                    then coalesce(class07,0)+coalesce(class08,0)+coalesce(class09,0) end as c3,
            case when coalesce(class10,class11,class12) is not null 
                    then coalesce(class10,0)+coalesce(class11,0)+coalesce(class12,0) end as c4,
            case when coalesce(class13,class14,class15) is not null 
                    then coalesce(class13,0)+coalesce(class14,0)+coalesce(class15,0) end as c5,
            case when coalesce(class16,class17,class18) is not null 
                    then coalesce(class16,0)+coalesce(class17,0)+coalesce(class18,0) end as c6,
            case when coalesce(class19,class20,class21) is not null 
                    then coalesce(class19,0)+coalesce(class20,0)+coalesce(class21,0) end as c7,
            case when coalesce(class22,class23,class24) is not null 
                    then coalesce(class22,0)+coalesce(class23,0)+coalesce(class24,0) end as c8,
            case when coalesce(class25,class26,class27) is not null 
                    then coalesce(class25,0)+coalesce(class26,0)+coalesce(class27,0) end as c9,
            case when coalesce(class28,class29,class30) is not null 
                    then coalesce(class28,0)+coalesce(class29,0)+coalesce(class30,0) end as c10,
            case when coalesce(class31,class32,class33) is not null 
                    then coalesce(class31,0)+coalesce(class32,0)+coalesce(class33,0) end as c11,
            case when coalesce(class34,class35,class36) is not null 
                    then coalesce(class34,0)+coalesce(class35,0)+coalesce(class36,0) end as c12,
            case when coalesce(class37,class38,class39) is not null 
                    then coalesce(class37,0)+coalesce(class38,0)+coalesce(class39,0) end as c13,
            case when coalesce(class40,class41,class42) is not null 
                    then coalesce(class40,0)+coalesce(class41,0)+coalesce(class42,0) end as c14,
            case when coalesce(class43,class44,class45) is not null 
                    then coalesce(class43,0)+coalesce(class44,0)+coalesce(class45,0) end as c15,
            case when coalesce(biovol01,biovol02,biovol03) is not null 
                    then coalesce(biovol01,0)+coalesce(biovol02,0)+coalesce(biovol03,0) end as bv1,
            case when coalesce(biovol04,biovol05,biovol06) is not null 
                    then coalesce(biovol04,0)+coalesce(biovol05,0)+coalesce(biovol06,0) end as bv2,
            case when coalesce(biovol07,biovol08,biovol09) is not null 
                    then coalesce(biovol07,0)+coalesce(biovol08,0)+coalesce(biovol09,0) end as bv3,
            case when coalesce(biovol10,biovol11,biovol12) is not null 
                    then coalesce(biovol10,0)+coalesce(biovol11,0)+coalesce(biovol12,0) end as bv4,
            case when coalesce(biovol13,biovol14,biovol15) is not null 
                    then coalesce(biovol13,0)+coalesce(biovol14,0)+coalesce(biovol15,0) end as bv5,
            case when coalesce(biovol16,biovol17,biovol18) is not null 
                    then coalesce(biovol16,0)+coalesce(biovol17,0)+coalesce(biovol18,0) end as bv6,
            case when coalesce(biovol19,biovol20,biovol21) is not null 
                    then coalesce(biovol19,0)+coalesce(biovol20,0)+coalesce(biovol21,0) end as bv7,
            case when coalesce(biovol22,biovol23,biovol24) is not null 
                    then coalesce(biovol22,0)+coalesce(biovol23,0)+coalesce(biovol24,0) end as bv8,
            case when coalesce(biovol25,biovol26,biovol27) is not null 
                    then coalesce(biovol25,0)+coalesce(biovol26,0)+coalesce(biovol27,0) end as bv9,
            case when coalesce(biovol28,biovol29,biovol30) is not null 
                    then coalesce(biovol28,0)+coalesce(biovol29,0)+coalesce(biovol30,0) end as bv10,
            case when coalesce(biovol31,biovol32,biovol33) is not null 
                    then coalesce(biovol31,0)+coalesce(biovol32,0)+coalesce(biovol33,0) end as bv11,
            case when coalesce(biovol34,biovol35,biovol36) is not null 
                    then coalesce(biovol34,0)+coalesce(biovol35,0)+coalesce(biovol36,0) end as bv12,
            case when coalesce(biovol37,biovol38,biovol39) is not null 
                    then coalesce(biovol37,0)+coalesce(biovol38,0)+coalesce(biovol39,0) end as bv13,
            case when coalesce(biovol40,biovol41,biovol42) is not null 
                    then coalesce(biovol40,0)+coalesce(biovol41,0)+coalesce(biovol42,0) end as bv14,
            case when coalesce(biovol43,biovol44,biovol45) is not null 
                    then coalesce(biovol43,0)+coalesce(biovol44,0)+coalesce(biovol45,0) end as bv15
    from part_histopart_det where psampleid=""" + str(psampleid)
    database.ExecSQL(sql)
    return " reduced Histogram computed"


def ImportCTD(psampleid, user_name, user_email):
    """
    Importe les données CTD 
    :param user_email:
    :param user_name:
    :param psampleid:
    :return:
    """

    uvp_sample = db.session.query(partdatabase.part_samples).filter_by(psampleid=psampleid).first()
    if uvp_sample is None:
        raise Exception("ImportCTD: Sample %d missing" % psampleid)
    prj = db.session.query(partdatabase.part_projects).filter_by(pprojid=uvp_sample.pprojid).first()
    if prj.instrumtype == 'uvp6remote':
        rawfileinvault = GetPathForRawHistoFile(uvp_sample.psampleid)
        zf = zipfile.ZipFile(rawfileinvault, "r")
        if 'CTD.txt' not in zf.namelist():
            app.logger.info("CTD.txt file missing")
            return False
        fctb = zf.open('CTD.txt', 'r')
        tsvfile = io.TextIOWrapper(fctb, encoding='latin_1')
    else:  # process normal par traitement du repertoire des données
        server_root = Path(app.config['SERVERLOADAREA'])
        dossier_uvp_path = server_root / prj.rawfolder
        ctd_file = dossier_uvp_path / "ctd_data_cnv" / (uvp_sample.profileid + ".ctd")
        if not ctd_file.exists():
            app.logger.info("CTD file %s missing", ctd_file.as_posix())
            return False
        app.logger.info("Import CTD file %s", ctd_file.as_posix())
        tsvfile = ctd_file.open('r', encoding='latin_1')

    rdr = csv.reader(tsvfile, delimiter='\t')
    head_row = rdr.__next__()
    # Analyser la ligne de titre et assigner à chaque ID l'attribut
    # Construire la table d'association des attributs complémentaires.
    extrames_id: int = 0
    mapping = []
    extra_mapping = {}
    for ic, c in enumerate(head_row):
        clow = c.lower().strip()
        if clow == "chloro fluo [mg chl/m3]":
            clow = "chloro fluo [mg chl m-3]"
        if clow == "conductivity [ms/cm]":
            clow = "conductivity [ms cm-1]"
        if clow == "depth [salt water, m]":
            clow = "depth [m]"
        if clow == "fcdom factory [ppb qse]":
            clow = "fcdom [ppb qse]"
        if clow == "in situ density anomaly [kg/m3]":
            clow = "in situ density anomaly [kg m-3]"
        if clow == "nitrate [µmol/l]":
            clow = "nitrate [umol l-1]"
        if clow == "oxygen [µmol/kg]":
            clow = "oxygen [umol kg-1]"
        if clow == "oxygen [ml/l]":
            clow = "oxygen [ml l-1]"
        if clow == "par [µmol m-2 s-1]":
            clow = "par [umol m-2 s-1]"
        if clow == "potential density anomaly [kg/m3]":
            clow = "potential density anomaly [kg m-3]"
        if clow == "pressure in water column [db]":
            clow = "pressure [db]"
        if clow == "spar [µmol m-2 s-1]":
            clow = "spar [umol m-2 s-1]"
        if clow in CTDFixedCol:
            target = CTDFixedCol[clow]
        else:
            # print (clow)
            extrames_id += 1
            target = 'extrames%02d' % extrames_id
            extra_mapping['%02d' % extrames_id] = c
            if extrames_id > 20:
                raise Exception("ImportCTD: Too much CTD data, column %s skipped" % c)
        mapping.append(target)
    app.logger.info("mapping = %s", mapping)
    database.ExecSQL("delete from part_ctd where psampleid=%s" % psampleid)
    for i, r in enumerate(rdr):
        cl = partdatabase.part_ctd()
        cl.psampleid = psampleid
        cl.lineno = i
        for j, c in enumerate(mapping):
            v = CleanValue(r[j])
            if v != '':
                if c == 'qc_flag':
                    setattr(cl, c, int(float(v)))
                elif c == 'datetime':
                    setattr(cl, c, datetime.datetime(int(v[0:4]), int(v[4:6]), int(v[6:8]), int(v[8:10]), int(v[10:12]),
                                                     int(v[12:14]), int(v[14:17]) * 1000))
                else:
                    setattr(cl, c, v)
        db.session.add(cl)
        db.session.commit()
    uvp_sample.ctd_desc = EncodeEqualList(extra_mapping)
    uvp_sample.ctd_import_datetime = datetime.datetime.now()
    uvp_sample.ctd_import_name = user_name
    uvp_sample.ctd_import_email = user_email
    db.session.commit()
    return True


def GetPathForRawHistoFile(psampleid, flash='1'):
    vault_folder = "partraw%04d" % (psampleid // 10000)
    vaultroot = Path(VaultRootDir)
    # creation du repertoire contenant les histogramme brut si necessaire
    CreateDirConcurrentlyIfNeeded(vaultroot / vault_folder)
    # si flash est à 0 on ajoute .black dans le nom du fichier
    return (vaultroot / vault_folder / (
            "%04d%s.tsv.bz2" % (psampleid % 10000, '.black' if flash == '0' else ''))).as_posix()
