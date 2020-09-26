from appli import db, database, DecodeEqualList
import typing
from gendb.Postgres import SequenceCache


class ZooProjectGenerator:
    def __init__(self):
        self.TaxoCache = {}
        self.projid = None
        self.Prj: typing.Optional[database.Projects] = None
        self.Acquisid=None
        self.Acq: typing.Optional[database.Acquisitions] = None
        # exemple de valeurs utilisée, issues d'un UVP5 HD project Celter 2019
        self.aa = 0.0043
        self.exp = 1.12
        self.volimage = 1.13
        self.pixel = 0.088
        self.MapAcq = {}  # Mapping ChampDb=>Data
        self.MapObj = {}
        self.RevMapAcq = {}  # Mapping Data=>ChampDb
        self.RevMapObj = {}
        self.obj_seq_cache = SequenceCache(db.session, "seq_objects", 500)
        self.bulk_obj=[]
        self.bulk_objF = []

        self.mappingprocess = """t01=software
t02=date
t03=time
t04=first_img
t05=last_img
t06=pressure_gain
t07=calibration
t08=pixel
t09=upper
t10=gamma
t11=esdmin
t12=esdmax"""
        self.mappingobj = """n01=area
n02=mean
n03=stddev
n04=mode
n05=min
n06=max
n07=x
n08=y
n09=xm
n10=ym
n11=perim.
n12=bx
n13=by
n14=width
n15=height
n16=major
n17=minor
n18=angle
n19=circ.
n20=feret
n21=intden
n22=median
n23=skew
n24=kurt
n25=%area
n26=xstart
n27=ystart
n28=area_exc
n29=fractal
n30=skelarea
n31=slope
n32=histcum1
n33=histcum2
n34=histcum3
n35=xmg5
n36=ymg5
n37=nb1
n38=nb2
n39=nb3
n40=compentropy
n41=compmean
n42=compslope
n43=compm1
n44=compm2
n45=compm3
n46=symetrieh
n47=symetriev
n48=symetriehc
n49=symetrievc
n50=convperim
n51=convarea
n52=fcons
n53=thickr
n54=areai
n55=tag
n56=esd
n57=elongation
n58=range
n59=meanpos
n60=centroids
n61=cv
n62=sr
n63=perimareaexc
n64=feretareaexc
n65=perimferet
n66=perimmajor
n67=circex
n68=cdexc
n69=kurt_mean
n70=skew_mean
n71=convperim_perim
n72=convarea_area
n73=symetrieh_area
n74=symetriev_area
n75=nb1_area
n76=nb2_area
n77=nb3_area
n78=nb1_range
n79=nb2_range
n80=nb3_range
n81=median_mean
n82=median_mean_range
n83=skeleton_area"""
        self.mappingsample = """t01=profileid
t02=cruise
t03=ship
t04=stationid
t05=bottomdepth
t06=ctdrosettefilename
t07=dn
t08=winddir
t09=windspeed
t10=seastate
t11=nebuloussness
t12=yoyo
t13=comment
t14=barcode"""
        self.mappingacq = """t01=sn
t02=volimage
t03=aa
t04=exp
t05=pixel
t06=file_description
t07=tasktype
t08=disktype
t09=shutterspeed
t10=gain
t11=threshold
t12=smbase
t13=smzoo
t14=erase_border_blob
t15=choice
t16=ratio
t17=exposure"""

    def InitializeProject(self, Title, OwnerID=1) -> database.Projects:
        self.Prj = database.Projects()
        self.Prj.title = Title
        self.Prj.visible = True
        self.Prj.status = 'Annotate'
        self.Prj.mappingobj = self.mappingobj
        self.Prj.mappingacq = self.mappingacq
        self.Prj.mappingprocess = self.mappingprocess
        self.Prj.mappingsample = self.mappingsample
        db.session.add(self.Prj)
        db.session.commit()
        self.projid = self.Prj.projid

        ProjPriv=database.ProjectsPriv()
        ProjPriv.projid=self.projid
        ProjPriv.member=OwnerID
        ProjPriv.privilege="Manage"
        db.session.add(ProjPriv)
        db.session.commit()


        self.MapAcq = DecodeEqualList(self.mappingacq)
        self.MapObj = DecodeEqualList(self.mappingobj)
        self.RevMapAcq = {v: k for k, v in self.MapAcq.items()}
        self.RevMapObj = {v: k for k, v in self.MapObj.items()}

        # Creation d'une Acq unique pour le projet
        self.Acq = database.Acquisitions()
        self.Acq.projid = self.projid
        self.Acq.orig_id = 'Acq01'
        setattr(self.Acq, self.RevMapAcq['aa'], self.aa)
        setattr(self.Acq, self.RevMapAcq['exp'], self.exp)
        setattr(self.Acq, self.RevMapAcq['pixel'], self.pixel)
        setattr(self.Acq, self.RevMapAcq['volimage'], self.volimage)
        db.session.add(self.Acq)
        db.session.commit()
        self.Acquisid = self.Acq.acquisid

        return self.Prj

    def GetTaxoByName(self, Name):
        if Name not in self.TaxoCache:
            self.TaxoCache[Name] = database.Taxonomy.query.filter_by(display_name=Name).first().id
        return self.TaxoCache[Name]

    def SaveBulkObjects(self):
        db.session.bulk_save_objects(self.bulk_obj)
        # db.session.commit() # Le commit intermediaire n'as pas d'impact sur le perf
        # Version differente qui prend des dictionnaires au lieu d'objets, pas d'impact significatif en terme de perf
        # Je laisse les 2 approches pour info parfois manipuler un dictionnaire pourrait être plus simple qu'un objet
        db.session.bulk_insert_mappings(database.ObjectsFields,self.bulk_objF,)
        db.session.commit()
        self.bulk_obj=[]
        self.bulk_objF = []

