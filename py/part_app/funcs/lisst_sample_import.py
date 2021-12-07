import bz2
import csv
import logging
from pathlib import Path

import numpy as np

from .uvp_sample_import import GetPathForRawHistoFile
from .. import database as partdatabase, app
from ..app import db
from ..constants import PartDetClassLimit
from ..db_utils import ExecSQL
from ..funcs.common_sample_import import CleanValue, ToFloat, GenerateReducedParticleHistogram
from ..prod_or_dev import DEV_BEHAVIOR


def CreateOrUpdateSample(pprojid, headerdata):
    """
    Crée ou met à jour le sample
    :param pprojid:
    :param headerdata:
    :return: Objet BD sample
    """
    for k, v in headerdata.items():
        headerdata[k] = CleanValue(v)
    sample = partdatabase.part_samples.query.filter_by(profileid=headerdata['profileid'], pprojid=pprojid).first()
    if sample is None:
        logging.info("Create LISST sample for %s %s" % (headerdata['profileid'], headerdata['filename']))
        sample = partdatabase.part_samples()
        sample.profileid = headerdata['profileid']
        sample.pprojid = pprojid
        db.session.add(sample)
    else:
        logging.info(
            "Update LISST sample %s for %s %s" % (sample.psampleid, headerdata['profileid'], headerdata['filename']))
    sample.filename = headerdata['filename']
    sample.latitude = ToFloat(headerdata['latitude'])
    sample.longitude = ToFloat(headerdata['longitude'])
    sample.organizedbydeepth = True
    sample.stationid = headerdata['stationid']
    sample.comment = headerdata['comment']
    sample.lisst_zscat_filename = headerdata['zscat_filename']
    sample.lisst_kernel = headerdata['kernel']
    sample.lisst_year = headerdata['year']
    db.session.commit()
    return sample.psampleid


def BuildLISSTClass(kerneltype):
    if kerneltype == 'spherical':
        x = 1.25
    elif kerneltype == 'random':
        x = 1.00
    else:
        raise Exception("Invalide LISST kernel type '%s'" % kerneltype)
    lisst_class = np.ndarray((32, 3))
    rho = np.power(200.0, 1 / 32.0)
    lisst_class[:, 0] = x * (np.power(rho, np.arange(0, 32))) / 1000
    lisst_class[:, 1] = x * (np.power(rho, np.arange(1, 33))) / 1000
    lisst_class[:, 2] = np.sqrt(lisst_class[:, 0] * lisst_class[:, 1])
    return lisst_class


def MapClasses(L, LISSTClass):
    res = np.zeros(45)
    for i, q in enumerate(L):
        # print ("%d %0.06f-%0.06f %g"%(i,LISSTClass[i,0],LISSTClass[i,1],q))
        if q != 0:  # on ne passe pas du temps à essayer de ventiler 0
            # recherche des limites dans PartDetClassLimit
            first_class = last_class = -1
            for ipd, pdl in enumerate(PartDetClassLimit):
                if first_class < 0 and pdl > LISSTClass[i, 0]:
                    first_class = ipd - 1
                if pdl > LISSTClass[i, 1]:
                    last_class = ipd - 1
                    break
            if first_class == last_class:  # ventilé dans une classe unique
                res[first_class] += q
            else:  # ventillé dans 2 classes (il n'y a jamais plus de 2 classes
                limite = PartDetClassLimit[last_class]
                gauche = q * (limite - LISSTClass[i, 0]) / (LISSTClass[i, 1] - LISSTClass[i, 0])
                droite = q - gauche
                res[first_class] += gauche
                res[first_class + 1] += droite
    return res


def GenerateRawHistogram(psampleid):
    """
    Sur le lisst, c'est juste une copie du asc qui est stockée en format BZIP
    :param psampleid:
    :return: None
    """
    # PartSample= partdatabase.part_samples.query.filter_by(psampleid=psampleid).first()
    part_sample = db.session.query(partdatabase.part_samples).filter_by(psampleid=psampleid).first()
    if part_sample is None:
        raise Exception("GenerateRawHistogram: Sample %d missing" % psampleid)

    prj = db.session.query(partdatabase.part_projects).filter_by(pprojid=part_sample.pprojid).first()
    server_root = app.ServerLoadArea
    dossier_uvp_path = server_root / prj.rawfolder
    fichier = dossier_uvp_path / "work" / (part_sample.filename + '.asc')
    if not fichier.exists():
        raise Exception(f"GenerateRawHistogram: file {fichier.as_posix()} missing")
    logging.info("Processing file " + fichier.as_posix())

    raw_file = GetPathForRawHistoFile(part_sample.psampleid)
    with bz2.open(raw_file, "wb") as f, fichier.open('rb') as fFichier:
        f.write(fFichier.read())
    part_sample.histobrutavailable = True
    db.session.commit()


def GenerateParticleHistogram(psampleid):
    """
    Génération de l'histogramme particulaire détaillé (45 classes) et réduit (15 classes) à partir du fichier ASC
    :param psampleid:
    :return:
    """
    part_sample = partdatabase.part_samples.query.filter_by(psampleid=psampleid).first()
    if part_sample is None:
        raise Exception("GenerateParticleHistogram: Sample %d missing" % psampleid)
    if not part_sample.organizedbydeepth:
        raise Exception("GenerateParticleHistogram: Sample %d , LISST support only organized by depth data" % psampleid)
    lisst_class = BuildLISSTClass(part_sample.lisst_kernel)

    logging.info(f"Processing sample {psampleid} raw file")
    # Col0=Nbr Data pour calculer la moyenne , 1->45 Biovol cumulé puis moyénné
    histo_by_tranche = np.zeros((1, 46))
    if DEV_BEHAVIOR:
        # Stocké sous forme .bz2?
        raw_file = GetPathForRawHistoFile(part_sample.psampleid)
        csvfile = bz2.open(raw_file, 'rt')
    else:
        Prj = partdatabase.part_projects.query.filter_by(pprojid=part_sample.pprojid).first()
        ServerRoot = app.ServerLoadArea
        DossierUVPPath = ServerRoot / Prj.rawfolder
        Fichier = DossierUVPPath / "work" / (part_sample.filename + '.asc')
        logging.info("Processing file " + Fichier.as_posix())
        NbrLine = 0
        with Fichier.open() as csvfile:
            for L in csvfile:
                NbrLine += 1
        logging.info("Line count %d" % NbrLine)
        csvfile = Fichier.open()
    try:
        rdr = csv.reader(csvfile, delimiter=' ')
        for i, row in enumerate(rdr):
            depth = float(row[36])
            if part_sample.organizedbydeepth:
                tranche = int(depth // 5)
            else:
                tranche = int(i // 50)
            part = np.empty(32)
            for k in range(0, 32):
                part[k] = float(row[k])
            # Mappe les 32 classes et retourne les 45 classes
            part = MapClasses(part, lisst_class)
            # Todo gérer l'horodatage des tranche en profil horizontal
            if tranche >= histo_by_tranche.shape[0]:
                new_array = np.zeros((tranche + 1, 46))
                new_array[0:histo_by_tranche.shape[0], :] = histo_by_tranche
                histo_by_tranche = new_array

            histo_by_tranche[tranche, 1:46] += part
            histo_by_tranche[tranche, 0] += 1
    finally:
        csvfile.close()
    histo_by_tranche[:, 1:46] /= histo_by_tranche[:, 0, np.newaxis]

    ExecSQL("delete from part_histopart_det where psampleid=" + str(psampleid))
    sql = """insert into part_histopart_det(psampleid, lineno, depth,  watervolume
        , biovol01, biovol02, biovol03, biovol04, biovol05, biovol06, biovol07, biovol08, biovol09, biovol10, biovol11
        , biovol12, biovol13, biovol14, biovol15, biovol16, biovol17, biovol18, biovol19, biovol20, biovol21, biovol22
        , biovol23, biovol24, biovol25, biovol26, biovol27, biovol28, biovol29, biovol30, biovol31, biovol32, biovol33
        , biovol34, biovol35, biovol36, biovol37, biovol38, biovol39, biovol40, biovol41, biovol42, biovol43, biovol44
        , biovol45)
    values(%(psampleid)s,%(lineno)s,%(depth)s,%(watervolume)s,%(biovol01)s,%(biovol02)s,%(biovol03)s,%(biovol04)s
    ,%(biovol05)s,%(biovol06)s,%(biovol07)s,%(biovol08)s,%(biovol09)s,%(biovol10)s,%(biovol11)s,%(biovol12)s
    ,%(biovol13)s,%(biovol14)s,%(biovol15)s,%(biovol16)s,%(biovol17)s
    ,%(biovol18)s,%(biovol19)s,%(biovol20)s,%(biovol21)s,%(biovol22)s,%(biovol23)s,%(biovol24)s,%(biovol25)s
    ,%(biovol26)s,%(biovol27)s,%(biovol28)s
    ,%(biovol29)s,%(biovol30)s,%(biovol31)s,%(biovol32)s,%(biovol33)s,%(biovol34)s,%(biovol35)s,%(biovol36)s
    ,%(biovol37)s,%(biovol38)s,%(biovol39)s
    ,%(biovol40)s,%(biovol41)s,%(biovol42)s,%(biovol43)s,%(biovol44)s,%(biovol45)s)"""
    sqlparam = {'psampleid': psampleid}
    for i, r in enumerate(histo_by_tranche):
        sqlparam['lineno'] = i
        # Todo ajuste au type
        sqlparam['depth'] = (i * 5 + 2.5)
        sqlparam['watervolume'] = None
        # sqlparam['watervolume'] = VolumeParTranche[i]
        for k in range(0, 45):
            sqlparam['biovol%02d' % (k + 1)] = r[k + 1]
        ExecSQL(sql, sqlparam)

    GenerateReducedParticleHistogram(psampleid)
