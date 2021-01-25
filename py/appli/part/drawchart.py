import io
import math
import matplotlib
import matplotlib.dates
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
import traceback
from flask import request, send_file
import appli.part.part_main as umain
from appli import app, database, gvg
from appli.part import PartDetClassLimit, PartRedClassLimit, GetClassLimitTxt, CTDFixedColByKey

DepthTaxoHistoLimit = [0, 25, 50, 75, 100, 125, 150, 200, 250, 300, 350, 400, 450, 500, 600, 700, 800, 900, 1000, 1250,
                       1500, 1750, 2000, 2250, 2500, 2750,
                       3000, 3250, 3500, 3750, 4000, 4250, 4500, 4750, 5000, 5250, 5500, 5750, 6000, 7000, 8000, 9000,
                       10000, 11000,
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
            else (DepthTaxoHistoLimit[i - 1] + DepthTaxoHistoLimit[i]) / 2,
            field)
    return res + " end"


# variante de matplotlib.dates.DateFormatter mais qui ne plante pas en cas de zero
# , ce qui arrive si les graphes sont vides
class dateFormaterYMD(matplotlib.ticker.Formatter):
    def __call__(self, x, pos=0):
        if x <= 0:
            return "-"
        return matplotlib.dates.num2date(x).strftime("%Y-%m-%d")


# noinspection DuplicatedCode
@app.route('/part/drawchart')
def part_drawchart():
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
        # Si pas de filtre sur le type de profil ou tous, alors on met Vertical pour ne pas melanger les 2
        # ce qui donne des graphes incoherents
        if filtre.get('filt_proftype', '') == '':
            filtre['filt_proftype'] = 'V'
        profil_vertical = filtre.get('filt_proftype', '') == 'V'
        if not profil_vertical:
            gpd.append('depth')  # si ce sont des profils temporels, on ajoute une trace pour les profondeurs
        samples = umain.GetFilteredSamples(Filter=filtre, GetVisibleOnly=True, RequiredPartVisibility='V')
        for S in samples:
            if S['pprojid'] not in prj_color_map:
                prj_color_map[S['pprojid']] = couleurs[len(prj_color_map) % len(couleurs)]
                prj_title[S['pprojid']] = S['ptitle']
            if S['psampleid'] not in sample_color_map:
                sample_color_map[S['psampleid']] = couleurs[len(sample_color_map) % len(couleurs)]
                sample_title[S['psampleid']] = S['profileid']
            prj_sample_count[S['pprojid']] = prj_sample_count.get(S['pprojid'], 0) + 1
        nbr_chart = len(gpr) + len(gpd) + len(gctd) + len(gtaxo)
        fig_size_x = nbr_chart
        time_absolute = False
        if not profil_vertical and gvg('TimeScale') == 'A':
            time_absolute = True
        if profil_vertical:
            if nbr_chart > 4:
                fig_size_x = 4
        else:
            if nbr_chart > 2:
                fig_size_x = 2
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
                        x_label = "X : date, Y : " + x_label
                    else:
                        x_label = "X : time (hour), Y : " + x_label
                graph[i].set_xlabel(x_label)
                chartid += 1
            for rs in samples:
                db_data = database.GetAll(sql, {'psampleid': rs['psampleid']})
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
                    except Exception:
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
                        x_label = "X : date, Y : " + x_label
                    else:
                        x_label = "X : time (hour), Y : " + x_label
                graph[i].set_xlabel(x_label)
                chartid += 1
            for rs in samples:
                db_data = database.GetAll(sql, {'psampleid': rs['psampleid']})
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
                    except Exception:
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
            for i, c in enumerate(gctd):
                graph[i] = fig.add_subplot(fig_size_y, fig_size_x, chartid + 1)
                x_label = 'CTD %s ' % (CTDFixedColByKey.get(c))
                if not profil_vertical:
                    if time_absolute:
                        x_label = "X : date, Y : " + x_label
                    else:
                        x_label = "X : time (hour), Y : " + x_label
                graph[i].set_xlabel(x_label)
                chartid += 1

            for rs in samples:
                db_data = database.GetAll(sql, {'psampleid': rs['psampleid']})
                data = np.empty((len(db_data), 2))
                for i, c in enumerate(gctd):
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

        # traitement des Graphes TAXO
        if len(gtaxo) > 0:
            if profil_vertical:
                sql = "select depth y "
            else:
                sql = "select lineno y "
                if time_absolute:
                    sql += " ,datetime"
            sql += " ,nbr as x  from part_histocat h "
            if gvg('taxochild') == '1':
                sql += " join taxonomy t0 on h.classif_id=t0.id "
                for i in range(1, 15):
                    sql += " left join taxonomy t{0} on t{1}.parent_id=t{0}.id ".format(i, i - 1)
            sql += " where psampleid=%(psampleid)s  and ( classif_id = %(taxoid)s "
            if gvg('taxochild') == '1':
                for i in range(1, 15):
                    sql += " or t{}.id= %(taxoid)s".format(i)
            sql += " ){} order by Y""".format(depth_filter)
            if profil_vertical:
                taxo_histo_water_volume_sql_expr = GetTaxoHistoWaterVolumeSQLExpr("depth")
            else:
                taxo_histo_water_volume_sql_expr = "lineno"
            sql_wv = """ select {0} tranche,sum(watervolume) from part_histopart_det 
                    where psampleid=%(psampleid)s {1} group by tranche
                    """.format(taxo_histo_water_volume_sql_expr, depth_filter)
            graph = list(range(0, len(gtaxo)))
            for i, c in enumerate(gtaxo):
                nom_taxo = database.GetAll("""select concat(t.name,' (',p.name,')') nom 
                      from taxonomy t 
                      left JOIN taxonomy p on t.parent_id=p.id 
                      where t.id= %(taxoid)s""", {'taxoid': c})[0]['nom']
                if gvg('taxochild') == '1':
                    nom_taxo += " and children"
                graph[i] = fig.add_subplot(fig_size_y, fig_size_x, chartid + 1)
                x_label = f'{nom_taxo} #/m3'
                if not profil_vertical:
                    if time_absolute:
                        x_label = "X : date, Y : " + x_label
                    else:
                        x_label = "X : time (hour), Y : " + x_label
                graph[i].set_xlabel(x_label)
                chartid += 1
                for isample, rs in enumerate(samples):
                    if rs['visibility'][1] >= 'V':  # Visible ou exportable
                        db_data = database.GetAll(sql, {'psampleid': rs['psampleid'], 'taxoid': c})
                        wv = database.GetAssoc2Col(sql_wv, {'psampleid': rs['psampleid']})
                    else:  # si pas le droit, on fait comme s'il n'y avait pas de données.
                        db_data = []
                        wv = {}
                    if len(db_data) > 0:
                        data = np.empty((len(db_data), 2))
                        time_values = {}
                        for rnum, r in enumerate(db_data):
                            data[rnum] = (r['y'], r['x'])
                            if time_absolute:
                                time_values[r['y']] = r['datetime']
                        if profil_vertical:
                            bins = GetTaxoHistoLimit(data[:, 0].max())
                        else:
                            bins = range(int(data[:, 0].max()) + 2)
                        hist, edge = np.histogram(data[:, 0], bins=bins, weights=data[:, 1])
                        # print(hist)
                        for ih, h in enumerate(hist):
                            if h > 0:
                                if wv.get(edge[ih], 0) > 0:
                                    hist[ih] = 1000 * h / wv.get(edge[ih])
                                else:
                                    hist[ih] = 0
                        # print(hist,edge)

                        color = prj_color_map[rs['pprojid']] if len(prj_color_map) > 1 else \
                            (sample_color_map[rs['psampleid']] if len(sample_color_map) < 25 else None)
                        if profil_vertical:
                            y = -edge[:-1]
                            # noinspection PyCallingNonCallable
                            graph[i].step(hist, y, color=color)
                        else:
                            if time_absolute:
                                x = np.empty(len(edge) - 1)
                                for ie in range(len(x)):
                                    if ie in time_values:
                                        x[ie] = matplotlib.dates.date2num(time_values.get(ie))
                                    elif ie > 0:  # si une valeur temps n'existe pas car générée par histogram
                                        x[ie] = x[ie - 1] + 1 / 24
                            else:
                                x = edge[:-1]
                            # noinspection PyCallingNonCallable
                            graph[i].step(x, hist, color=color)
                    bottom, top = graph[i].get_ylim()
                    if profil_vertical:
                        if gvg('filt_depthmin'):
                            top = -float(gvg('filt_depthmin'))
                        if gvg('filt_depthmax'):
                            bottom = -float(gvg('filt_depthmax'))
                        elif len(wv) > 0:
                            bottom = min(bottom, -max(wv.keys()))
                        if top > 0:
                            top = 0
                        if bottom >= top:
                            bottom = top - 10
                        graph[i].set_ylim(bottom, top)
                    graph[i].set_xscale('linear')
                    graph[i].set_yscale('linear')
            if not profil_vertical:
                for g in graph:
                    bottom, top = g.get_ylim()
                    bottom = 0
                    if top < 1:
                        top = 1
                    if bottom >= top:
                        top = bottom + 1
                    g.set_ylim(bottom, top)

        if time_absolute:
            for g in fig.axes:
                if g.get_xlim()[0] < 0:
                    g.set_xlim(left=1.0, right=2.0)  # permet d'eviter les erreurs si pas de données
                g.xaxis.set_major_formatter(dateFormaterYMD())

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
