import io
import math
import traceback

import matplotlib
import matplotlib.dates
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
from flask import request, send_file

from ..app import part_app
from ..constants import PartDetClassLimit, PartRedClassLimit, CTDFixedColByKey
from ..db_utils import GetAll, GetAssoc2Col
from ..http_utils import gvg
from ..remote import EcoTaxaInstance
from ..txt_utils import GetClassLimitTxt
from ..views import part_main as umain

DepthTaxoHistoLimit = [0, 25, 50, 75, 100, 125, 150, 200, 250, 300, 350, 400, 450, 500, 600, 700, 800, 900, 1000, 1250,
                       1500, 1750, 2000, 2250, 2500, 2750
    , 3000, 3250, 3500, 3750, 4000, 4250, 4500, 4750, 5000, 5250, 5500, 5750, 6000, 7000, 8000, 9000, 10000, 11000,
                       12000, 13000, 14000, 15000, 20000, 50000]


def GetTaxoHistoLimit(MaxDepth):
    res = []
    break_on_next = False
    for d in DepthTaxoHistoLimit:
        res.append(d)
        if break_on_next:
            break
        if d > MaxDepth:
            break_on_next = True
    return res


def GetTaxoHistoWaterVolumeSQLExpr(field, retval='start'):
    res = "case "
    for i in range(1, len(DepthTaxoHistoLimit)):
        res += " when {2}<{0} then {1}".format(
            DepthTaxoHistoLimit[i],
            DepthTaxoHistoLimit[i - 1] if retval == 'start'
            else (DepthTaxoHistoLimit[i - 1] +
                  DepthTaxoHistoLimit[i]) / 2,
            field)
    return res + " end"


# variante de matplotlib.dates.DateFormatter mais qui ne plante pas en cas de zero, ce qui arrive si les graphes sont vides
class dateFormaterYMD(matplotlib.ticker.Formatter):
    def __call__(self, x, pos=0):
        if x <= 0:
            return "-"
        return matplotlib.dates.num2date(x).strftime("%Y-%m-%d")


@part_app.route('/drawchart')
def part_drawchart():
    ecotaxa_if = EcoTaxaInstance(request)
    couleurs = (
        "#FF0000", "#4385FF", "#00BE00", "#AA6E28", "#FF9900", "#FFD8B1", "#808000", "#FFEA00", "#FFFAC8", "#BEFF00",
        "#AAFFC3", "#008080", "#64FFFF", "#000080", "#800000", "#820096", "#E6BEFF", "#FF00FF", "#808080", "#FFC9DE",
        "#000000")
    prj_color_map = {}  # chaque projet à une couleur
    prj_sample_count = {}
    prj_title = {}
    sample_color_map = {}  # chaque sample à une couleur s'il n'y a qu'un seul projet
    sample_title = {}
    try:
        gpr = request.args.getlist('gpr')
        gpd = request.args.getlist('gpd')
        gctd = request.args.getlist('ctd')
        gtaxo = request.args.getlist('taxolb')
        filtre = {k: v for k, v in request.args.items()}
        prof_type_vertical_forced = False
        if filtre.get('filt_proftype', '') == '':
            filtre['filt_proftype'] = 'V'
            # Si pas de filtre sur le type de profil ou tous, alors on met Vertical pour ne pas melanger les 2 ce qui donne des graphes incoherents
            prof_type_vertical_forced = True  # pourrais être utile pour affiche un message, mais risque d'être un message parasite.
        profil_vertical = filtre.get('filt_proftype', '') == 'V'
        if not profil_vertical:
            gpd.append('depth')  # si ce sont des profils temporels, on ajoute une trace pour les profondeurs
        samples, _ignored = umain.GetFilteredSamples(ecotaxa_if=ecotaxa_if, Filter=filtre,
                                                     GetVisibleOnly=True, MinimumPartVisibility='V')
        for S in samples:
            if S['pprojid'] not in prj_color_map:
                prj_color_map[S['pprojid']] = couleurs[len(prj_color_map) % len(couleurs)]
                prj_title[S['pprojid']] = S['ptitle']
            if S['psampleid'] not in sample_color_map:
                sample_color_map[S['psampleid']] = couleurs[len(sample_color_map) % len(couleurs)]
                sample_title[S['psampleid']] = S['profileid']
            prj_sample_count[S['pprojid']] = prj_sample_count.get(S['pprojid'], 0) + 1
        # nbr_chart += 1 # toujours un graphe en plus à la fin pour la legende ou le message disant pourquoi pas de legende
        nbr_chart = len(gpr) + len(gpd) + len(gctd) + len(gtaxo)
        fig_size_x = nbr_chart
        time_absolute = False
        if not profil_vertical and gvg('TimeScale') == 'A':
            time_absolute = True
        if profil_vertical:
            if nbr_chart > 4: fig_size_x = 4
        else:
            if nbr_chart > 2: fig_size_x = 2
        fig_size_y = math.ceil(nbr_chart / fig_size_x)
        # toujours un graphe en plus à la fin pour la legende ou le message disant pourquoi pas de legende
        fig_size_y += 1
        if fig_size_x < 2:
            fig_size_x = 2  # le graphe de legende fait 2 de largeur même s'il n'y a qu'un graphe
        font = {'family': 'arial', 'weight': 'normal', 'size': 10}
        plt.rc('font', **font)
        plt.rcParams['lines.linewidth'] = 0.5
        if profil_vertical:
            fig = plt.figure(figsize=(fig_size_x * 4, fig_size_y * 5), dpi=100)
        else:
            fig = plt.figure(figsize=(fig_size_x * 8, fig_size_y * 3), dpi=100)
        chartid = 0
        depth_filter = ""
        if gvg('filt_depthmin'):
            depth_filter += " and depth>=%d" % int(gvg('filt_depthmin'))
        if gvg('filt_depthmax'):
            depth_filter += " and depth<=%d" % int(gvg('filt_depthmax'))
        # traitement des Graphes particulaire réduit
        if len(gpr) > 0:
            if profil_vertical:
                sql = "select depth y "
            else:
                if time_absolute:
                    sql = "select datetime y "
                else:
                    sql = "select -lineno y "
            # sql+=''.join([',case when watervolume>0 then class%02d/watervolume else 0 end as c%s'%(int(c[2:]),i)
            #               for i,c in enumerate(gpr) if c[0:2]=="cl"])
            sql += ''.join([',case when watervolume>0 then class%02d/watervolume else null end as c%s' % (int(c[2:]), i)
                            for i, c in enumerate(gpr) if c[0:2] == "cl"])
            sql += ''.join([',coalesce(biovol%02d) as c%s' % (int(c[2:]), i)
                            for i, c in enumerate(gpr) if c[0:2] == "bv"])
            sql += """ from part_histopart_reduit
             where psampleid=%(psampleid)s
             {}
            order by Y""".format(depth_filter)
            graph = list(range(0, len(gpr)))
            for i, c in enumerate(gpr):
                graph[i] = fig.add_subplot(fig_size_y, fig_size_x, chartid + 1)
                x_label = ""
                if c[0:2] == "cl":
                    x_label = 'Particle red. class %s (%s) # l-1' % (c, GetClassLimitTxt(PartRedClassLimit, int(c[2:])))
                if c[0:2] == "bv":
                    x_label = 'Biovolume red. class %s (%s) mm3 l-1' % (
                        c, GetClassLimitTxt(PartRedClassLimit, int(c[2:])))
                if not profil_vertical:
                    if time_absolute:
                        graph[i].xaxis.set_major_formatter(dateFormaterYMD())
                        x_label = "X : date, Y : " + x_label
                    else:
                        x_label = "X : time (hour), Y : " + x_label
                graph[i].set_xlabel(x_label)
                chartid += 1
            for rs in samples:
                db_data = GetAll(sql, {'psampleid': rs['psampleid']})
                data = np.empty((len(db_data), 2))
                for i, c in enumerate(gpr):
                    xcolname = "c%d" % i
                    valcount = 0
                    for rnum, r in enumerate(db_data):
                        if r[xcolname] is None or r['y'] is None:
                            continue
                        if profil_vertical:
                            data[valcount] = (-r['y'], r[xcolname])
                        else:
                            if time_absolute:
                                data[valcount] = (r[xcolname], matplotlib.dates.date2num(r['y']))
                            else:
                                data[valcount] = (r[xcolname], -r['y'])
                        valcount += 1
                    # data = data[~np.isnan(data[:,1]),:] # Supprime les lignes avec une valeur à Nan et fait donc de l'extrapolation linaire
                    # sans cette ligne les null des colonnes cl devient des nan et ne sont pas tracès (rupture de ligne)
                    # cependant l'autre option est de le traiter au niveau de l'import
                    color = prj_color_map[rs['pprojid']] if len(prj_color_map) > 1 else \
                        (sample_color_map[rs['psampleid']] if len(sample_color_map) < 25 else None)
                    graph[i].plot(data[:valcount, 1], data[:valcount, 0], color=color)
            # fait après les plot pour avoir un echelle X bien callé avec les données
            # et evite les erreurs log si la premiere serie n'as pas de valeurs
            for i, c in enumerate(gpr):
                if gvg('XScale') != 'I':
                    try:
                        if gvg('XScale') == 'O':
                            if profil_vertical:
                                graph[i].set_xscale('log')
                            else:
                                graph[i].set_yscale('log')
                        if gvg('XScale') == 'S':
                            if profil_vertical:
                                graph[i].set_xscale('symlog')
                            else:
                                graph[i].set_yscale('symlog')
                    except Exception as e:
                        # parfois s'il n'y a pas de données pas possible de passer en echelle log
                        # , on force alors linear sinon ça plante plus loin
                        if profil_vertical:
                            graph[i].set_xscale('linear')
                        else:
                            graph[i].set_yscale('linear')
                else:
                    if not time_absolute:
                        graph[i].set_xlim(left=0)
        # traitement des Graphes particulaire détaillés
        if len(gpd) > 0:
            if profil_vertical:
                sql = "select depth y "
            else:
                if time_absolute:
                    sql = "select datetime y "
                else:
                    sql = "select -lineno y "
            sql += ''.join([',case when watervolume>0 then class%02d/watervolume else 0 end as c%s' % (int(c[2:]), i)
                            for i, c in enumerate(gpd) if c[0:2] == "cl"])
            sql += ''.join([',coalesce(biovol%02d) as c%s' % (int(c[2:]), i)
                            for i, c in enumerate(gpd) if c[0:2] == "bv"])
            sql += ''.join([',-coalesce(depth) as c%s' % i
                            for i, c in enumerate(gpd) if c == "depth"])
            sql += """ from part_histopart_det
             where psampleid=%(psampleid)s
             {}
            order by Y""".format(depth_filter)
            graph = list(range(0, len(gpd)))
            for i, c in enumerate(gpd):
                graph[i] = fig.add_subplot(fig_size_y, fig_size_x, chartid + 1)
                x_label = ""
                if c[0:2] == "cl":
                    x_label = 'Particle det. class %s (%s) # l-1' % (c, GetClassLimitTxt(PartDetClassLimit, int(c[2:])))
                if c[0:2] == "bv":
                    x_label = 'Biovolume det. class %s (%s) mm3 l-1' % (
                        c, GetClassLimitTxt(PartDetClassLimit, int(c[2:])))
                if c == "depth":
                    x_label = 'pressure [db]'
                if not profil_vertical:
                    if time_absolute:
                        graph[i].xaxis.set_major_formatter(dateFormaterYMD())
                        x_label = "X : date, Y : " + x_label
                    else:
                        x_label = "X : time (hour), Y : " + x_label
                graph[i].set_xlabel(x_label)
                chartid += 1
            for rs in samples:
                db_data = GetAll(sql, {'psampleid': rs['psampleid']})
                data = np.empty((len(db_data), 2))
                for i, c in enumerate(gpd):
                    xcolname = "c%d" % i
                    valcount = 0
                    for rnum, r in enumerate(db_data):
                        if r[xcolname] is None or r['y'] is None:
                            continue
                        if profil_vertical:
                            data[valcount] = (-r['y'], r[xcolname])
                        else:
                            if time_absolute:
                                y = matplotlib.dates.date2num(r['y'])
                                data[valcount] = (r[xcolname], y)
                            else:
                                data[valcount] = (r[xcolname], -r['y'])
                        valcount += 1
                    color = prj_color_map[rs['pprojid']] if len(prj_color_map) > 1 else \
                        (sample_color_map[rs['psampleid']] if len(sample_color_map) < 25 else None)
                    graph[i].plot(data[:valcount, 1], data[:valcount, 0], color=color)
            # fait après les plot pour avoir un echelle X bien callé avec les données
            # et evite les erreurs log si la premiere serie n'as pas de valeurs
            for i, c in enumerate(gpd):
                if gvg('XScale') != 'I':
                    try:
                        if gvg('XScale') == 'O':
                            if profil_vertical:
                                graph[i].set_xscale('log')
                            else:
                                graph[i].set_yscale('log')
                        if gvg('XScale') == 'S':
                            if profil_vertical:
                                graph[i].set_xscale('symlog')
                            else:
                                graph[i].set_yscale('symlog')
                    except Exception as e:
                        # parfois s'il n'y a pas de données pas possible de passer en echelle log,
                        # on force alors linear sinon ça plante plus loin
                        if profil_vertical:
                            graph[i].set_xscale('linear')
                        else:
                            graph[i].set_yscale('linear')
                else:
                    if not time_absolute:
                        graph[i].set_xlim(left=0)

        # traitement des Graphes CTD
        if len(gctd) > 0:
            if profil_vertical:
                sql = "select depth y "
            else:
                if time_absolute:
                    sql = "select datetime y "
                else:
                    # noinspection SqlResolve
                    sql = """select -round(cast(EXTRACT(EPOCH FROM datetime-(select min(datetime) 
                             from part_ctd 
                             where psampleid=%(psampleid)s))/3600 as numeric),2) y """
            sql += ''.join([',%s as c%d' % (c, i) for i, c in enumerate(gctd)])
            sql += """ from part_ctd
             where psampleid=%(psampleid)s
             {}
            order by lineno""".format(depth_filter)
            graph = list(range(0, len(gctd)))
            totvalcount = [0] * len(gctd)
            for i, c in enumerate(gctd):
                graph[i] = fig.add_subplot(fig_size_y, fig_size_x, chartid + 1)
                x_label = 'CTD %s ' % (CTDFixedColByKey.get(c))
                if not profil_vertical:
                    if time_absolute:
                        graph[i].xaxis.set_major_formatter(dateFormaterYMD())
                        x_label = "X : date, Y : " + x_label
                    else:
                        x_label = "X : time (hour), Y : " + x_label
                else:
                    if c == 'datetime':
                        graph[i].xaxis.set_major_formatter(dateFormaterYMD())
                graph[i].set_xlabel(x_label)
                chartid += 1

            for rs in samples:
                db_data = GetAll(sql, {'psampleid': rs['psampleid']})
                data = np.empty((len(db_data), 2))
                for i, c in enumerate(gctd):
                    xcolname = "c%d" % i
                    valcount = 0
                    for rnum, r in enumerate(db_data):
                        if r[xcolname] is None or r['y'] is None:
                            continue
                        if profil_vertical:
                            x_val = r[xcolname]
                            if c == 'datetime':
                                x_val = matplotlib.dates.date2num(x_val)
                            data[valcount] = (-r['y'], x_val)
                        else:
                            if time_absolute:
                                y = matplotlib.dates.date2num(r['y'])
                                data[valcount] = (r[xcolname], y)
                            else:
                                data[valcount] = (r[xcolname], -r['y'])
                        valcount += 1
                    color = prj_color_map[rs['pprojid']] if len(prj_color_map) > 1 else \
                        (sample_color_map[rs['psampleid']] if len(sample_color_map) < 25 else None)
                    graph[i].plot(data[:valcount, 1], data[:valcount, 0], color=color)
                    totvalcount[i] += len(data[:valcount, 1])
            for i in range(len(gctd)):  # permet de gérer l'affichage correct s'il n'y a pas de données en time absolu
                if totvalcount[i] == 0:
                    graph[i].set_xscale('linear')
                    graph[i].set_yscale('linear')

        # traitement des Graphes TAXO
        if len(gtaxo) > 0:
            # sql = "select depth y ,1000*nbr/watervolume as x from part_histocat h "
            sql = "select ph.depth y, ph.nbr as x from part_histocat ph "
            with_taxo_children = gvg('taxochild') == '1'
            sql += " where ph.psampleid = %(psampleid)s  and ph.classif_id in %(taxoid)s "
            sql += " {} order by Y""".format(depth_filter)

            sqlWV = """ select {0} tranche,sum(watervolume) from part_histopart_det 
                    where psampleid=%(psampleid)s {1} group by tranche
                    """.format(GetTaxoHistoWaterVolumeSQLExpr("depth"), depth_filter)
            graph = list(range(0, len(gtaxo)))
            gtaxo_ids = [int(t) for t in gtaxo]
            # On appelle l'API pour avoir les noms à afficher
            taxo_infos = ecotaxa_if.get_taxo3(gtaxo_ids)
            # 1 graphe par taxo demandée
            for i, a_taxo_id in enumerate(gtaxo_ids):
                nom_taxo = taxo_infos[a_taxo_id]["nom"]
                if with_taxo_children:
                    nom_taxo += " and children"
                graph[i] = fig.add_subplot(fig_size_y, fig_size_x, chartid + 1)
                graph[i].set_xlabel('%s #/m3' % (nom_taxo))

                # On pré-calcule le sous-arbre taxo, au besoin
                if with_taxo_children:
                    # TODO: On pourrait accélérer pour les gros sous-arbres en récupérant tous les histo
                    # et en les filtrant par coincidence du lineage
                    taxoids = tuple(ecotaxa_if.get_taxo_subtree(a_taxo_id))
                else:
                    taxoids = (a_taxo_id,)

                # graph[i].set_yscale('log')
                def format_fn(tick_val, tick_pos):
                    if -int(tick_val) < len(DepthTaxoHistoLimit) and -int(tick_val) >= 0:
                        return DepthTaxoHistoLimit[-int(tick_val)]
                    else:
                        return ''

                ##graph[i].yaxis.set_major_formatter(FuncFormatter(format_fn))
                # graph[i].set_yticklabels(GetTaxoHistoLimit(20000))
                # graph[i].set_yticklabels(["a","b","c"])
                # graph[i].yticks(np.arange(5), ('Tom', 'Dick', 'Harry', 'Sally', 'Sue'))
                ##graph[i].set_yticks(np.arange(0,-20,-1))
                chartid += 1
                for isample, rs in enumerate(samples):
                    if rs['visibility'][1] >= 'V':  # Visible ou exportable
                        db_data = GetAll(sql, {'psampleid': rs['psampleid'], 'taxoid': taxoids})
                        wv = GetAssoc2Col(sqlWV, {'psampleid': rs['psampleid']})
                    else:  # si pas le droit, on fait comme s'il n'y avait pas de données.
                        db_data = []
                        wv = {}
                    # print("{} =>{}".format(rs['psampleid'],wv))
                    if len(db_data) > 0:
                        data = np.empty((len(db_data), 2))
                        for rnum, r in enumerate(db_data):
                            data[rnum] = (r['y'], r['x'])
                        # hist,edge=np.histogram(data[:,0],bins=GetTaxoHistoLimit(data[:,0].max()),weights=data[:,1])
                        # Y=(edge[:-1]+edge[1:])/2
                        # graph[i].step(hist,Y)
                        # graph[i].hist(data[:,0],bins=GetTaxoHistoLimit(data[:,0].max()),weights=data[:,1],histtype ='step',orientation ='horizontal')
                        bins = GetTaxoHistoLimit(data[:, 0].max())
                        categ = -np.arange(len(bins) - 1)  # -isample*0.1
                        hist, edge = np.histogram(data[:, 0], bins=bins, weights=data[:, 1])
                        # print(hist)
                        for ih, h in enumerate(hist):
                            if h > 0:
                                if wv.get(edge[ih], 0) > 0:
                                    hist[ih] = 1000 * h / wv.get(edge[ih])
                                else:
                                    hist[ih] = 0
                        # print(hist,edge)
                        # Y=-(edge[:-1]+edge[1:])/2 calcul du milieu de l'espace
                        Y = -edge[:-1]
                        # Y=categ
                        color = prj_color_map[rs['pprojid']] if len(prj_color_map) > 1 else \
                            (sample_color_map[rs['psampleid']] if len(sample_color_map) < 25 else None)
                        graph[i].step(hist, Y, color=color)
                        # bottom, top=graph[i].get_ylim()
                        # bottom=min(bottom,categ.min()-1)
                        # graph[i].set_ylim(bottom, top)
                    bottom, top = graph[i].get_ylim()
                    if gvg('filt_depthmin'):
                        top = -float(gvg('filt_depthmin'))
                    if gvg('filt_depthmax'):
                        bottom = -float(gvg('filt_depthmax'))
                    elif len(wv) > 0:
                        bottom = min(bottom, -max(wv.keys()))
                    if top > 0: top = 0
                    if bottom >= top: bottom = top - 10
                    graph[i].set_ylim(bottom, top)
        # on ajuste la disposition avant de placer le dernier qui est en placement forcé et perturbe le tight_layout
        fig.tight_layout()
        # generation du graphique qui liste les projets
        if len(prj_color_map) > 1:
            data = np.empty((len(prj_sample_count), 2))
            prj_label = []
            g_color = []
            for i, (k, v) in enumerate(prj_sample_count.items()):
                data[i] = i, v
                prj_label.append(prj_title[k])
                g_color.append(prj_color_map[k])
            if profil_vertical:  # chaque ligne fait 500px , la legende basse 55px
                graph = fig.add_subplot(fig_size_y, fig_size_x, (fig_size_y - 1) * fig_size_x + 1,
                                        # 1ère image de la dernière ligne
                                        position=[0.4,  # Left
                                                  55 / (500 * fig_size_y),  # Bottom
                                                  0.25,  # with
                                                  (500 - 85) / (500 * fig_size_y)  # height
                                                    ])
            else:  # chaque ligne fait 300px
                graph = fig.add_subplot(fig_size_y, fig_size_x, (fig_size_y - 1) * fig_size_x + 1,
                                        # 1ère image de la dernière ligne
                                        position=[0.4,  # Left
                                                  55 / (300 * fig_size_y),  # Bottom
                                                  0.25,  # with
                                                  (300 - 85) / (300 * fig_size_y)  # height
                                                    ])
            graph.barh(data[:, 0], data[:, 1], color=g_color)
            graph.set_yticks(np.arange(len(prj_label)) + 0.4)
            graph.set_yticklabels(prj_label)
            graph.set_xlabel("Sample count per project + Legend")
        elif 0 < len(sample_color_map) <= 25:
            data = np.empty((len(samples), 2))
            sample_label = []
            g_color = []
            for i, S in enumerate(samples):
                data[i] = i, 1
                sample_label.append(S['profileid'])
                g_color.append(sample_color_map[S['psampleid']])
            if profil_vertical:  # chaque ligne fait 500px , la legende basse 55px
                graph = fig.add_subplot(fig_size_y, fig_size_x, (fig_size_y - 1) * fig_size_x + 1,
                                        # 1ère image de la dernière ligne
                                        position=[0.4,  # Left
                                                  55 / (500 * fig_size_y),  # Bottom
                                                  0.25,  # with
                                                  (500 - 85) / (500 * fig_size_y)  # height
                                                    ])
            else:  # chaque ligne fait 300px
                graph = fig.add_subplot(fig_size_y, fig_size_x, (fig_size_y - 1) * fig_size_x + 1,
                                        # 1ère image de la dernière ligne
                                        position=[0.4,  # Left
                                                  55 / (300 * fig_size_y),  # Bottom
                                                  0.25,  # with
                                                  (300 - 85) / (300 * fig_size_y)  # height
                                                    ])
            graph.barh(data[:, 0], data[:, 1], color=g_color)
            graph.set_yticks(np.arange(len(sample_label)) + 0.4)
            graph.set_yticklabels(sample_label)
            graph.set_xlabel("Sample Legend")
        elif len(sample_color_map) == 0:
            graph = fig.add_subplot(fig_size_y, fig_size_x, chartid + 1)
            graph.text(0.05, 0.5, "No Data\nor set 'profile type' to 'time series'\nif you handle this kind of data ",
                       fontsize=15, clip_on=True)
        else:
            graph = fig.add_subplot(fig_size_y, fig_size_x, chartid + 1)
            graph.text(0.05, 0.5, "Too many samples,\nLegend not available \nfor too numerous selections\n(N>25)",
                       fontsize=15, clip_on=True)

    except Exception as e:
        fig = plt.figure(figsize=(8, 6), dpi=100)
        tb_list = traceback.format_tb(e.__traceback__)
        s = "%s - %s " % (str(e.__class__), str(e))
        for m in tb_list[::-1]:
            s += "\n" + m
        fig.text(0, 0.5, s)
        print(s)
    png_output = io.BytesIO()
    fig.savefig(png_output)
    png_output.seek(0)
    return send_file(png_output, mimetype='image/png')
