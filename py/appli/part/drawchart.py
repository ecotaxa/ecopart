from flask import request,send_file
from appli import app,database,gvg
import appli.part.part_main as umain
import matplotlib,io,math,traceback,matplotlib.dates,matplotlib.ticker
import matplotlib.pyplot as plt
import numpy as np
from appli.part import PartDetClassLimit,PartRedClassLimit,GetClassLimitTxt,CTDFixedColByKey

DepthTaxoHistoLimit=[0,25,50,75,100,125,150,200,250,300,350,400,450,500,600,700,800,900,1000,1250,1500,1750,2000,2250,2500,2750
    ,3000,3250,3500,3750,4000,4250,4500,4750,5000,5250,5500,5750,6000,7000,8000,9000,10000,11000,12000,13000,14000,15000,20000,50000]
def GetTaxoHistoLimit(MaxDepth):
    Res=[]
    BreakOnNext=False
    for d in DepthTaxoHistoLimit:
        Res.append(d)
        if BreakOnNext:
            break
        if d>MaxDepth:
            BreakOnNext=True
    return Res

def GetTaxoHistoWaterVolumeSQLExpr(field,retval='start'):
    Res="case "
    for i in range(1,len(DepthTaxoHistoLimit)):
        Res +=" when {2}<{0} then {1}".format(DepthTaxoHistoLimit[i]
                  ,DepthTaxoHistoLimit[i-1] if retval=='start' else (DepthTaxoHistoLimit[i-1]+DepthTaxoHistoLimit[i])/2
                  ,field)
    return Res+" end"

# variante de matplotlib.dates.DateFormatter mais qui ne plante pas en cas de zero, ce qui arrive si les graphes sont vides
class dateFormaterYMD(matplotlib.ticker.Formatter):
    def __call__(self, x, pos=0):
        if x<=0:
            return "-"
        return matplotlib.dates.num2date(x).strftime("%Y-%m-%d")

# noinspection DuplicatedCode
@app.route('/part/drawchart')
def part_drawchart():
    Couleurs=("#FF0000","#4385FF","#00BE00","#AA6E28","#FF9900","#FFD8B1","#808000","#FFEA00","#FFFAC8","#BEFF00",
        "#AAFFC3","#008080","#64FFFF","#000080","#800000","#820096","#E6BEFF","#FF00FF","#808080","#FFC9DE","#000000" )
    PrjColorMap={} # chaque projet à une couleur
    PrjSampleCount={}
    PrjTitle={}
    SampleColorMap={} # chaque sample à une couleur s'il n'y a qu'un seul projet
    SampleTitle={}
    try:
        gpr=request.args.getlist('gpr')
        gpd=request.args.getlist('gpd')
        gctd = request.args.getlist('ctd')
        gtaxo = request.args.getlist('taxolb')
        Filter = {k:v for k,v in request.args.items()}
        if Filter.get('filt_proftype','')=='':
            Filter['filt_proftype']='V' # Si pas de filtre sur le type de profil ou tous, alors on met Vertical pour ne pas melanger les 2 ce qui donne des graphes incoherents
        ProfilVertical=Filter.get('filt_proftype', '') == 'V'
        if not ProfilVertical :
            gpd.append('depth') # si ce sont des profils temporels, on ajoute une trace pour les profondeurs
        samples=umain.GetFilteredSamples(Filter=Filter,GetVisibleOnly=True,RequiredPartVisibility='V')
        for S in samples:
            if S['pprojid'] not in PrjColorMap:
                PrjColorMap[S['pprojid']]=Couleurs[len(PrjColorMap)%len(Couleurs)]
                PrjTitle[S['pprojid']]=S['ptitle']
            if S['psampleid'] not in SampleColorMap:
                SampleColorMap[S['psampleid']]=Couleurs[len(SampleColorMap)%len(Couleurs)]
                SampleTitle[S['psampleid']]=S['profileid']
            PrjSampleCount[S['pprojid']]=PrjSampleCount.get(S['pprojid'],0)+1
        # NbrChart += 1 # toujours un graphe en plus à la fin pour la legende ou le message disant pourquoi pas de legende
        NbrChart=len(gpr)+len(gpd)+len(gctd)+len(gtaxo)
        FigSizeX=NbrChart
        TimeAbsolute = False
        if not ProfilVertical and gvg('TimeScale') == 'A':
            TimeAbsolute=True
        if ProfilVertical:
            if NbrChart>4: FigSizeX = 4
        else:
            if NbrChart > 2: FigSizeX = 2
        FigSizeY=math.ceil(NbrChart/FigSizeX)
        FigSizeY+= 1 # toujours un graphe en plus à la fin pour la legende ou le message disant pourquoi pas de legende
        if FigSizeX<2:
            FigSizeX=2 # le graphe de legende fait 2 de largeur même s'il n'y a qu'un graphe
        font = {'family' : 'arial','weight' : 'normal','size'   : 10}
        plt.rc('font', **font)
        plt.rcParams['lines.linewidth'] = 0.5
        if ProfilVertical:
            Fig = plt.figure(figsize=(FigSizeX*4, FigSizeY*5), dpi=100)
        else:
            Fig = plt.figure(figsize=(FigSizeX * 8, FigSizeY * 3), dpi=100)
        chartid=0
        DepthFilter=""
        if gvg('filt_depthmin'):
            DepthFilter += " and depth>=%d"%int(gvg('filt_depthmin'))
        if gvg('filt_depthmax'):
            DepthFilter += " and depth<=%d"%int(gvg('filt_depthmax'))
        # traitement des Graphes particulaire réduit
        if len(gpr)>0:
            if ProfilVertical:
                sql="select depth y "
            else:
                if TimeAbsolute:
                    sql = "select datetime y "
                else:
                    sql = "select -lineno y "
            # sql+=''.join([',case when watervolume>0 then class%02d/watervolume else 0 end as c%s'%(int(c[2:]),i)
            #               for i,c in enumerate(gpr) if c[0:2]=="cl"])
            sql+=''.join([',case when watervolume>0 then class%02d/watervolume else null end as c%s'%(int(c[2:]),i)
                          for i,c in enumerate(gpr) if c[0:2]=="cl"])
            sql+=''.join([',coalesce(biovol%02d) as c%s'%(int(c[2:]),i)
                          for i,c in enumerate(gpr) if c[0:2]=="bv"])
            sql += """ from part_histopart_reduit
             where psampleid=%(psampleid)s
             {}
            order by Y""".format(DepthFilter)
            graph=list(range(0,len(gpr)))
            for i, c in enumerate(gpr):
                graph[i] = Fig.add_subplot(FigSizeY  , FigSizeX , chartid + 1)
                XLabel=""
                if c[0:2] == "cl":
                    XLabel='Particle red. class %s (%s) # l-1'%(c,GetClassLimitTxt(PartRedClassLimit,int(c[2:])))
                if c[0:2] == "bv":
                    XLabel='Biovolume red. class %s (%s) mm3 l-1'%(c,GetClassLimitTxt(PartRedClassLimit,int(c[2:])))
                if not ProfilVertical:
                    if TimeAbsolute:
                        XLabel="X : date, Y : "+XLabel
                    else:
                        XLabel="X : time (hour), Y : "+XLabel
                graph[i].set_xlabel(XLabel)
                chartid += 1
            for rs in samples:
                DBData = database.GetAll(sql, {'psampleid': rs['psampleid']})
                data = np.empty((len(DBData), 2))
                for i, c in enumerate(gpr):
                    xcolname="c%d"%i
                    valcount=0
                    for rnum,r in enumerate(DBData):
                        if r[xcolname] is None or r['y'] is None:
                            continue
                        if ProfilVertical:
                            data[valcount] = (-r['y'], r[xcolname])
                        else:
                            if TimeAbsolute:
                                data[valcount]=(r[xcolname],matplotlib.dates.date2num(r['y']))
                            else:
                                data[valcount] = (r[xcolname],-r['y'])
                        valcount +=1
                    # data = data[~np.isnan(data[:,1]),:] # Supprime les lignes avec une valeur à Nan et fait donc de l'extrapolation linaire
                    # sans cette ligne les null des colonnes cl devient des nan et ne sont pas tracès (rupture de ligne)
                    # cependant l'autre option est de le traiter au niveau de l'import
                    color = PrjColorMap[rs['pprojid']] if len(PrjColorMap) > 1 else \
                        (SampleColorMap[rs['psampleid']] if len(SampleColorMap) <25 else None)
                    graph[i].plot(data[:valcount, 1], data[:valcount, 0], color=color)
            # fait après les plot pour avoir un echelle X bien callé avec les données et evite les erreurs log si la premiere serie n'as pas de valeurs
            for i, c in enumerate(gpr):
                if gvg('XScale') != 'I':
                    try:
                        if gvg('XScale') == 'O':
                            if ProfilVertical: graph[i].set_xscale('log')
                            else: graph[i].set_yscale('log');
                        if gvg('XScale') == 'S':
                            if ProfilVertical: graph[i].set_xscale('symlog')
                            else: graph[i].set_yscale('symlog')
                    except Exception:
                        # parfois s'il n'y a pas de données pas possible de passer en echelle log, on force alors linear sinon ça plante plus loin
                        if ProfilVertical: graph[i].set_xscale('linear')
                        else: graph[i].set_yscale('linear')
                else:
                    if not TimeAbsolute:
                        graph[i].set_xlim(left=0)
        # traitement des Graphes particulaire détaillés
        if len(gpd)>0:
            if ProfilVertical:
                sql="select depth y "
            else:
                if TimeAbsolute:
                    sql = "select datetime y "
                else:
                    sql = "select -lineno y "
            sql+=''.join([',case when watervolume>0 then class%02d/watervolume else 0 end as c%s'%(int(c[2:]),i)
                          for i,c in enumerate(gpd) if c[0:2]=="cl"])
            sql+=''.join([',coalesce(biovol%02d) as c%s'%(int(c[2:]),i)
                          for i,c in enumerate(gpd) if c[0:2]=="bv"])
            sql+=''.join([',-coalesce(depth) as c%s'%i
                          for i,c in enumerate(gpd) if c=="depth"])
            sql += """ from part_histopart_det
             where psampleid=%(psampleid)s
             {}
            order by Y""".format(DepthFilter)
            graph=list(range(0,len(gpd)))
            for i, c in enumerate(gpd):
                graph[i]=Fig.add_subplot(FigSizeY,FigSizeX,chartid+1)
                XLabel=""
                if c[0:2] == "cl":
                    XLabel='Particle det. class %s (%s) # l-1'%(c,GetClassLimitTxt(PartDetClassLimit,int(c[2:])))
                if c[0:2] == "bv":
                    XLabel='Biovolume det. class %s (%s) mm3 l-1'%(c,GetClassLimitTxt(PartDetClassLimit,int(c[2:])))
                if c == "depth":
                    XLabel='pressure [db]'
                if not ProfilVertical:
                    if TimeAbsolute:
                        XLabel="X : date, Y : "+XLabel
                    else:
                        XLabel="X : time (hour), Y : "+XLabel
                graph[i].set_xlabel(XLabel)
                chartid += 1
            for rs in samples:
                DBData = database.GetAll(sql, {'psampleid': rs['psampleid']})
                data = np.empty((len(DBData), 2))
                for i, c in enumerate(gpd):
                    xcolname="c%d"%i
                    valcount = 0
                    for rnum,r in enumerate(DBData):
                        if r[xcolname] is None or r['y'] is None:
                            continue
                        if ProfilVertical:
                            data[valcount] = (-r['y'], r[xcolname])
                        else:
                            if TimeAbsolute:
                                y=matplotlib.dates.date2num(r['y'])
                                data[valcount]=(r[xcolname],y)
                            else:
                                data[valcount] = (r[xcolname],-r['y'])
                        valcount +=1
                    color = PrjColorMap[rs['pprojid']] if len(PrjColorMap) > 1 else \
                        (SampleColorMap[rs['psampleid']] if len(SampleColorMap) <25 else None)
                    graph[i].plot(data[:valcount,1],data[:valcount,0],color=color)
            # fait après les plot pour avoir un echelle X bien callé avec les données et evite les erreurs log si la premiere serie n'as pas de valeurs
            for i, c in enumerate(gpd):
                if gvg('XScale') != 'I':
                    try:
                        if gvg('XScale') == 'O':
                            if ProfilVertical: graph[i].set_xscale('log')
                            else: graph[i].set_yscale('log');
                        if gvg('XScale') == 'S':
                            if ProfilVertical: graph[i].set_xscale('symlog')
                            else: graph[i].set_yscale('symlog')
                    except Exception :
                        # parfois s'il n'y a pas de données pas possible de passer en echelle log, on force alors linear sinon ça plante plus loin
                        if ProfilVertical: graph[i].set_xscale('linear')
                        else: graph[i].set_yscale('linear')
                else:
                    if not TimeAbsolute:
                        graph[i].set_xlim(left=0)

        # traitement des Graphes CTD
        if len(gctd)>0:
            if ProfilVertical:
                sql="select depth y "
            else:
                if TimeAbsolute:
                    sql = "select datetime y "
                else:
                    # noinspection SqlResolve
                    sql = "select -round(cast(EXTRACT(EPOCH FROM datetime-(select min(datetime) from part_ctd where psampleid=%(psampleid)s))/3600 as numeric),2) y "
            sql+=''.join([',%s as c%d'%(c,i) for i,c in enumerate(gctd)])
            sql += """ from part_ctd
             where psampleid=%(psampleid)s
             {}
            order by lineno""".format(DepthFilter)
            graph=list(range(0,len(gctd)))
            for i, c in enumerate(gctd):
                graph[i]=Fig.add_subplot(FigSizeY,FigSizeX,chartid+1)
                XLabel ='CTD %s '%(CTDFixedColByKey.get(c))
                if not ProfilVertical:
                    if TimeAbsolute:
                        XLabel = "X : date, Y : " + XLabel
                    else:
                        XLabel="X : time (hour), Y : "+XLabel
                graph[i].set_xlabel(XLabel)
                chartid += 1

            for rs in samples:
                DBData = database.GetAll(sql, {'psampleid': rs['psampleid']})
                data = np.empty((len(DBData), 2))
                for i, c in enumerate(gctd):
                    xcolname="c%d"%i
                    valcount = 0
                    for rnum,r in enumerate(DBData):
                        if r[xcolname] is None or r['y'] is None:
                            continue
                        if ProfilVertical:
                            data[valcount] = (-r['y'], r[xcolname])
                        else:
                            if TimeAbsolute:
                                y=matplotlib.dates.date2num(r['y'])
                                data[valcount]=(r[xcolname],y)
                            else:
                                data[valcount] = (r[xcolname],-r['y'])
                        valcount +=1
                    color = PrjColorMap[rs['pprojid']] if len(PrjColorMap) > 1 else \
                        (SampleColorMap[rs['psampleid']] if len(SampleColorMap) <25 else None)
                    graph[i].plot(data[:valcount,1],data[:valcount,0],color=color)

        # traitement des Graphes TAXO
        if len(gtaxo)>0:
            if ProfilVertical:
                sql="select depth y "
            else:
                sql = "select lineno y "
                if TimeAbsolute:
                    sql += " ,datetime"
            sql+=" ,nbr as x  from part_histocat h "
            if gvg('taxochild')=='1':
                sql += " join taxonomy t0 on h.classif_id=t0.id "
                for i in range(1,15) :
                    sql += " left join taxonomy t{0} on t{1}.parent_id=t{0}.id ".format(i,i-1)
            sql += " where psampleid=%(psampleid)s  and ( classif_id = %(taxoid)s "
            if gvg('taxochild') == '1':
                for i in range(1, 15):
                    sql += " or t{}.id= %(taxoid)s".format(i)
            sql += " ){} order by Y""".format(DepthFilter)
            if ProfilVertical:
                TaxoHistoWaterVolumeSQLExpr=GetTaxoHistoWaterVolumeSQLExpr("depth")
            else:
                TaxoHistoWaterVolumeSQLExpr = "lineno"
            sqlWV =""" select {0} tranche,sum(watervolume) from part_histopart_det 
                    where psampleid=%(psampleid)s {1} group by tranche
                    """.format(TaxoHistoWaterVolumeSQLExpr,DepthFilter )
            graph=list(range(0,len(gtaxo)))
            for i, c in enumerate(gtaxo):
                NomTaxo = database.GetAll("""select concat(t.name,' (',p.name,')') nom 
                      from taxonomy t 
                      left JOIN taxonomy p on t.parent_id=p.id 
                      where t.id= %(taxoid)s""", {'taxoid': c})[0]['nom']
                if gvg('taxochild') == '1':
                    NomTaxo += " and children"
                graph[i]=Fig.add_subplot(FigSizeY,FigSizeX,chartid+1)
                XLabel =f'{NomTaxo} #/m3'
                if not ProfilVertical:
                    if TimeAbsolute:
                        XLabel="X : date, Y : "+XLabel
                    else:
                        XLabel="X : time (hour), Y : "+XLabel
                graph[i].set_xlabel(XLabel)
                chartid += 1
                for isample,rs in enumerate(samples):
                    if rs['visibility'][1]>='V': # Visible ou exportable
                        DBData = database.GetAll(sql, {'psampleid': rs['psampleid'],'taxoid':c})
                        WV=database.GetAssoc2Col(sqlWV, {'psampleid': rs['psampleid']})
                    else: # si pas le droit, on fait comme s'il n'y avait pas de données.
                        DBData=[]
                        WV = {}
                    if len(DBData)>0:
                        data = np.empty((len(DBData), 2))
                        TimeValues={}
                        for rnum,r in enumerate(DBData):
                            data[rnum]=(r['y'],r['x'])
                            if TimeAbsolute:
                                TimeValues[r['y']]=r['datetime']
                        if ProfilVertical:
                            bins=GetTaxoHistoLimit(data[:,0].max())
                        else:
                            bins = range(int(data[:,0].max())+2)
                        hist,edge=np.histogram(data[:,0],bins=bins,weights=data[:,1])
                        # print(hist)
                        for ih,h in enumerate(hist):
                            if h>0:
                                if WV.get(edge[ih],0)>0:
                                    hist[ih]=1000*h/WV.get(edge[ih])
                                else: hist[ih]=0
                        # print(hist,edge)

                        color = PrjColorMap[rs['pprojid']] if len(PrjColorMap) > 1 else \
                            (SampleColorMap[rs['psampleid']] if len(SampleColorMap) < 25 else None)
                        if  ProfilVertical:
                            Y = -edge[:-1]
                            # noinspection PyCallingNonCallable
                            graph[i].step(hist,Y,color=color)
                        else:
                            if TimeAbsolute :
                                X=np.empty(len(edge)-1)
                                for ie in range(len(X)):
                                    if ie in TimeValues :
                                        X[ie]=matplotlib.dates.date2num(TimeValues.get(ie))
                                    elif ie>0:
                                        X[ie] =X[ie-1]+1/24 # si une valeur temps n'existe pas car générée par histogram

                            else:
                                X = edge[:-1]
                            # noinspection PyCallingNonCallable
                            graph[i].step( X,hist, color=color)
                    bottom, top = graph[i].get_ylim()
                    if ProfilVertical:
                        if gvg('filt_depthmin'):
                            top=-float(gvg('filt_depthmin'))
                        if gvg('filt_depthmax'):
                            bottom=-float(gvg('filt_depthmax'))
                        elif len(WV)>0:
                            bottom =min(bottom,-max(WV.keys()))
                        if top > 0: top = 0
                        if bottom >= top: bottom = top - 10
                        graph[i].set_ylim(bottom, top)
                    graph[i].set_xscale('linear')
                    graph[i].set_yscale('linear')
            if not ProfilVertical:
                for g in graph:
                    bottom, top = g.get_ylim()
                    bottom=0
                    if top<1:
                        top=1
                    if bottom >= top:
                        top = bottom + 1
                    g.set_ylim(bottom, top)

        if TimeAbsolute:
            for g in Fig.axes:
                if g.get_xlim()[0]<0:
                    g.set_xlim(left=1.0, right=2.0) # permet d'eviter les erreurs si pas de données
                g.xaxis.set_major_formatter(dateFormaterYMD())

        # on ajuste la disposition avant de placer le dernier qui est en placement forcé et perturbe le tight_layout
        Fig.tight_layout()
        # generation du graphique qui liste les projets
        if len(PrjColorMap) > 1:
            data = np.empty((len(PrjSampleCount), 2))
            PrjLabel=[]
            GColor=[]
            for i,(k,v) in enumerate(PrjSampleCount.items()):
                data[i]=i,v
                PrjLabel.append(PrjTitle[k])
                GColor.append(PrjColorMap[k])
            if ProfilVertical: # chaque ligne fait 500px , la legende basse 55px
                graph = Fig.add_subplot(FigSizeY, FigSizeX, (FigSizeY-1)*FigSizeX+1 # 1ère image de la dernière ligne
                                        ,position=[0.4 # Left
                                        ,55/(500*FigSizeY) #Bottom
                                        ,0.25 #with
                                        ,(500-85)/(500*FigSizeY) # height
                                                   ])
            else: # chaque ligne fait 300px
                graph = Fig.add_subplot(FigSizeY, FigSizeX, (FigSizeY-1)*FigSizeX+1 # 1ère image de la dernière ligne
                                        ,position=[0.4 # Left
                                        ,55/(300*FigSizeY) #Bottom
                                        ,0.25 #with
                                        ,(300-85)/(300*FigSizeY) # height
                                                   ])
            graph.barh(data[:,0],data[:,1],color=GColor)
            graph.set_yticks(np.arange(len(PrjLabel))+0.4)
            graph.set_yticklabels(PrjLabel)
            graph.set_xlabel("Sample count per project + Legend")
        elif 0<len(SampleColorMap)<=25 :
            data = np.empty((len(samples), 2))
            SampleLabel=[]
            GColor=[]
            for i,S in enumerate(samples):
                data[i]=i,1
                SampleLabel.append(S['profileid'])
                GColor.append(SampleColorMap[S['psampleid']])
            if ProfilVertical: # chaque ligne fait 500px , la legende basse 55px
                graph = Fig.add_subplot(FigSizeY, FigSizeX, (FigSizeY-1)*FigSizeX+1 # 1ère image de la dernière ligne
                                        ,position=[0.4 # Left
                                        ,55/(500*FigSizeY) #Bottom
                                        ,0.25 #with
                                        ,(500-85)/(500*FigSizeY) # height
                                                   ])
            else: # chaque ligne fait 300px
                graph = Fig.add_subplot(FigSizeY, FigSizeX, (FigSizeY-1)*FigSizeX+1 # 1ère image de la dernière ligne
                                        ,position=[0.4 # Left
                                        ,55/(300*FigSizeY) #Bottom
                                        ,0.25 #with
                                        ,(300-85)/(300*FigSizeY) # height
                                                   ])
            graph.barh(data[:,0],data[:,1],color=GColor)
            graph.set_yticks(np.arange(len(SampleLabel))+0.4)
            graph.set_yticklabels(SampleLabel)
            graph.set_xlabel("Sample Legend")
        elif len(SampleColorMap)==0:
            graph = Fig.add_subplot(FigSizeY, FigSizeX, chartid + 1)
            graph.text(0.05, 0.5, "No Data\nor set 'profile type' to 'time series'\nif you handle this kind of data ",fontsize=15, clip_on=True)
        else:
            graph = Fig.add_subplot(FigSizeY, FigSizeX, chartid + 1)
            graph.text(0.05, 0.5, "Too many samples,\nLegend not available \nfor too numerous selections\n(N>25)", fontsize=15, clip_on=True)

    except Exception as e:
        Fig = plt.figure(figsize=(8,6), dpi=100)
        tb_list = traceback.format_tb(e.__traceback__)
        s = "%s - %s "%(str(e.__class__), str(e))
        for m in tb_list[::-1]:
            s += "\n" + m
        Fig.text(0,0.5,s)
        print(s)
    png_output = io.BytesIO()
    Fig.savefig(png_output)
    png_output.seek(0)
    return send_file(png_output, mimetype='image/png')
