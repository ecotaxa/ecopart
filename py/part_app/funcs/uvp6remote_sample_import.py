import csv
import datetime
import io
import logging
import os
import re
import shutil
import ssl
import tempfile
import urllib.request
import zipfile
from ftplib import FTP
from html.parser import HTMLParser

import numpy as np

from part_app.constants import VOLUME_ROUNDING
from part_app.funcs.uvp_sample_import import GetPathForRawHistoFile
from part_app.prod_or_dev import DEV_BEHAVIOR
from .. import database as partdatabase
from ..app import db
from ..db_utils import ExecSQL
from ..funcs import uvp_sample_import as uvp_sample_import
from ..funcs.common_sample_import import ToFloat, GenerateReducedParticleHistogram
from ..remote import EcoTaxaInstance
from ..txt_utils import ntcv


class ATagParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.FoundA = []

    def handle_starttag(self, tag, attrs):
        if tag != 'a':
            return
        attr_dict = dict(attrs)
        if 'href' not in attr_dict:
            return
        href = attr_dict['href']
        if ':' in href:
            return  # on ignore les url qui respécifient un protocole
        if not href.endswith('.txt'):
            return  # on ne garde que les .txt
        fichier = os.path.basename(href)
        self.FoundA.append(fichier)


def ParseMetadataFile(MetaF):
    meta_data = {}
    for line in MetaF:
        cols = line.strip().split('\t')
        if len(cols) == 2:
            meta_data[cols[0].lower()] = cols[1]
    return meta_data


class RemoteServerFetcher:
    # A surcharger pour les tests sous Linux
    FTP_PORT = 21

    def __init__(self, pprojid: int):
        self.Prj = partdatabase.part_projects.query.filter_by(pprojid=pprojid).first()
        self.ftp = None

    def Connect(self):
        self.ftp = FTP(timeout=10)
        self.ftp.connect(host=self.Prj.remote_url, port=self.FTP_PORT)
        self.ftp.login(user=self.Prj.remote_user, passwd=self.Prj.remote_password)
        if ntcv(self.Prj.remote_directory) != "":
            self.ftp.cwd(self.Prj.remote_directory)

    def IsHttp(self):
        return self.Prj.remote_url.startswith('http:') or self.Prj.remote_url.startswith('https:')

    def GetHTTPUrl(self, Filename=''):
        url = self.Prj.remote_url
        if (not url.endswith('/')) and (not self.Prj.remote_directory.startswith('/')):
            url += '/'
        url += self.Prj.remote_directory
        if not url.endswith('/'):
            url += '/'
        url += Filename
        return url

    def RetrieveFile(self, FileName, TempFile):
        if self.IsHttp():
            contexte_ssl_sans_controle = ssl.SSLContext()
            with urllib.request.urlopen(self.GetHTTPUrl(FileName), context=contexte_ssl_sans_controle) as response:
                html = response.read()
                TempFile.write(html)
        else:
            self.ftp.retrbinary('RETR %s' % FileName, TempFile.write)

    def GetServerFiles(self):
        """Retourne la liste des fichiers sous forme d'un dictionnaire
        clé : N° de sample value=> sampletype,files[filetype]:filename
        Exemple :
        {'SG003B': {'sampletype': 'TIME',
            'files': {'META': 'SG003B_000002LP_TIME_META.txt', 'LPM': 'SG003B_000002LP_TIME_LPM.txt'
                                        , 'BLACK': 'SG003B_000002LP_TIME_BLACK.txt'}
             },
        'SG003A': {'sampletype': 'DEPTH',
            'files': {'TAXO2': 'SG003A_000002LP_DEPTH_TAXO2.txt', 'META': 'SG003A_000002LP_DEPTH_META.txt'
                    , 'LPM': 'SG003A_000002LP_DEPTH_LPM.txt', 'TAXO1': 'SG003A_000002LP_DEPTH_TAXO1.txt'
                    , 'BLACK': 'SG003A_000002LP_DEPTH_BLACK.txt'} }}
"""
        if self.IsHttp():
            lst = self.GetServerFilelistHTTP()
        else:
            lst = self.GetServerFilelistFTP()
        samples = {}
        for entry in lst:
            if entry[-4:] != '.txt':  # premier filtrage basique et silencieux
                continue
            m = re.fullmatch(r"([^_]+)_([^_]+)_([^_]+)_([^_]+)\.txt", entry)
            if m is None:
                logging.warning("Particule RemoteServerFetcher.GetServerFiles Skip malformed file " + entry)
                continue
            sample_name = m.group(1)
            if sample_name not in samples:
                samples[sample_name] = {'sampletype': m.group(3), 'files': {}}
            samples[sample_name]['files'][m.group(4)] = entry
            # print(entry, m.group(1), m.group(2), m.group(3), m.group(4))
        if DEV_BEHAVIOR:
            for samplename in list(samples.keys()):
                if 'LPM' not in samples[samplename]['files']:
                    del samples[samplename]
        return samples

    def GetServerFilelistHTTP(self):
        contexte_ssl_sans_controle = ssl.SSLContext()
        url = self.GetHTTPUrl()
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, context=contexte_ssl_sans_controle) as response:
            html = response.read().decode('latin-1')
            parser = ATagParser()
            parser.feed(html)
            return parser.FoundA

    def GetServerFilelistFTP(self):
        if self.ftp is None:
            self.Connect()
        return list(self.ftp.nlst())

    def FetchServerDataForProject(self, ForcedSample: list):
        if self.Prj.remote_type == 'TSV LOV':
            return self.FetchServerDataForProjectLamda(ForcedSample)

    def FetchServerDataForProjectLamda(self, forced_sample: list):
        """
        Recupère les données d'un serveur lamba et les charge
        :param forced_sample: Permet de forcer une liste de samplename pour ne traiter que ceux là et forcer leur
                rechargement même s'il existent déjà
        :return Liste des sampleid
        """
        returnedsampleid = []
        server_samples = self.GetServerFiles()
        db_samples = partdatabase.part_samples.query.filter_by(pprojid=self.Prj.pprojid)
        db_samples_names = {s.profileid: s for s in db_samples}
        if len(forced_sample) == 0:
            forced_sample = None
        tmp_dir = None
        for SampleName in server_samples:
            if forced_sample:  # on restreint la liste de ce qu'on traite
                if SampleName not in forced_sample:
                    continue
            sample = None
            if SampleName in db_samples_names:  # Sample existe déjà
                if forced_sample and SampleName in forced_sample:  # mais on souhaite reforce son chargement
                    sample = db_samples_names[SampleName]
                else:
                    continue  # existe déjà sans souhait de reforcer son chargement, on saute
            if 'META' not in server_samples[SampleName]['files'] or 'LPM' not in server_samples[SampleName]['files']:
                logging.warning("Particule RemoteServerFetcher.GetServerFiles skip processing : META and LPM are "
                                "required to handle sample " + SampleName)
                continue
            print("Processing sample ", SampleName)
            if sample is None:
                sample = partdatabase.part_samples()
                db.session.add(sample)
            tmp_dir = tempfile.mkdtemp()
            with zipfile.ZipFile(tmp_dir + '/raw.zip', 'w', compression=zipfile.ZIP_DEFLATED) as zf:
                for filetype in server_samples[SampleName]['files']:
                    with open(tmp_dir + "/" + filetype, "wb") as TmpF:
                        self.RetrieveFile(server_samples[SampleName]['files'][filetype], TmpF)
                    zf.write(TmpF.name, arcname=filetype + '.txt')
            with open(tmp_dir + "/META", 'r') as MetaF:
                meta_data = ParseMetadataFile(MetaF)

            sample.pprojid = self.Prj.pprojid
            sample.profileid = SampleName
            sample.filename = server_samples[SampleName]['files']['LPM']
            if 'CTD' in server_samples[SampleName]['files']:
                sample.ctd_origfilename = server_samples[SampleName]['files']['CTD']
            sample.instrumsn = meta_data.get('camera_ref', '')
            sample.acq_aa = meta_data.get('aa', '')
            sample.acq_exp = meta_data.get('exp', '')
            sample.acq_pixel = meta_data.get('pixel_size', '')
            sample.acq_volimage = meta_data.get('image_volume', '')
            sample.acq_gain = meta_data.get('gain', '')
            sample.acq_threshold = meta_data.get('threshold', '')
            sample.acq_shutterspeed = meta_data.get('shutter', '')
            sample.instrumsn = meta_data.get('camera_ref', '')
            # Sample.op_sample_email=MetaData.get('operator_email','')
            sample.histobrutavailable = True
            sample.organizedbydeepth = server_samples[SampleName]['sampletype'] == 'DEPTH'
            if meta_data.get('pressure_offset', '') != '':
                sample.acq_depthoffset = ToFloat(meta_data.get('pressure_offset', ''))

            # Lat,Long et Date sont les moyennes du fichier LPM
            # noinspection PyTypeChecker
            samples_data = np.genfromtxt(tmp_dir + "/LPM", names=True, delimiter='\t', autostrip=True,
                                         usecols=['DATE_TIME', 'LATITUDE_decimal_degree', 'LONGITUDE_decimal_degree'],
                                         # ,usecols=[0,2,3]
                                         dtype=[('DATE_TIME', 'S15'), ('LATITUDE_decimal_degree', '<f4'),
                                                ('LONGITUDE_decimal_degree', '<f4')])
            # s'il n'y a qu'une seule ligne genfromtxt ne retourne pas un tableau à 2 dimensions
            # , donc on transforme celui ci en tableau 2D
            if len(samples_data.shape) == 0:
                samples_data = np.array([samples_data])
            sample.latitude = round(np.average(samples_data['LATITUDE_decimal_degree'] + 360) - 360, 3)
            sample.longitude = round(np.average(samples_data['LONGITUDE_decimal_degree'] + 360) - 360, 3)
            first_date = datetime.datetime.strptime(samples_data['DATE_TIME'][0].decode(), '%Y%m%dT%H%M%S')
            last_date = datetime.datetime.strptime(samples_data['DATE_TIME'][samples_data.shape[0] - 1].decode(),
                                                   '%Y%m%dT%H%M%S')
            sample.sampledate = datetime.datetime.fromtimestamp(int((first_date.timestamp() + last_date.timestamp())
                                                                    / 2))

            db.session.commit()
            returnedsampleid.append(sample.psampleid)
            rawfileinvault = GetPathForRawHistoFile(sample.psampleid)
            shutil.copyfile(tmp_dir + '/raw.zip', rawfileinvault)
            # shutil.copyfile(MetaF.name, "c:/temp/testmeta.txt")
            # shutil.copyfile(TmpDir+'/raw.zip', "c:/temp/testremote.zip")
        if tmp_dir:
            shutil.rmtree(tmp_dir)
        return returnedsampleid


def GenerateParticleHistogram(psampleid: int):
    """
    Génération de l'histogramme particulaire détaillé (45 classes) et réduit (15 classes) à partir du fichier ASC
    :param psampleid:
    :return:
    """
    part_sample = partdatabase.part_samples.query.filter_by(psampleid=psampleid).first()
    if part_sample is None:
        raise Exception("GenerateRawHistogram: Sample %d missing" % psampleid)
    prj = partdatabase.part_projects.query.filter_by(pprojid=part_sample.pprojid).first()
    rawfileinvault = GetPathForRawHistoFile(part_sample.psampleid)
    depth_offset = prj.default_depthoffset
    if depth_offset is None:
        depth_offset = part_sample.acq_depthoffset
    if depth_offset is None:
        depth_offset = 0

    with zipfile.ZipFile(rawfileinvault, "r") as zf:
        with zf.open('LPM.txt', 'r') as flpmb:
            flpm = io.TextIOWrapper(flpmb, encoding='latin_1')
            csvfile = csv.DictReader(flpm, delimiter='\t')
            nbr_line = 0
            histo_by_tranche = {}
            for L in csvfile:
                nbr_line += 1
                depth = float(L['PRES_decibar']) + depth_offset
                time = L['DATE_TIME']
                if part_sample.organizedbydeepth:
                    tranche = (depth // 5) * 5
                    depth_tranche = tranche + 2.5
                    if DEV_BEHAVIOR:
                        dateheure = datetime.datetime.strptime(time, "%Y%m%dT%H%M%S")
                else:
                    tranche = time[:-4]  # On enlève minute et secondes
                    depth_tranche = depth  # on prend la premiere profondeur
                    if DEV_BEHAVIOR:
                        dateheure = None
                nbr_par_classe = {}
                # GreyParClasse = {}
                nbr_img = float(L['IMAGE_NUMBER_PARTICLES'])
                for classe in range(18):
                    nbr_par_classe[classe] = round(
                        ToFloat(L['NB_SIZE_SPECTRA_PARTICLES_class_%s' % (classe + 1,)]) * nbr_img)
                if tranche not in histo_by_tranche:
                    histo_by_tranche[tranche] = {'NbrImg': 0, 'NbrParClasse': nbr_par_classe,
                                                 'DepthTranche': depth_tranche}  # ,'GreyParClasse':GreyParClasse
                    if DEV_BEHAVIOR:
                        histo_by_tranche[tranche]['timestamp'] = 0
                else:
                    for classe in range(18):
                        histo_by_tranche[tranche]['NbrParClasse'][classe] += nbr_par_classe[classe]
                histo_by_tranche[tranche]['NbrImg'] += nbr_img
                if DEV_BEHAVIOR:
                    if dateheure:
                        # on va calculer l'heure moyenne, donc on fait la somme
                        histo_by_tranche[tranche]['timestamp'] += dateheure.timestamp() * nbr_img
            logging.info("Line count %d" % nbr_line)

            ExecSQL("delete from part_histopart_det where psampleid=" + str(psampleid))
            sql = """insert into part_histopart_det(psampleid, lineno, depth,  watervolume,datetime
                , class17, class18, class19, class20, class21, class22, class23, class24, class25, class26, class27
                , class28, class29, class30, class31, class32, class33, class34)
            values(%(psampleid)s,%(lineno)s,%(depth)s,%(watervolume)s,%(datetime)s,%(class17)s,%(class18)s,%(class19)s
            ,%(class20)s,%(class21)s,%(class22)s,%(class23)s,%(class24)s,%(class25)s,%(class26)s,%(class27)s
            ,%(class28)s,%(class29)s,%(class30)s,%(class31)s,%(class32)s,%(class33)s,%(class34)s)"""
            sqlparam = {'psampleid': psampleid}
            tranches = sorted(histo_by_tranche.keys())
            for i, tranche in enumerate(tranches):
                sqlparam['lineno'] = i
                sqlparam['depth'] = round(histo_by_tranche[tranche]['DepthTranche'], 2)
                sqlparam['watervolume'] = round(histo_by_tranche[tranche]['NbrImg'] * part_sample.acq_volimage, VOLUME_ROUNDING)
                if part_sample.organizedbydeepth:
                    sqlparam['datetime'] = None
                    if DEV_BEHAVIOR:
                        if histo_by_tranche[tranche]['timestamp']:
                            ts = round(histo_by_tranche[tranche]['timestamp'] / histo_by_tranche[tranche]['NbrImg'], 1)
                            sqlparam['datetime'] = datetime.datetime.fromtimestamp(ts)
                else:
                    # on insère avec l'heure à 30minutes
                    sqlparam['datetime'] = datetime.datetime.strptime(tranche + '3000', "%Y%m%dT%H%M%S")

                for classe in range(18):
                    sqlparam['class%02d' % (17 + classe)] = histo_by_tranche[tranche]['NbrParClasse'][classe]
                ExecSQL(sql, sqlparam)
    GenerateReducedParticleHistogram(psampleid)


def GenerateTaxonomyHistogram(ecotaxa_if: EcoTaxaInstance, psampleid):
    """
    Génération de l'histogramme Taxonomique
    :param psampleid:
    :return:
    """
    part_sample = partdatabase.part_samples.query.filter_by(psampleid=psampleid).first()
    if part_sample is None:
        raise Exception("GenerateTaxonomyHistogram: Sample %d missing" % psampleid)
    prj = partdatabase.part_projects.query.filter_by(pprojid=part_sample.pprojid).first()
    if DEV_BEHAVIOR:
        ExecSQL("delete from part_histocat_lst where psampleid=%s" % psampleid)
        ExecSQL("delete from part_histocat where psampleid=%s" % psampleid)
    rawfileinvault = GetPathForRawHistoFile(part_sample.psampleid)
    depth_offset = prj.default_depthoffset
    if depth_offset is None:
        depth_offset = part_sample.acq_depthoffset
    if depth_offset is None:
        depth_offset = 0
    with zipfile.ZipFile(rawfileinvault, "r") as zf:
        with zf.open("META.txt", 'r') as MetaFb:
            meta_f = io.TextIOWrapper(MetaFb, encoding='latin_1')
            meta_data = ParseMetadataFile(meta_f)
            taxo_ids = list(range(40))
            for i in range(40):
                try:
                    taxo_ids[i] = int(meta_data.get('category_name_%d' % (i + 1), ''))
                except:
                    taxo_ids[i] = 0

            valid_ids = [x for x in taxo_ids if x > 0]
            if len(valid_ids) == 0:
                raise Exception("GenerateTaxonomyHistogram: Sample %d no valid category_name_" % psampleid)
            taxo_db = set([tid for tid, _name in ecotaxa_if.get_taxo(valid_ids)])

            for i in range(40):
                if taxo_ids[i] > 0:
                    if taxo_ids[i] not in taxo_db:
                        raise Exception(
                            "GenerateTaxonomyHistogram: Sample %d category_name_%d is not a known taxoid" % (
                                psampleid, (i + 1)))

        if DEV_BEHAVIOR:
            if 'taxo2.txt' not in [f.filename.lower() for f in zf.filelist]:
                return
        with zf.open('TAXO2.txt', 'r') as ftaxob:
            ftaxo = io.TextIOWrapper(ftaxob, encoding='latin_1')
            csvfile = csv.DictReader(ftaxo, delimiter='\t')
            nbr_line = 0
            histo_by_tranche = {}
            for L in csvfile:
                if L['PRES_decibar'] == '':  # ligne vide
                    continue
                nbr_line += 1
                depth = float(L['PRES_decibar']) + depth_offset
                time = L['DATE_TIME']
                if part_sample.organizedbydeepth:
                    tranche = (depth // 5) * 5
                    depth_tranche = tranche + 2.5
                else:
                    tranche = time[:-4]  # On enlève Heure et minute
                    depth_tranche = depth  # on prend la premiere profondeur
                nbr_par_classe = {}
                size_par_classe = {}
                nbr_img = float(L['IMAGE_NUMBER_PLANKTON'])
                for classe in range(40):
                    if DEV_BEHAVIOR:
                        nbr_par_classe[classe] = ToFloat(L['NB_PLANKTON_cat_%s' % (classe + 1,)]) or 0.0
                        size_par_classe[classe] = ToFloat(L['SIZE_PLANKTON_cat_%s' % (classe + 1,)]) or 0.0
                    else:
                        nbr_par_classe[classe] = ToFloat(L['NB_PLANKTON_cat_%s' % (classe + 1,)])
                        size_par_classe[classe] = ToFloat(L['SIZE_PLANKTON_cat_%s' % (classe + 1,)])
                    size_par_classe[classe] = nbr_par_classe[classe] * size_par_classe[classe] \
                        if size_par_classe[classe] else 0
                if tranche not in histo_by_tranche:
                    histo_by_tranche[tranche] = {'NbrImg': nbr_img, 'NbrParClasse': nbr_par_classe,
                                                 'DepthTranche': depth_tranche,
                                                 'SizeParClasse': size_par_classe}
                else:
                    histo_by_tranche[tranche]['NbrImg'] += nbr_img
                    for classe in range(40):
                        histo_by_tranche[tranche]['NbrParClasse'][classe] += nbr_par_classe[classe]
                        histo_by_tranche[tranche]['SizeParClasse'][classe] += size_par_classe[classe]
            for tranche in histo_by_tranche:  # fin calcul du niveau de gris moyen pas tranche/classe
                for classe in range(40):
                    if histo_by_tranche[tranche]['NbrParClasse'][classe] > 0:
                        histo_by_tranche[tranche]['SizeParClasse'][classe] /= histo_by_tranche[tranche]['NbrParClasse'][
                            classe]
            logging.info("Line count %d" % nbr_line)

            if DEV_BEHAVIOR:
                pass
            else:
                ExecSQL("delete from part_histocat_lst where psampleid=%s" % psampleid)
                ExecSQL("delete from part_histocat where psampleid=%s" % psampleid)
            sql = """INSERT INTO part_histocat(psampleid, classif_id, lineno, depth, watervolume, nbr
                                , avgesd, totalbiovolume)
                    VALUES(%(psampleid)s,%(classif_id)s,%(lineno)s,%(depth)s,%(watervolume)s,%(nbr)s
                                ,%(avgesd)s,%(totalbiovolume)s)"""
            sqlparam = {'psampleid': psampleid}
            tranches = sorted(histo_by_tranche.keys())
            for i, tranche in enumerate(tranches):
                sqlparam['lineno'] = i
                sqlparam['depth'] = histo_by_tranche[tranche]['DepthTranche']
                sqlparam['watervolume'] = round(histo_by_tranche[tranche]['NbrImg'] * part_sample.acq_volimage, VOLUME_ROUNDING)
                for classe in range(40):
                    if taxo_ids[classe] > 0 and histo_by_tranche[tranche]['NbrParClasse'][classe] > 0:
                        sqlparam['classif_id'] = taxo_ids[classe]
                        sqlparam['nbr'] = histo_by_tranche[tranche]['NbrParClasse'][classe]
                        sqlparam['avgesd'] = histo_by_tranche[tranche]['SizeParClasse'][classe]
                        sqlparam['totalbiovolume'] = None
                        ExecSQL(sql, sqlparam)
            ExecSQL("""insert into part_histocat_lst(psampleid, classif_id) 
            select distinct psampleid,classif_id from part_histocat where psampleid=%s""" % psampleid)


if __name__ == "__main__":
    RSF = RemoteServerFetcher(1)
    # print(RSF.GetServerFiles())
    # RSF.FetchServerDataForProject(['SG003A'])
