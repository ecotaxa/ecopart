import bz2
import configparser
import csv
import datetime
import io
import logging
import math
import re
import sys
import zipfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import psycopg2.extras

from .common_sample_import import GetPathForRawHistoFile
from .. import database as partdatabase, app
from ..app import part_app, db
from ..constants import PartDetClassLimit, VOLUME_ROUNDING
from ..db_utils import ExecSQL, GetAssoc, GetAll
from ..fs_utils import CreateDirConcurrentlyIfNeeded
from ..funcs.common_sample_import import CleanValue, ToFloat, GetTicks, GenerateReducedParticleHistogram
from ..prod_or_dev import DEV_BEHAVIOR
from ..remote import EcoTaxaInstance
from ..tasks.importcommon import ConvTextDegreeDotMinuteToDecimalDegree, calcpixelfromesd_aa_exp
from ..txt_utils import DecodeEqualList


def CreateOrUpdateSample(pprojid, headerdata):
    """
    Crée ou met à jour le sample
    :param pprojid:
    :param headerdata:
    :return: Objet BD sample
    """
    prj = partdatabase.part_projects.query.filter_by(pprojid=pprojid).first()
    for k, v in headerdata.items():
        headerdata[k] = CleanValue(v)
    sample = partdatabase.part_samples.query.filter_by(profileid=headerdata['profileid'], pprojid=pprojid).first()
    if sample is None:
        logging.info("Create UVP sample for %s %s" % (headerdata['profileid'], headerdata['filename']))
        sample = partdatabase.part_samples()
        sample.profileid = headerdata['profileid']
        sample.pprojid = pprojid
        db.session.add(sample)
    else:
        logging.info(
            "Update UVP sample %s for %s %s" % (sample.psampleid, headerdata['profileid'], headerdata['filename']))
    sample.filename = headerdata['filename']
    if 'sampledatetime' in headerdata and headerdata['sampledatetime']:
        sampledatetxt = headerdata['sampledatetime']  # format uvpapp
    else:
        sampledatetxt = headerdata['filename']  # format historique uvp5
    m = re.search(r"(\d{4})(\d{2})(\d{2})-?(\d{2})(\d{2})(\d{2})?",
                  sampledatetxt)  # YYYYMMDD-HHMMSS avec tiret central et secondes optionnelles
    sample.sampledate = datetime.datetime(*[int(x) if x else 0 for x in m.group(1, 2, 3, 4, 5, 6)])
    sample.latitude = ConvTextDegreeDotMinuteToDecimalDegree(
        headerdata['latitude'], prj.instrumtype)  # dans les fichiers UVP historique c'est la notation degree.minute
    sample.longitude = ConvTextDegreeDotMinuteToDecimalDegree(headerdata['longitude'], prj.instrumtype)
    # Nouvelle colonne optionnelle, par défaut organisé par (P)ression
    sample.organizedbydeepth = headerdata.get('sampletype', 'P') == 'P'
    # 2020-05-01 : ce champ est à present actualisé lors du traitement du sample
    # Si sample vertical alors filtrage en descente activé par défaut.
    # sample.acq_descent_filter=sample.organizedbydeepth
    sample.ctd_origfilename = headerdata['ctdrosettefilename']
    if headerdata['winddir']:
        sample.winddir = int(round(ToFloat(headerdata['winddir'])))
    if headerdata['windspeed']:
        sample.winspeed = int(round(ToFloat(headerdata['windspeed'])))
    if headerdata['seastate']:
        sample.seastate = int(headerdata['seastate'])
    if headerdata['nebuloussness']:
        sample.nebuloussness = int(headerdata['nebuloussness'])
    if headerdata.get('integrationtime'):
        sample.integrationtime = int(headerdata['integrationtime'])
    sample.comment = headerdata['comment']
    sample.stationid = headerdata['stationid']
    sample.acq_volimage = ToFloat(headerdata['volimage'])
    sample.acq_aa = ToFloat(headerdata['aa'])
    sample.acq_exp = ToFloat(headerdata['exp'])
    if headerdata.get('bottomdepth'):
        sample.bottomdepth = int(headerdata['bottomdepth']) // 10
    sample.yoyo = headerdata['yoyo'] == "Y"
    sample.firstimage = int(float(headerdata['firstimage']))
    sample.lastimg = int(float(headerdata['endimg']))
    sample.proc_soft = "Zooprocess"
    if headerdata.get("pixelsize"):
        sample.acq_pixel = float(headerdata['pixelsize'])

    server_root = app.ServerLoadArea
    dossier_uvp_path = server_root / prj.rawfolder
    uvp5_configuration_data = dossier_uvp_path / "config" / "uvp5_settings" / "uvp5_configuration_data.txt"
    if not uvp5_configuration_data.exists():
        # warning sauf si déjà rempli grace à la colonne ajoutée au fichier header version uvpapp
        if sample.acq_pixel is None:
            logging.warning("file %s is missing, pixel data will miss (required for Taxo histogram esd/biovolume)" % (
                uvp5_configuration_data.as_posix()))
    else:
        with uvp5_configuration_data.open('r', encoding='latin_1') as F:
            lines = F.read()
            config_param = DecodeEqualList(lines)
            if 'pixel' not in config_param:
                part_app.logger.warning("pixel parameter missing in file %s " % (uvp5_configuration_data.as_posix()))
            else:
                sample.acq_pixel = float(config_param['pixel'])
            if 'xsize' in config_param:
                sample.acq_xsize = int(config_param['xsize'])
            if 'ysize' in config_param:
                sample.acq_ysize = int(config_param['ysize'])

    ecodata_part_file = None
    hdr_folder = dossier_uvp_path / "raw" / ("HDR" + sample.filename)
    hdr_file = hdr_folder / ("HDR" + sample.filename + ".hdr")
    if not hdr_file.exists():
        hdr_folder = dossier_uvp_path / "work" / sample.profileid
        hdr_file = hdr_folder / ("HDR" + sample.filename + ".txt")
        if not hdr_file.exists():
            ecodata_part_file = dossier_uvp_path / "ecodata" / sample.profileid / (sample.profileid + "_Particule.zip")
            if ecodata_part_file.exists():
                hdr_file = None  # pas un fichier HDR donc on lira le fichier zip
            else:
                raise Exception("File %s or %s are  missing, and in raw folder too" % (
                    hdr_file.as_posix(), ecodata_part_file.as_posix()))
    if hdr_file:
        with hdr_file.open('r', encoding='latin_1') as F:
            F.readline()  # on saute la ligne 1
            ligne2 = F.readline().strip('; \r\n')
            # print("ligne2= '%s'" % (ligne2))
            sample.acq_filedescription = ligne2
            m = re.search(R"\w+ (\w+)", ligne2)
            if m is not None and m.lastindex == 1:
                sample.instrumsn = m.group(1)
            lines = F.read()
            hdr_param = DecodeEqualList(lines)
            # print("%s" % (hdr_param))
            sample.acq_shutterspeed = ToFloat(hdr_param.get('shutterspeed', ''))
            sample.acq_smzoo = int(hdr_param['smzoo'])
            sample.acq_smbase = int(hdr_param['smbase'])
            sample.acq_exposure = ToFloat(hdr_param.get('exposure', ''))
            sample.acq_gain = ToFloat(hdr_param.get('gain', ''))
            sample.acq_eraseborder = ToFloat(hdr_param.get('eraseborderblobs', ''))
            sample.acq_tasktype = ToFloat(hdr_param.get('tasktype', ''))
            sample.acq_threshold = ToFloat(hdr_param.get('thresh', ''))
            sample.acq_choice = ToFloat(hdr_param.get('choice', ''))
            sample.acq_disktype = ToFloat(hdr_param.get('disktype', ''))
            sample.acq_ratio = ToFloat(hdr_param.get('ratio', ''))
    else:
        z = zipfile.ZipFile(ecodata_part_file.as_posix())
        with z.open("metadata.ini", "r") as metadata_ini_raw:
            metadata_ini = io.TextIOWrapper(io.BytesIO(metadata_ini_raw.read()), encoding="latin_1")
            # with open(metadata_ini_raw, encoding='latin_1') as metadata_ini:
            ini = configparser.ConfigParser()
            ini.read_file(metadata_ini)
            hw_conf = ini['HW_CONF']
            acq_conf = ini['ACQ_CONF']
            sample.acq_shutterspeed = ToFloat(hw_conf.get('Shutter', ''))
            sample.acq_gain = ToFloat(hw_conf.get('Gain', ''))
            sample.acq_threshold = ToFloat(hw_conf.get('Threshold', ''))
            sample.acq_smzoo = calcpixelfromesd_aa_exp(
                ToFloat(acq_conf.get('Vignetting_lower_limit_size', '')) / 1000.0, sample.acq_aa, sample.acq_exp)
            sample.acq_smbase = calcpixelfromesd_aa_exp(ToFloat(acq_conf.get('Limit_lpm_detection_size', '')) / 1000.0,
                                                        sample.acq_aa, sample.acq_exp)
            if hw_conf.get('Pressure_offset', '') != '':
                if 0 <= ToFloat(hw_conf.get('Pressure_offset', '')) < 100:
                    sample.acq_depthoffset = ToFloat(hw_conf.get('Pressure_offset', ''))
    db.session.commit()
    return sample.psampleid


def GetPathForImportGraph(psampleid, suffix, relative_to_vault=False):
    """
    Retourne le chemin vers l'image associée en gérant l'éventuelle création du répertoire  
    :param psampleid: 
    :param suffix: suffixe mis à la fin du nom de l'image
    :param relative_to_vault:
    :return: chemin posix de l'image 
    """
    vault_folder = "pargraph%04d" % (psampleid // 10000)
    vaultroot = Path(app.VaultRootDir)
    # creation du repertoire contenant les graphe d'importation si necessaire
    if not relative_to_vault:  # Si Relatif c'est pour avoir l'url inutile de regarder si le repertoire existe.
        CreateDirConcurrentlyIfNeeded(vaultroot / vault_folder)
    nom_fichier = "%06d_%s.png" % (psampleid % 10000, suffix)
    if relative_to_vault:
        return vault_folder + "/" + nom_fichier
    else:
        return (vaultroot / vault_folder / nom_fichier).as_posix()


def ExplodeGreyLevel(Nbr, Avg, ET):
    """
    ventile les particule de façon lineaire sur +/- l'ecart type
    :param Nbr: # de particule
    :param Avg: # Gris moyen
    :param ET:  # ecart type
    :return: Liste de paire Nbr, Niveau de gris
    """
    if ET < 1 or Nbr < ET:
        return [[Nbr, Avg]]
    mini = Avg - ET
    if mini < 1:
        mini = 1
    maxi = Avg + ET
    if maxi > 255:
        maxi = 255
    res = []
    tot = 0
    for i in range(mini, maxi + 1):
        n = round(Nbr / (2 * ET + 1))
        res.append([n, i])
        tot += n
    res[len(res) // 2][0] += Nbr - tot  # On ajoute ce qu'il manque sur la moyenne
    return res


def GenerateRawHistogramUVPAPP(UvpSample, Prj, DepthOffset, organizedbydepth, descent_filter, EcodataPartFile):
    """
    Génération de l'histogramme particulaire à partir d'un fichier généré par UVPApp
    """
    raw_img_depth = {}  # version non filtrée utilisée pour générer le graphique
    img_depth = {}  # version filtrée
    img_time = {}  # heure des images
    segmented_data = {'0': {}, '1': {}}  # version filtrée black&flash
    prev_depth = 0
    descent_filter_removed_count = 0
    organizedbytime = not organizedbydepth
    if organizedbytime:
        descent_filter = False  # sur les profile temporel le filtrage en descente ne peux pas être utilisé.
    z = zipfile.ZipFile(EcodataPartFile.as_posix())
    with z.open("particules.csv", "r") as csvfile:
        logging.info("Processing file " + EcodataPartFile.as_posix() + "/particules.csv")
        idx = -1  # Les index d'image sont en base 0
        for rownum, row in enumerate(csvfile):
            row = row.decode('latin-1')
            rowpart = row.split(":")
            if len(rowpart) != 2:  # Pas une ligne data
                continue
            if rowpart[0][0:2] != "20":
                continue  # les lignes de données commencent toutes par la date 2019-MM-DD ...
            idx += 1
            header = rowpart[0].split(",")
            dateheuretxt = header[0]
            depth = float(header[1]) + DepthOffset
            if math.isnan(depth):
                if organizedbydepth:
                    continue  # si on a pas de profondeur on ne peut pas traiter la donnée
                else:
                    depth = float(0)
            else:
                if depth < 0:
                    depth = 0  # les profondeur négatives sont forcées à 0
            raw_img_depth[idx] = depth
            img_time[idx] = dateheuretxt
            flash = header[3]
            # Application du filtre en descente
            keep_line = True
            if descent_filter:
                if depth < prev_depth:
                    keep_line = False
                else:
                    prev_depth = depth
            if keep_line:
                img_depth[idx] = depth
            else:
                descent_filter_removed_count += 1
            if keep_line == False:
                continue

            data = [p.split(',') for p in rowpart[1].split(";") if len(p.split(',')) == 4]
            if rowpart[1].find("OVER_EXPOSED") >= 0:
                pass
            elif rowpart[1].find("EMPTY_IMAGE") >= 0:
                pass
            elif int(data[0][0]) == 0:  # taille de particule non valide
                pass
            else:  # Données normales

                nb_tirets = dateheuretxt.count("-")
                if nb_tirets == 1:
                    dateheure = datetime.datetime.strptime(dateheuretxt, "%Y%m%d-%H%M%S")
                elif nb_tirets == 2:  # avec ms https://github.com/ecotaxa/ecopart/issues/32
                                       # et https://github.com/ecotaxa/ecopart/issues/60
                    dateheure = datetime.datetime.strptime(dateheuretxt, "%Y%m%d-%H%M%S-%f")
                else:  # Pas un format valide ou chaîne vide
                    dateheure = None

                if organizedbydepth:
                    partition = math.floor(depth)
                else:
                    integrationtime = int(UvpSample.integrationtime)
                    if integrationtime <= 0:
                        raise Exception(
                            "GenerateRawHistogramUVPAPP: Sample %d : integrationtime must be a positive value for horizontal profile"
                            % [UvpSample.psampleid])
                    partts = (dateheure.timestamp() // integrationtime) * integrationtime
                    # Conversion en TimeStamp, regroupement par integration time
                    partition = int(datetime.datetime.fromtimestamp(partts).strftime("%Y%m%d%H%M%S"))
                    # conversion en numerique YYYYMMDDHHMISS

                if flash in ('0', '1'):
                    if partition not in segmented_data[flash]:
                        if organizedbydepth:
                            segmented_data[flash][partition] = {'depth': partition,
                                                                'imgcount': 0,
                                                                'area': {},
                                                                'timestamp': 0}  # 'time':dateheuretxt,
                        else:
                            segmented_data[flash][partition] = {'depth': 0,
                                                                'imgcount': 0,
                                                                'area': {},
                                                                'time': partition}
                    segmented_data[flash][partition]['imgcount'] += 1
                    if organizedbytime:
                        # on va calculer la profondeur moyenne, donc on fait la somme
                        segmented_data[flash][partition]['depth'] += depth
                    else:
                        if dateheure:
                            # on va calculer l'heure' moyenne, donc on fait la somme
                            segmented_data[flash][partition]['timestamp'] += dateheure.timestamp()
                    for data1taille in data:
                        area = int(data1taille[0])
                        if area not in segmented_data[flash][partition]['area']:
                            segmented_data[flash][partition]['area'][area] = []  # tableau=liste des niveaux de gris
                        try:
                            segmented_data[flash][partition]['area'][area].extend(
                                ExplodeGreyLevel(int(data1taille[1]), round(float(data1taille[2])),
                                                 round(float(data1taille[3]))))  # nbr, moyenne,ecarttype
                        except:
                            raise Exception(
                                "{} at row {} data=[{},{},{},{}]".format(sys.exc_info(), rownum, data1taille[0],
                                                                         data1taille[1], data1taille[2],
                                                                         data1taille[3]))

            # logging.info("rowpart={}",rowpart)

        if len(raw_img_depth) == 0:
            raise Exception("No data in particlefile for sample %s " % [UvpSample.profileid])

        logging.info(
            "Raw image count = {0} , Filtered image count = {1} ,  DescentFiltered images={2}".format(
                len(raw_img_depth), len(img_depth), len(raw_img_depth) - len(img_depth) + 1))
        if len(img_depth) == 0:
            raise Exception("No remaining filtered data in dat file")

        GenerateDepthChart(Prj, UvpSample, raw_img_depth, img_depth)
        for flash in ('0', '1'):
            raw_histo_file = GetPathForRawHistoFile(UvpSample.psampleid, flash)
            with bz2.open(raw_histo_file, 'wt', newline='') as f:
                cf = csv.writer(f, delimiter='\t')
                header_cols_name = ["depth", "imgcount", "area", "nbr",
                                    "greylimit1", "greylimit2", "greylimit3", "datetime"]
                cf.writerow(header_cols_name)
                partition_cles = list(segmented_data[flash].keys())
                partition_cles.sort()
                for partition in partition_cles:
                    if organizedbytime:  # calcule la profondeur moyenne de la partition si profil temporel
                        segmented_data[flash][partition]['depth'] = round(
                            segmented_data[flash][partition]['depth'] / segmented_data[flash][partition]['imgcount'], 1)
                    else:
                        segmented_data[flash][partition]['timestamp'] = round(
                            segmented_data[flash][partition]['timestamp'] / segmented_data[flash][partition][
                                'imgcount'],
                            1)
                    for area in segmented_data[flash][partition]['area']:
                        a = np.array(segmented_data[flash][partition]['area'][area])
                        (histo, limits) = np.histogram(a[:, 1], bins=4, weights=a[:, 0])
                        data_row = [segmented_data[flash][partition]['depth'],
                                    segmented_data[flash][partition]['imgcount'], area, histo.sum(), limits[1],
                                    limits[2],
                                    limits[3]]
                        if organizedbytime:  # ajout de l'heure de la partition
                            data_row.append(partition)
                        else:  # ajout de l'heure moyenne de la partition
                            ts = segmented_data[flash][partition]['timestamp']
                            data_row.append(datetime.datetime.fromtimestamp(ts).strftime("%Y%m%d%H%M%S") if ts else '')
                        cf.writerow(data_row)

        UvpSample.histobrutavailable = True
        UvpSample.imp_descent_filtered_row = descent_filter_removed_count
        db.session.commit()


def GenerateRawHistogram(psampleid):
    """
    Génération de l'histogramme particulaire brut stocké dans un fichier tsv bzippé stocké dans le vault.
    :param psampleid:
    :return: None    
    """
    uvp_sample = partdatabase.part_samples.query.filter_by(psampleid=psampleid).first()
    if uvp_sample is None:
        raise Exception("GenerateRawHistogram: Sample %d missing" % psampleid)
    prj = partdatabase.part_projects.query.filter_by(pprojid=uvp_sample.pprojid).first()

    first_image = int(uvp_sample.firstimage)
    last_image = int(uvp_sample.lastimg)
    if last_image >= 999999:
        last_image = None
    depth_offset = prj.default_depthoffset
    if depth_offset is None:
        depth_offset = uvp_sample.acq_depthoffset
    if depth_offset is None:
        depth_offset = 0
    if uvp_sample.organizedbydeepth:
        if prj.enable_descent_filter == 'Y':
            uvp_sample.acq_descent_filter = True
        elif prj.enable_descent_filter == 'N':
            uvp_sample.acq_descent_filter = False
        else:  # si pas explicitement positionné au niveau du projet,
            # on utilise des valeurs par defaut en fonction de l'instrument.
            if prj.instrumtype == 'uvp5':
                uvp_sample.acq_descent_filter = True
            else:
                uvp_sample.acq_descent_filter = False
    else:  # si pas organisé par temps, pas de filtre de descente.
        uvp_sample.acq_descent_filter = False
    descent_filter = uvp_sample.acq_descent_filter
    # Ecart format suivant l'endroit
    # dans result on a comme dans work
    #      1;	20160710164151_998;	00203;00181;00181;00009;02761;02683;00612;01051;00828;00396;00588;00692!;	542;	1;	4;	2;	5;
    # dans work on a ;	00208;00175;00175;00019;02828;02055;00732;01049;00756;00712;00705;00682!;
    #      1;	20160710164151_998;	00203;00181;00181;00009;02761;02683;00612;01051;00828;00396;00588;00692!;	542;	1;	4;	2;	5;
    # 12 colonnes au lieu de 1
    # alors que dans RAW on a ;	00208*00175*00175*00019*02828*02055*00732*01049*00756*00712*00705*00682!;
    #      1;	20160628160507_071;	00203*00180*00180*00012*02611*02766*01125*00898*00655*00752*00786*00791!;	1289;	1;	7;	1;	10;
    # Nom du fichier dans raw : HDR20160710164150/HDR20160710164150_000.dat
    # Nom du fichier dans work ge_2016_202/HDR20160710164150.dat , un fichier unique
    # Nom du fichier dans result ge_2016_202_datfile.txt, un fichier unique
    # le changement de format n'as pas d'impact car seule les 3 premières colonnes sont utilisées et c'est le format de la 3eme qui change
    # dans l'instrument on ne se sert que de la première valeurs donc le découpage suivant * et la prise de la première valeur donne le même résultat.
    server_root = app.ServerLoadArea
    dossier_uvp_path = server_root / prj.rawfolder
    path_dat = dossier_uvp_path / 'results' / (uvp_sample.profileid + "_datfile.txt")
    ecodata_part_file = dossier_uvp_path / "ecodata" / uvp_sample.profileid / (uvp_sample.profileid + "_Particule.zip")
    if ecodata_part_file.exists():
        GenerateRawHistogramUVPAPP(uvp_sample, prj, depth_offset, uvp_sample.organizedbydeepth,
                                   descent_filter, ecodata_part_file)
        return

    if path_dat.exists():
        lst_fichiers = [path_dat]
    else:
        path_dat = dossier_uvp_path / 'work' / uvp_sample.profileid / ('HDR' + uvp_sample.filename + ".dat")
        if path_dat.exists():
            lst_fichiers = [path_dat]
        else:
            # Le sorted n'as pas l'air necessaire d'après les essais sous windows, mais glob ne garanti pas l'ordre
            lst_fichiers = sorted(list(
                (dossier_uvp_path / 'raw' / ('HDR' + uvp_sample.filename)).glob('HDR' + uvp_sample.filename + "*.dat")))
    # print(lst_fichiers)
    raw_img_depth = {}  # version non filtrée utilisée pour générer le graphique
    img_depth = {}  # version filtrée
    img_time = {}  # heure des images
    last_image_idx = last_image_depth = None
    if DEV_BEHAVIOR:
        if len(lst_fichiers) == 0:
            raise Exception("No dat files")
    fichier = None
    for fichier in lst_fichiers:
        logging.info("Processing file " + fichier.as_posix())
        with fichier.open(encoding='latin_1') as csvfile:
            rdr = csv.reader(csvfile, delimiter=';')
            next(rdr)  # au saute la ligne de titre
            for row in rdr:
                idx = row[0].strip("\t ")
                instrumdata = row[2].strip("\t ")
                if idx == "" or instrumdata == "":
                    continue
                idx = int(idx)
                instrumdata = instrumdata.split('*')
                depth = float(instrumdata[0]) * 0.1 + depth_offset
                if (not math.isnan(depth)) and (depth < 0):
                    depth = 0  # les profondeur négatives sont forcées à 0
                raw_img_depth[idx] = depth
                if idx < first_image:
                    continue
                img_time[idx] = row[1][0:14]
                if last_image is None:  # On détermine la dernière image si elle n'est pas determinée
                    # si le filtre de descente n'est pas actif on considère toujours la derniere image
                    if descent_filter == False and (last_image_idx is None or idx > last_image_idx):
                        last_image_idx = idx
                    elif last_image_depth is None or depth > last_image_depth:
                        last_image_depth = depth
                        last_image_idx = idx
    if last_image is None:
        last_image = last_image_idx
    if len(raw_img_depth) == 0:
        raise Exception("No data in dat file %s " % (fichier.as_posix()))
    prev_depth = 0
    descent_filter_removed_count = 0
    # Application du filtre en descente
    for i in range(first_image, last_image + 1):
        if i not in raw_img_depth:
            continue
        keep_line = True
        if descent_filter:
            if raw_img_depth[i] < prev_depth:
                keep_line = False
            else:
                prev_depth = raw_img_depth[i]
        if keep_line:
            img_depth[i] = raw_img_depth[i]
        else:
            descent_filter_removed_count += 1
    logging.info(
        "Raw image count = {0} , Filtered image count = {1} , LastIndex= {2},LastIndex-First+1= {4}, DescentFiltered "
        "images={3} ".format(len(raw_img_depth),
                             len(img_depth), last_image, last_image - first_image - len(img_depth) + 1,
                             last_image - first_image + 1))
    if len(img_depth) == 0:
        raise Exception("No remaining filtered data in dat file")

    depth_bin_count = GenerateDepthChart(prj, uvp_sample, raw_img_depth, img_depth)
    # Ecart format suivant l'endroit
    # Dans results nom = p1604_13.bru toujours au format bru1 malgré l'extension bru fichier unique
    # dans work p1604_13/p1604_13.bru toujours au format bru1 malgré l'extension bru fichier unique
    # dans raw HDR20160429180115/HDR20160429180115_000.bru ou bru1
    # chargement des données particulaires
    logging.info("Processing BRU Files:")
    path_bru = dossier_uvp_path / 'results' / (uvp_sample.profileid + ".bru")
    if path_bru.exists():
        bru_format = "bru1"
        lst_fichiers = [path_bru]
    else:
        path_bru = dossier_uvp_path / 'work' / uvp_sample.profileid / (uvp_sample.profileid + ".bru")
        if path_bru.exists():
            bru_format = "bru1"
            lst_fichiers = [path_bru]
        else:
            lst_fichiers = list(
                (dossier_uvp_path / 'raw' / ('HDR' + uvp_sample.filename)).glob('HDR' + uvp_sample.filename + "*.bru"))
            if len(lst_fichiers) > 0:
                bru_format = "bru"
            else:
                lst_fichiers = list(
                    (dossier_uvp_path / 'raw' / ('HDR' + uvp_sample.filename)).glob('HDR' + uvp_sample.filename
                                                                                    + "*.bru1"))
                bru_format = "bru1"
    # logging.info(lst_fichiers)
    segmented_data = {}  # version filtrée
    for fichier in lst_fichiers:
        logging.info("Processing file " + fichier.as_posix())
        with fichier.open(encoding='latin_1') as csvfile:
            rdr = csv.reader(csvfile, delimiter=';')
            next(rdr)  # au saute la ligne de titre
            for row in rdr:
                idx = int(row[0].strip("\t "))
                if idx not in img_depth:
                    continue  # c'est sur une image filtrée, on ignore
                if bru_format == 'bru':
                    area = int(row[3].strip("\t "))
                    grey = int(row[4].strip("\t "))
                elif bru_format == 'bru1':
                    area = int(row[2].strip("\t "))
                    grey = int(row[3].strip("\t "))
                else:
                    raise Exception("Invalid file extension")
                # calcule la partition en sections de 5m depuis le minimum
                depth = math.floor(img_depth[idx])
                partition = depth
                if partition not in segmented_data:
                    segmented_data[partition] = {'depth': depth, 'time': img_time[idx],
                                                 'imgcount': depth_bin_count[partition], 'area': {}}
                if area not in segmented_data[partition]['area']:
                    segmented_data[partition]['area'][area] = []  # tableau=liste des niveaux de gris
                segmented_data[partition]['area'][area].append(grey)

    raw_histo_file = GetPathForRawHistoFile(psampleid)
    import bz2
    with bz2.open(raw_histo_file, 'wt', newline='') as f:
        cf = csv.writer(f, delimiter='\t')
        cf.writerow(["depth", "imgcount", "area", "nbr", "greylimit1", "greylimit2", "greylimit3"])
        for partition, PartitionContent in segmented_data.items():
            for area, greydata in PartitionContent['area'].items():
                # if area in ('depth', 'time'): continue  # ces clés sont au même niveau que les area
                agreydata = np.asarray(greydata)
                # ça ne gère pas l'organisation temporelle des données
                cf.writerow([PartitionContent['depth'], PartitionContent['imgcount'], area, len(agreydata),
                             np.percentile(agreydata, 25, interpolation='lower'),
                             np.percentile(agreydata, 50, interpolation='lower'),
                             np.percentile(agreydata, 75, interpolation='higher')]
                            )
    uvp_sample.histobrutavailable = True
    uvp_sample.lastimgused = last_image
    uvp_sample.imp_descent_filtered_row = descent_filter_removed_count
    db.session.commit()


def GenerateDepthChart(Prj, UvpSample, raw_img_depth, ImgDepth):
    font = {'family': 'arial', 'weight': 'normal', 'size': 10}
    plt.rc('font', **font)
    plt.rcParams['lines.linewidth'] = 0.5
    fig = plt.figure(figsize=(8, 10), dpi=100)
    # 2 lignes, 3 colonnes, graphique en haut à gauche trace de la courbe de descente
    # ax = fig.add_subplot(231)
    ax = plt.axes()
    a_raw_img_depth = np.empty([len(raw_img_depth), 2])
    for i, (idx, dept) in enumerate(sorted(raw_img_depth.items(), key=lambda r: r[0])):
        a_raw_img_depth[i] = idx, dept
    # Courbe bleu des données brutes
    ax.plot(a_raw_img_depth[:, 0], -a_raw_img_depth[:, 1])
    ax.set_xlabel('Image nb')
    ax.set_ylabel('Depth(m)')
    ax.set_xticks(np.arange(0, a_raw_img_depth[:, 0].max(), 5000))
    # noinspection PyUnusedLocal
    # libère la mémoire des données brutes, elle ne sont plus utile une fois le graphe tracé
    a_raw_img_depth = raw_img_depth = None
    # courbe rouge des données réduites à first==>Last et filtrées
    a_filtered_img_depth = np.empty([len(ImgDepth), 2])
    for i, (idx, dept) in enumerate(sorted(ImgDepth.items(), key=lambda r: r[0])):
        a_filtered_img_depth[i] = idx, dept
    ax.plot(a_filtered_img_depth[:, 0], -a_filtered_img_depth[:, 1], 'r')
    min_depth = a_filtered_img_depth[:, 1].min()
    max_depth = a_filtered_img_depth[:, 1].max()
    # Calcule le nombre d'image par mettre à partir de 0m
    depth_bin_count = np.bincount(np.floor(a_filtered_img_depth[:, 1]).astype('int'))
    # noinspection PyUnusedLocal
    a_filtered_img_depth = None  # version nparray plus necessaire.
    logging.info("Depth range= {0}->{1}".format(min_depth, max_depth))
    # fig.savefig((DossierUVPPath / 'results' / ('ecotaxa_depth_' + UvpSample.profileid+'.png')).as_posix())
    fig.text(0.05, 0.98,
             "Project : %s , Profile %s , Filename : %s" % (Prj.ptitle, UvpSample.profileid, UvpSample.filename),
             ha='left')
    fig.tight_layout(rect=(0, 0, 1, 0.98))  # permet de laisser un peu de blanc en haut pour le titre
    fig.savefig(GetPathForImportGraph(UvpSample.psampleid, 'depth'))
    fig.clf()
    return depth_bin_count


def GenerateParticleHistogram(psampleid):
    """
    Génération de l'histogramme particulaire détaillé (45 classes) et réduit (15 classes) à partir de l'histogramme détaillé
    :param psampleid:
    :return:
    """
    uvp_sample = partdatabase.part_samples.query.filter_by(psampleid=psampleid).first()
    if uvp_sample is None:
        raise Exception("GenerateParticleHistogram: Sample %d missing" % psampleid)
    if not uvp_sample.histobrutavailable:
        raise Exception(
            "GenerateParticleHistogram: Sample %d Particle Histogram can't be computed without Raw histogram"
            % psampleid)
    prj = partdatabase.part_projects.query.filter_by(pprojid=uvp_sample.pprojid).first()
    first_image = uvp_sample.firstimage
    last_image = uvp_sample.lastimgused
    if DEV_BEHAVIOR:
        # Juste utilisé sur les organizedbydeepth ou time déclarée pour supprimer warning
        time_par_tranche = depth_par_tranche = heure_debut = None
    # Si aucune determinée lors de la génération de l'histogramme brut, on prend celle spécifiée dans le sample.
    if last_image is None:
        last_image = uvp_sample.lastimg
    if first_image is None or last_image is None:
        raise Exception("GenerateParticuleHistogram sample %s first or last image undefined %s-%s" % (
            uvp_sample.profileid, first_image, last_image))

    det_histo_file = GetPathForRawHistoFile(psampleid)
    logging.info("GenerateParticleHistogram processing raw histogram file  %s" % det_histo_file)
    # format de raw 0:depth, 1:imgcount, 2:area, 3:nbr, 4:greylimit1, 5:greylimit2, 6:greylimit3, 7:Heure(optionnel)
    part = np.loadtxt(det_histo_file, delimiter='\t', skiprows=1)
    if DEV_BEHAVIOR:
        # ESD en mm (diametre équivalent sphérique) calculé à partir de l'area
        part_esd = 2 * np.sqrt((pow(part[:, 2], uvp_sample.acq_exp) * uvp_sample.acq_aa) / np.pi)
        # BV en mm3 , utiliser l'ESD et la nombre de particule
        part_bv = part[:, 3] * pow(part_esd / 2, 3) * 4 * math.pi / 3
    if uvp_sample.organizedbydeepth:
        # 1 Ligne par mètre et area, ne contient les données entre fist et last
        min_depth = part[:, 0].min()
        if DEV_BEHAVIOR:
            part_tranche = part[:, 0] // 5  # calcul de la tranche 0 pour [0m..5m[,1 pour [5m..10m[
            last_tranche = part_tranche.max()
            date_conv_dict = {}
            if part.shape[1] > 7:  # s'il y a une colonne des heures on les convertis en TimeStamp
                for i in range(part.shape[0]):
                    if part[i, 7]:
                        dateint = int(part[i, 7])
                        if dateint not in date_conv_dict:
                            date_conv_dict[dateint] = datetime.datetime.strptime(str(dateint),
                                                                                 "%Y%m%d%H%M%S").timestamp()
                        part[i, 7] = date_conv_dict[dateint]
        else:
            # ajout d'attributs calculés pour chaque ligne du fichier.
            part_tranche = np.empty([part.shape[0], 3])  # col0 = tranche, Col1=ESD, Col2=Biovolume en µl=mm3
            part_tranche[:, 0] = part[:, 0] // 5  # calcul de la tranche 0 pour [0m..5m[,1 pour [5m..10m[
            part_tranche[:, 1] = 2 * np.sqrt((pow(part[:, 2], uvp_sample.acq_exp) * uvp_sample.acq_aa) / np.pi)
            part_tranche[:, 2] = part[:, 3] * pow(part_tranche[:, 1] / 2, 3) * 4 * math.pi / 3
            last_tranche = part_tranche[:, 0].max()
        # on récupere les 1ère ligne de chaque mètre afin de calculer le volume d'eau
        first_lig_by_depth = part[np.unique(part[:, 0], return_index=True)[1]]
        # on calcule le volume de chaque tranche (y compris celle qui n'existent pas en 0 et la profondeur maxi)
        # Bin par tranche de tranche 5m partant de 0m
        volume_par_tranche = np.bincount((first_lig_by_depth[:, 0] // 5).astype(int),
                                         first_lig_by_depth[:, 1]) * uvp_sample.acq_volimage
        # Bin par tranche de tranche 5m partant de 0m
        metre_par_tranche = np.bincount((first_lig_by_depth[:, 0] // 5).astype(int))
        # On supprime les tranches vides, mais ça fait planter les graphes suivants
        # volume_par_tranche=volume_par_tranche[np.nonzero(volume_par_tranche)]
        # metre_par_tranche = metre_par_tranche[np.nonzero(volume_par_tranche)]
        if DEV_BEHAVIOR:
            if part.shape[1] > 7:
                time_par_tranche = np.bincount((first_lig_by_depth[:, 0] // 5).astype(np.int32),
                                               first_lig_by_depth[:, 7]) / np.bincount(
                    (first_lig_by_depth[:, 0] // 5).astype(np.int32))
            else:
                time_par_tranche = np.zeros([part.shape[0]])

    else:  # calcul des histogramme temporels
        # format de raw 0:depth,1:imgcount,2:area,3:nbr,4:greylimit1,5:greylimit2,6:greylimit3
        # ,7:YYYYMMDDHHMISS en decimal arrondi à la resolution integrationtime
        # 1 Ligne par mètre et area, ne contient les données entre fist et last
        min_depth = part[:, 0].min()
        # ajout d'attributs calculés pour chaque ligne du fichier.
        # col0 = tranche, Col1=ESD, Col2=Biovolume en µl=mm3
        if DEV_BEHAVIOR:
            # utile seulement pour les graphes depth, cette ligne permet d'éviter des warnings
            metre_par_tranche = last_tranche = None
            # ajout d'attributs calculés pour chaque ligne du fichier.
            part_tranche = np.empty([part.shape[0]])
        else:
            part_tranche = np.empty([part.shape[0], 3])
        date_conv_dict = {}
        for i in range(part.shape[0]):
            dateint = int(part[i, 7])
            if dateint not in date_conv_dict:
                date_conv_dict[dateint] = datetime.datetime.strptime(str(dateint), "%Y%m%d%H%M%S").timestamp() // 3600
            if DEV_BEHAVIOR:
                part_tranche[i] = date_conv_dict[dateint]
            else:
                part_tranche[i, 0] = date_conv_dict[dateint]
        if DEV_BEHAVIOR:
            ts_heure_debut = np.min(part_tranche)
        else:
            ts_heure_debut = np.min(part_tranche[:, 0])
        heure_debut = datetime.datetime.fromtimestamp(ts_heure_debut * 3600)
        if DEV_BEHAVIOR:
            part_tranche -= ts_heure_debut  # contient Le N° de tranche temporelle relatif 0= 1ère tranche, 1=1h plus tard
        else:
            part_tranche[:, 0] -= ts_heure_debut  # contient Le N° de tranche temporelle relatif...
            # ... 0= 1ère tranche, 1=1h plus tard
            part_tranche[:, 1] = 2 * np.sqrt((pow(part[:, 2], uvp_sample.acq_exp) * uvp_sample.acq_aa) / np.pi)
            part_tranche[:, 2] = part[:, 3] * pow(part_tranche[:, 1] / 2, 3) * 4 * math.pi / 3
        # on récupere les 1ère ligne de chaque tranche temporelle originale
        first_lig_id_by_image = np.unique(part[:, 7], return_index=True)[1]
        # on calcule le volume de chaque tranche
        # , y compris celle qui n'existent pas (bincount génère tous les pas entre 0 et la MaxTrancheId)
        # Bin par tranche de 1h
        if DEV_BEHAVIOR:
            volume_par_tranche = np.bincount((part_tranche[first_lig_id_by_image]).astype(np.int32),
                                             part[first_lig_id_by_image, 1]) * uvp_sample.acq_volimage
            depth_par_tranche = np.bincount((part_tranche[first_lig_id_by_image]).astype(np.int32),
                                            part[first_lig_id_by_image, 0]) / np.bincount(
                (part_tranche[first_lig_id_by_image]).astype(np.int32))
        else:
            volume_par_tranche = np.bincount((part_tranche[first_lig_id_by_image, 0]).astype(np.int32),
                                             part[first_lig_id_by_image, 1]) * uvp_sample.acq_volimage
            depth_par_tranche = np.bincount((part_tranche[first_lig_id_by_image, 0]).astype(np.int32),
                                            part[first_lig_id_by_image, 0]) / np.bincount(
                (part_tranche[first_lig_id_by_image, 0]).astype(np.int32))

    # On arrondit les volumes avant de s'en servir comme base pour les autres calculs
    volume_par_tranche = np.round(volume_par_tranche, decimals=VOLUME_ROUNDING)

    # les calculs de concentration sont communs aux 2 types de profils
    if DEV_BEHAVIOR:
        pass
    else:
        part_esd = part_tranche[:, 1]
        part_bv = part_tranche[:, 2]
        sav_part_tranche = part_tranche
        part_tranche = part_tranche[:, 0]
    (PartByClassAndTranche, bins, binsdept) = \
        np.histogram2d(part_esd, part_tranche,
                       bins=(PartDetClassLimit, np.arange(0, volume_par_tranche.shape[0] + 1)),
                       weights=part[:, 3])
    (BioVolByClassAndTranche, bins, binsdept) = \
        np.histogram2d(part_esd, part_tranche,
                       bins=(PartDetClassLimit, np.arange(0, volume_par_tranche.shape[0] + 1)),
                       weights=part_bv)
    with np.errstate(divide='ignore',
                     invalid='ignore'):  # masque les warning provoquées par les divisions par 0 des tranches vides.
        BioVolByClassAndTranche /= volume_par_tranche

    font = {'family': 'arial',
            'weight': 'normal',
            'size': 10}
    plt.rc('font', **font)
    plt.rcParams['lines.linewidth'] = 0.5

    fig = plt.figure(figsize=(16, 12), dpi=100, )

    if DEV_BEHAVIOR:
        pos_col_name = 'posP' if uvp_sample.organizedbydeepth else 'posT'
        # Calcul des graphes Particle
        graphes = [
            {'filtre': np.argwhere(part_esd <= 0.53),
             "label": 'part 0.06-0.53 mm esd # l-1', 'posT': 422, 'posP': 242},
            {'filtre': np.argwhere((part_esd >= 0.53) & (part_esd <= 1.06)),
             "label": 'part 0.53-1.06 mm esd # l-1', 'posT': 423, 'posP': 243},
            {'filtre': np.argwhere((part_esd >= 1.06) & (part_esd <= 2.66)),
             "label": 'part 1.06-2.66 mm esd # l-1', 'posT': 424, 'posP': 244},
        ]
        for G in graphes:
            ax = fig.add_subplot(G[pos_col_name])
            (n, bins) = np.histogram(part_tranche[G['filtre']], np.arange(len(volume_par_tranche) + 1),
                                     weights=part[G['filtre'], 3])
            with np.errstate(divide='ignore',
                             invalid='ignore'):  # masque les warning provoquées par les divisions par 0 des tranches vides.
                n = n / volume_par_tranche
            ax.set_yticks(GetTicks(n.max()))
            if uvp_sample.organizedbydeepth:
                ax.plot(n, bins[:-1] * -5 - min_depth - 2.5)
                ax.set_xticks(GetTicks(n.max()))
                ax.set_xlabel(G['label'])
                ax.set_ylabel('Depth(m)')
            else:
                ax.plot(np.arange(len(volume_par_tranche)) + 0.5, n)
                ax.set_ylabel(G['label'])

        # Calcul Biovolume & # Particle via histograme
        graphes = [
            {'data': np.sum(BioVolByClassAndTranche[28:30, :], axis=0),
             "label": 'part >=0.512-<1.02 mm esd mm3 l-1', 'posT': 425, 'posP': 245},
            {'data': np.sum(PartByClassAndTranche[0:28, :], axis=0) / volume_par_tranche,
             "label": 'part <0.512 mm esd # l-1', 'posT': 426, 'posP': 246},
            {'data': np.sum(PartByClassAndTranche[28:30, :], axis=0) / volume_par_tranche,
             "label": 'part >=0.512-<1.02 mm esd # l-1', 'posT': 427, 'posP': 247},
            {'data': np.sum(PartByClassAndTranche[30:34, :], axis=0) / volume_par_tranche,
             "label": 'part >=1.02-<2.58 mm esd # l-1', 'posT': 428, 'posP': 248},
        ]
        for G in graphes:
            ax = fig.add_subplot(G[pos_col_name])
            if uvp_sample.organizedbydeepth:
                ax.plot(G['data'], np.arange(0, last_tranche + 1) * -5 - 2.5)
                ax.set_xticks(GetTicks(n.max()))
                ax.set_xlabel(G['label'])
                ax.set_ylabel('Depth(m)  from det histo')
            else:
                ax.plot(np.arange(len(volume_par_tranche)) + 0.5, G['data'])
                ax.set_yticks(GetTicks(G['data'].max()))
                ax.set_ylabel(G['label'])
                ax.set_xlabel('Time(h) from det histo')

        if uvp_sample.organizedbydeepth:
            # calcul volume par metre moyen de chaque tranche
            ax = fig.add_subplot(241)
            # si une tranche n'as pas été entierement explorée la /5 est un calcul éronné
            with np.errstate(divide='ignore',
                             invalid='ignore'):  # masque les warning provoquées par les divisions par 0 des tranches vides.
                ax.plot(volume_par_tranche / metre_par_tranche, np.arange(len(volume_par_tranche)) * -5 - 2.5)
            ax.set_xticks(GetTicks((volume_par_tranche / 5).max()))
            ax.set_xlabel('Volume/M')
            ax.set_ylabel('Depth(m)')

        else:
            # calcul volume par metre moyen de chaque tranche
            ax = fig.add_subplot(421)
            ax.plot(np.arange(len(volume_par_tranche)) + 0.5, volume_par_tranche)
            ax.set_yticks(GetTicks(volume_par_tranche.max()))
            ax.set_ylabel('Volume')
    else:
        part_tranche = sav_part_tranche
        if uvp_sample.organizedbydeepth:
            # calcul volume par metre moyen de chaque tranche
            ax = fig.add_subplot(241)
            # si une tranche n'as pas été entierement explorée la /5 est un calcul éronné
            with np.errstate(divide='ignore',
                             invalid='ignore'):  # masque les warning provoquées par les divisions par 0 des tranches vides.
                ax.plot(volume_par_tranche / metre_par_tranche, np.arange(len(volume_par_tranche)) * -5 - 2.5)
            ax.set_xticks(GetTicks((volume_par_tranche / 5).max()))
            ax.set_xlabel('Volume/M')
            ax.set_ylabel('Depth(m)')

            # Calcul Particle <=0.53
            Filtre = np.argwhere(part_tranche[:, 1] <= 0.53)
            ax = fig.add_subplot(242)
            (n, bins) = np.histogram(part_tranche[Filtre, 0], np.arange(len(volume_par_tranche) + 1),
                                     weights=part[Filtre, 3])
            with np.errstate(divide='ignore',
                             invalid='ignore'):  # masque les warning provoquées par les divisions par 0 des tranches vides.
                n = n / volume_par_tranche
            ax.plot(n, bins[:-1] * -5 - min_depth - 2.5)
            ax.set_xticks(GetTicks(n.max()))

            ax.set_xlabel('Part 0.06-0.53 mm esd # l-1')
            ax.set_ylabel('Depth(m)')

            # Calcul Particle 0.53->1.06
            Filtre = np.argwhere((part_tranche[:, 1] >= 0.53) & (part_tranche[:, 1] <= 1.06))
            ax = fig.add_subplot(243)
            (n, bins) = np.histogram(part_tranche[Filtre, 0], np.arange(len(volume_par_tranche) + 1),
                                     weights=part[Filtre, 3])
            with np.errstate(divide='ignore',
                             invalid='ignore'):  # masque les warning provoquées par les divisions par 0 des tranches vides.
                n = n / volume_par_tranche
            ax.plot(n, bins[:-1] * -5 - min_depth - 2.5)
            ax.set_xticks(GetTicks(n.max()))
            ax.set_xlabel('Part 0.53-1.06 mm esd # l-1')
            ax.set_ylabel('Depth(m)')

            # Calcul Particle 1.06->2.66
            Filtre = np.argwhere((part_tranche[:, 1] >= 1.06) & (part_tranche[:, 1] <= 2.66))
            ax = fig.add_subplot(244)
            (n, bins) = np.histogram(part_tranche[Filtre, 0], np.arange(len(volume_par_tranche) + 1),
                                     weights=part[Filtre, 3])
            with np.errstate(divide='ignore',
                             invalid='ignore'):  # masque les warning provoquées par les divisions par 0 des tranches vides.
                n = n / volume_par_tranche
            ax.plot(n, bins[:-1] * -5 - min_depth - 2.5)
            ax.set_xticks(GetTicks(n.max()))
            ax.set_xlabel('Part 1.06-2.66 mm esd # l-1')
            ax.set_ylabel('Depth(m)')

            # Calcul Biovolume Particle >0.512-<=1.02 mm via histograme
            n = np.sum(BioVolByClassAndTranche[28:30, :], axis=0)
            ax = fig.add_subplot(245)
            ax.plot(n, np.arange(0, last_tranche + 1) * -5 - 2.5)
            ax.set_xticks(GetTicks(n.max()))
            ax.set_xlabel('Part >=0.512-<1.02 mm esd mm3 l-1 from det histo')
            ax.set_ylabel('Depth(m)')

            # Calcul Particle <=0.512 mm via histograme
            n = np.sum(PartByClassAndTranche[0:28, :], axis=0)
            ax = fig.add_subplot(246)
            with np.errstate(divide='ignore',
                             invalid='ignore'):  # masque les warning provoquées par les divisions par 0 des tranches vides.
                n = n / volume_par_tranche
            ax.plot(n, np.arange(0, last_tranche + 1) * -5 - 2.5)
            ax.set_xticks(GetTicks(n.max()))
            ax.set_xlabel('Part <0.512 mm esd # l-1 from det histo')
            ax.set_ylabel('Depth(m)')

            # Calcul Particle >0.512-<=1.02 mm via histograme
            n = np.sum(PartByClassAndTranche[28:30, :], axis=0)
            ax = fig.add_subplot(247)
            with np.errstate(divide='ignore',
                             invalid='ignore'):  # masque les warning provoquées par les divisions par 0 des tranches vides.
                n = n / volume_par_tranche
            ax.plot(n, np.arange(0, last_tranche + 1) * -5 - 2.5)
            ax.set_xticks(GetTicks(n.max()))
            ax.set_xlabel('Part >=0.512-<1.02 mm esd # l-1 from det histo')
            ax.set_ylabel('Depth(m)')

            # Calcul Particle >0.512-<=1.02 mm via histograme
            n = np.sum(PartByClassAndTranche[30:34, :], axis=0)
            ax = fig.add_subplot(248)
            with np.errstate(divide='ignore',
                             invalid='ignore'):  # masque les warning provoquées par les divisions par 0 des tranches vides.
                n = n / volume_par_tranche
            ax.plot(n, np.arange(0, last_tranche + 1) * -5 - 2.5)
            ax.set_xticks(GetTicks(n.max()))
            ax.set_xlabel('Part >=1.02-<2.58 mm esd # l-1 from det histo')
            ax.set_ylabel('Depth(m)')
        else:
            # calcul volume par metre moyen de chaque tranche
            ax = fig.add_subplot(421)
            # si une tranche n'as pas été entierement explorée la /5 est un calcul éronné
            ax.plot(np.arange(len(volume_par_tranche)) + 0.5, volume_par_tranche)
            ax.set_yticks(GetTicks(volume_par_tranche.max()))
            ax.set_ylabel('Volume')

            # Calcul Particle <=0.53
            graphes = [
                {'filtre': np.argwhere(part_tranche[:, 1] <= 0.53), "label": 'Part 0.06-0.53 mm esd # l-1', 'pos': 422},
                {'filtre': np.argwhere((part_tranche[:, 1] >= 0.53) & (part_tranche[:, 1] <= 1.06)),
                 "label": 'Part 0.53-1.06 mm esd # l-1', 'pos': 423},
                {'filtre': np.argwhere((part_tranche[:, 1] >= 1.06) & (part_tranche[:, 1] <= 2.66)),
                 "label": 'Part 1.06-2.66 mm esd # l-1', 'pos': 424},
            ]
            for G in graphes:
                ax = fig.add_subplot(G['pos'])
                (n, bins) = np.histogram(part_tranche[G['filtre'], 0], np.arange(len(volume_par_tranche) + 1),
                                         weights=part[G['filtre'], 3])
                with np.errstate(divide='ignore',
                                 invalid='ignore'):  # masque les warning provoquées par les divisions par 0 des tranches vides.
                    n = n / volume_par_tranche
                ax.plot(np.arange(len(volume_par_tranche)) + 0.5, n)
                ax.set_yticks(GetTicks(n.max()))
                ax.set_ylabel(G['label'])

            # Calcul Biovolume Particle >0.512-<=1.02 mm via histograme
            graphes = [
                {'data': np.sum(BioVolByClassAndTranche[28:30, :], axis=0),
                 "label": 'Part >=0.512-<1.02 mm esd mm3 l-1',
                 'pos': 425},
                {'data': np.sum(PartByClassAndTranche[0:28, :], axis=0) / volume_par_tranche,
                 "label": 'Part <0.512 mm esd # l-1', 'pos': 426},
                {'data': np.sum(PartByClassAndTranche[28:30, :], axis=0) / volume_par_tranche,
                 "label": 'Part >=0.512-<1.02 mm esd # l-1', 'pos': 427},
                {'data': np.sum(PartByClassAndTranche[30:34, :], axis=0) / volume_par_tranche,
                 "label": 'Part >=1.02-<2.58 mm esd # l-1', 'pos': 428},
            ]
            for G in graphes:
                ax = fig.add_subplot(G['pos'])
                ax.plot(np.arange(len(volume_par_tranche)) + 0.5, G['data'])
                ax.set_yticks(GetTicks(G['data'].max()))
                ax.set_xlabel('Time(h) from det histo')
                ax.set_ylabel(G['label'])

    # Fig.savefig((DossierUVPPath / 'results' / ('ecotaxa_particle_' + UvpSample.profileid+'.png')).as_posix())
    fig.text(0.05, 0.99,
             "Project : %s , Profile %s , Filename : %s" % (prj.ptitle, uvp_sample.profileid, uvp_sample.filename),
             ha='left')
    fig.tight_layout(rect=(0, 0, 1, 0.99))  # permet de laisser un peu de blanc en haut pour le titre
    fig.savefig(GetPathForImportGraph(psampleid, 'particle'))
    fig.clf()

    ExecSQL("delete from part_histopart_det where psampleid=" + str(psampleid))
    sql = """insert into part_histopart_det(psampleid, lineno, depth,  watervolume,datetime
        , class01, class02, class03, class04, class05, class06, class07, class08, class09, class10, class11, class12
        , class13, class14, class15, class16, class17, class18, class19, class20, class21, class22, class23, class24
        , class25, class26, class27, class28, class29, class30, class31, class32, class33, class34, class35, class36
        , class37, class38, class39, class40, class41, class42, class43, class44, class45
        , biovol01, biovol02, biovol03, biovol04, biovol05, biovol06, biovol07, biovol08, biovol09, biovol10, biovol11
        , biovol12, biovol13, biovol14, biovol15, biovol16, biovol17, biovol18, biovol19, biovol20, biovol21, biovol22
        , biovol23, biovol24, biovol25, biovol26, biovol27, biovol28, biovol29, biovol30, biovol31, biovol32, biovol33
        , biovol34, biovol35, biovol36, biovol37, biovol38, biovol39, biovol40, biovol41, biovol42, biovol43, biovol44
        , biovol45        )
    values(%(psampleid)s,%(lineno)s,%(depth)s,%(watervolume)s,%(datetime)s
    ,%(class01)s,%(class02)s,%(class03)s,%(class04)s,%(class05)s,%(class06)s
    ,%(class07)s,%(class08)s,%(class09)s,%(class10)s,%(class11)s,%(class12)s,%(class13)s,%(class14)s,%(class15)s
    ,%(class16)s,%(class17)s,%(class18)s,%(class19)s,%(class20)s,%(class21)s,%(class22)s,%(class23)s,%(class24)s
    ,%(class25)s,%(class26)s,%(class27)s,%(class28)s,%(class29)s,%(class30)s,%(class31)s,%(class32)s,%(class33)s
    ,%(class34)s,%(class35)s,%(class36)s,%(class37)s,%(class38)s,%(class39)s,%(class40)s,%(class41)s,%(class42)s
    ,%(class43)s,%(class44)s,%(class45)s
    ,%(biovol01)s,%(biovol02)s,%(biovol03)s,%(biovol04)s,%(biovol05)s,%(biovol06)s
    ,%(biovol07)s,%(biovol08)s,%(biovol09)s,%(biovol10)s,%(biovol11)s,%(biovol12)s,%(biovol13)s,%(biovol14)s
    ,%(biovol15)s,%(biovol16)s,%(biovol17)s    ,%(biovol18)s,%(biovol19)s,%(biovol20)s,%(biovol21)s,%(biovol22)s
    ,%(biovol23)s,%(biovol24)s,%(biovol25)s,%(biovol26)s,%(biovol27)s,%(biovol28)s,%(biovol29)s,%(biovol30)s
    ,%(biovol31)s,%(biovol32)s,%(biovol33)s,%(biovol34)s,%(biovol35)s,%(biovol36)s,%(biovol37)s,%(biovol38)s
    ,%(biovol39)s,%(biovol40)s,%(biovol41)s,%(biovol42)s,%(biovol43)s,%(biovol44)s,%(biovol45)s
    )"""
    sqlparam = {'psampleid': psampleid}
    for i, r in enumerate(volume_par_tranche):
        sqlparam['lineno'] = i
        if uvp_sample.organizedbydeepth:
            sqlparam['depth'] = (i * 5 + 2.5)
            if DEV_BEHAVIOR:
                if time_par_tranche[i] and time_par_tranche[i] != np.NaN:
                    sqlparam['datetime'] = datetime.datetime.fromtimestamp(int(time_par_tranche[i]))
                else:
                    sqlparam['datetime'] = None
            else:
                sqlparam['datetime'] = None
        else:
            sqlparam['depth'] = round(depth_par_tranche[i], 1)
            sqlparam['datetime'] = heure_debut + datetime.timedelta(hours=i, minutes=30)
        # On ne charge pas les lignes sans volume d'eau car ça signifie qu'l n'y a pas eu d'échantillon
        if volume_par_tranche[i] == 0:
            continue
        sqlparam['watervolume'] = volume_par_tranche[i]
        for k in range(0, 45):
            sqlparam['class%02d' % (k + 1)] = PartByClassAndTranche[k, i]
        for k in range(0, 45):
            sqlparam['biovol%02d' % (k + 1)] = BioVolByClassAndTranche[k, i]
        ExecSQL(sql, sqlparam)

    GenerateReducedParticleHistogram(psampleid)


def GenerateTaxonomyHistogram(ecotaxa_if: EcoTaxaInstance, psampleid):
    """
    Génération de l'histogramme Taxonomique 
    :param psampleid:
    :return:
    """
    uvp_sample = partdatabase.part_samples.query.filter_by(psampleid=psampleid).first()
    if uvp_sample is None:
        raise Exception("GenerateTaxonomyHistogram: Sample %d missing" % psampleid)
    prj = partdatabase.part_projects.query.filter_by(pprojid=uvp_sample.pprojid).first()
    if uvp_sample.sampleid is None:
        raise Exception("GenerateTaxonomyHistogram: EcoTaxa sampleid is required in Sample %d " % psampleid)
    pixel = uvp_sample.acq_pixel

    # Lire le projet EcoTaxa correspondant
    zoo_proj = ecotaxa_if.get_project(prj.projid)
    if zoo_proj is None:
        raise Exception("GenerateTaxonomyHistogram: EcoTaxa project %s could not be read in EcoPart project %s"
                        % (prj.projid, prj.pprojid))
    areacol = zoo_proj.obj_free_cols.get("area")
    if areacol is None:
        raise Exception("GenerateTaxonomyHistogram: area attribute is required in EcoTaxa project %d" % prj.projid)

    # app.logger.info("Esd col is %s",areacol)
    depth_offset = prj.default_depthoffset
    if depth_offset is None:
        depth_offset = uvp_sample.acq_depthoffset
    if depth_offset is None:
        depth_offset = 0

    # select classif_id,depth_min depth,objdate+objtime objdatetime,{areacol} areacol
    if DEV_BEHAVIOR:
        def GetObjectsForTaxoHistoCompute(prj, sampleid):
            # """
            # select classif_id,depth_min depth,objdate+objtime objdatetime,{areacol} areacol
            # from objects
            # join acquisitions on objects.acquisid=acquisitions.acquisid
            # WHERE acq_sample_id={sampleid} and classif_id is not NULL and depth_min is not NULL
            # and {areacol} is not NULL and classif_qual='V'
            # """.format(sampleid=eco_sampleid, areacol=areacol), None, False, psycopg2.extras.RealDictCursor)
            queried_columns = ["obj.classif_id", "obj.classif_qual", "obj.depth_min",
                               "obj.objdate", "obj.objtime", "fre.area"]
            api_res = ecotaxa_if.get_objects_for_sample(prj.projid, sampleid, queried_columns,
                                                        only_validated=True)
            # Do some calculations/filtering for returned data
            ret = []
            for an_obj in api_res:
                if an_obj["classif_id"] is None or an_obj["depth_min"] is None \
                        or an_obj["area"] is None:
                    continue
                an_obj["objdatetime"] = None
                if an_obj["objdate"] is not None and an_obj["objtime"] is not None:
                    # Les dates retournées par l'API sont textuelles
                    an_obj["objdatetime"] = datetime.datetime.strptime(an_obj["objdate"] + " " + an_obj["objtime"],
                                                                       "%Y-%m-%d %H:%M:%S")
                ret.append(an_obj)
            return ret

        epoch0 = 0
        if uvp_sample.organizedbydeepth:
            lst_vol = GetAssoc("""select cast(round((depth-2.5)/5) as INT) tranche,watervolume 
            from part_histopart_reduit where psampleid=%s""" % psampleid)
            lst_taxo_det = GetObjectsForTaxoHistoCompute(prj, uvp_sample.sampleid)
            for obj in lst_taxo_det:
                obj['tranche'] = math.floor((obj['depth_min'] + depth_offset) / 5)
        else:
            lst_voldb = GetAll("""select distinct datetime
                                                ,watervolume 
                                            from part_histopart_reduit 
                                            where psampleid=%s""" % psampleid, None, False,
                               psycopg2.extras.RealDictCursor)
            lst_vol = {}
            for vol in lst_voldb:
                tranche = int(math.floor(vol['datetime'].timestamp() / 3600))
                lst_vol[tranche] = vol['watervolume']
            if len(lst_vol.keys()) > 0:
                epoch0 = min(lst_vol.keys())
            lst_vol = {k - epoch0: {'tranche': k - epoch0, 'watervolume': v} for (k, v) in lst_vol.items()}
            lst_taxo_det = GetObjectsForTaxoHistoCompute(prj, uvp_sample.sampleid)
            for obj in lst_taxo_det:
                if obj['objdatetime']:
                    obj['tranche'] = math.floor(obj['objdatetime'].timestamp() / 3600) - epoch0
                    obj['datetimetranche'] = obj['objdatetime'].strftime("%Y%m%d %H:30:00")
                else:
                    obj['tranche'] = 0
                    obj['datetimetranche'] = ""
    else:
        queried_columns = ["obj.classif_id", "obj.classif_qual", "obj.depth_min", "fre.area"]
        api_res = ecotaxa_if.get_objects_for_sample(zoo_proj.projid, uvp_sample.sampleid, queried_columns,
                                                    only_validated=True)
        # Do some calculations/filtering for returned data
        lst_taxo_det = []
        for an_obj in api_res:
            if an_obj["classif_id"] is None or an_obj["depth_min"] is None or an_obj["area"] is None:
                continue
            an_obj["tranche"] = int((an_obj["depth_min"] + depth_offset) / 5)
            lst_taxo_det.append(an_obj)

    lst_taxo = {}
    for r in lst_taxo_det:
        # On aggrège par catégorie+tranche d'eau
        cle = "{}/{}".format(r['classif_id'], r['tranche'])
        if cle not in lst_taxo:
            lst_taxo[cle] = {'nbr': 0, 'esdsum': 0, 'bvsum': 0, 'classif_id': r['classif_id'], 'tranche': r['tranche']}
            if DEV_BEHAVIOR:
                if not uvp_sample.organizedbydeepth:
                    lst_taxo[cle]['datetimetranche'] = r['datetimetranche']
        lst_taxo[cle]['nbr'] += 1
        esd = 2 * math.sqrt(r['area'] * (pixel ** 2) / math.pi)
        lst_taxo[cle]['esdsum'] += esd
        biovolume = pow(esd / 2, 3) * 4 * math.pi / 3
        lst_taxo[cle]['bvsum'] += biovolume

    if DEV_BEHAVIOR:
        pass
    else:
        lst_vol = GetAssoc("""select cast(round((depth-2.5)/5) as INT) tranche, watervolume 
        from part_histopart_reduit 
        where psampleid=%s""" % psampleid)
    ExecSQL("delete from part_histocat_lst where psampleid=%s" % psampleid)
    ExecSQL("delete from part_histocat where psampleid=%s" % psampleid)
    if DEV_BEHAVIOR:
        sql = "insert into " + \
              "part_histocat(psampleid, classif_id, lineno, depth,datetime, watervolume, nbr, avgesd, totalbiovolume)" \
              "  values({psampleid},{classif_id},{lineno},{depth},{datetime},{watervolume},{nbr},{avgesd},{totalbiovolume})"
    else:
        sql = """insert into part_histocat(psampleid, classif_id, lineno, depth, watervolume, nbr, avgesd, totalbiovolume)
                values({psampleid},{classif_id},{lineno},{depth},{watervolume},{nbr},{avgesd},{totalbiovolume})"""
    # 0 Taxoid, tranche
    for r in lst_taxo.values():
        avgesd = r['esdsum'] / r['nbr']
        biovolume = r['bvsum']
        watervolume = 'NULL'
        if r['tranche'] in lst_vol:
            watervolume = lst_vol[r['tranche']]['watervolume']
        if DEV_BEHAVIOR:
            ExecSQL(sql.format(
                psampleid=psampleid, classif_id=r['classif_id'],
                lineno=r['tranche'],
                depth=r['tranche'] * 5 + 2.5 if uvp_sample.organizedbydeepth else "null",
                datetime="null" if uvp_sample.organizedbydeepth
                else f" to_timestamp('{r['datetimetranche']}','YYYYMMDD HH24:MI:SS')",
                watervolume=watervolume,
                nbr=r['nbr'], avgesd=avgesd, totalbiovolume=biovolume))
        else:
            ExecSQL(sql.format(
                psampleid=psampleid, classif_id=r['classif_id'],
                lineno=r['tranche'],
                depth=r['tranche'] * 5 + 2.5,
                watervolume=watervolume,
                nbr=r['nbr'], avgesd=avgesd, totalbiovolume=biovolume))
    ExecSQL("""insert into part_histocat_lst(psampleid, classif_id) 
            select distinct psampleid,classif_id from part_histocat where psampleid=%s""" % psampleid)

    ExecSQL("""update part_samples set daterecalculhistotaxo=current_timestamp  
            where psampleid=%s""" % psampleid)
