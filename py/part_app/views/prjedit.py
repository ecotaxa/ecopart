import csv
import re

from flask import json, redirect
from flask import render_template, flash, request, g
from wtforms import Form, StringField, validators, IntegerField, FloatField, SelectField, \
    TextAreaField

from . import part_PrintInCharte
from .. import database as partdatabase, app
from ..app import part_app, db
from ..db_utils import GetAll
from ..http_utils import gvg, gvp, ErrorFormat
from ..remote import EcoTaxaInstance
from ..txt_utils import DecodeEqualList
from ..urls import PART_URL


class UvpPrjForm(Form):
    ptitle = StringField("Particle Project title")
    rawfolder = StringField("rawfolder")
    ownerid = StringField("Project Manager name")
    projid = StringField("Ecotaxa Project")
    instrumtype = StringField("Instrument type")
    op_name = StringField("Operator name")
    op_email = StringField("Operator email")
    cs_name = StringField("Chief scientist name")
    cs_email = StringField("Chief scientist email")
    do_name = StringField("Data owner name")
    do_email = StringField("Data owner email")
    prj_acronym = StringField("Project acronym")
    cruise = StringField("Cruise")
    ship = StringField("Ship")
    default_instrumsn = StringField("default instrum SN")
    default_depthoffset = FloatField("Override depth offset", [validators.Optional(strip_whitespace=True)])
    prj_info = TextAreaField("Project information")
    public_visibility_deferral_month = IntegerField("Privacy delay", [validators.Optional(strip_whitespace=True)])
    public_partexport_deferral_month = IntegerField("General download delay",
                                                    [validators.Optional(strip_whitespace=True)])
    public_zooexport_deferral_month = IntegerField("Plankton annotation download delay",
                                                   [validators.Optional(strip_whitespace=True)])
    remote_url = StringField("Host")
    remote_user = StringField("User")
    remote_password = StringField("Password")
    remote_directory = StringField("Directory on server")
    remote_vectorref = StringField("Additionnal reference of the vector")
    enable_descent_filter = StringField("Enable descent filter")


@part_app.route('/prjedit/<int:pprojid>', methods=['get', 'post'])
def part_prjedit(pprojid):
    ecotaxa_if = EcoTaxaInstance(request)
    ecotaxa_user = ecotaxa_if.get_current_user()
    assert ecotaxa_user is not None  # i.e. @login_required
    g.headcenter = "<h3>Particle Project Metadata edition</h3>"
    if pprojid > 0:
        model = partdatabase.part_projects.query.filter_by(pprojid=pprojid).first()
        if model.ownerid != ecotaxa_user.id and not (2 in ecotaxa_user.can_do):
            return part_PrintInCharte(ecotaxa_if, ErrorFormat("Access Denied"))
    else:
        # <= 0, i.e. 'créer un nouveau projet'
        model = partdatabase.part_projects()
        model.pprojid = 0
        model.ownerid = ecotaxa_user.id
        # model.default_depthoffset=1.2
        model.public_visibility_deferral_month = part_app.config.get('PART_DEFAULT_VISIBLE_DELAY', '')
        model.public_partexport_deferral_month = part_app.config.get('PART_DEFAULT_GENERAL_EXPORT_DELAY', '')
        model.public_zooexport_deferral_month = part_app.config.get('PART_DEFAULT_PLANKTON_EXPORT_DELAY', '')

    all_users = ecotaxa_if.get_all_users()
    all_users.sort(key=lambda u: u[1].lower())
    UvpPrjForm.ownerid = SelectField('Project Manager',
                                     choices=all_users,
                                     coerce=int)
    UvpPrjForm.instrumtype = SelectField('Instrument type',
                                         choices=[(x, x) for x in ("", "uvp5", "uvp6", "lisst", "uvp6remote")])
    
    # Fetch the visible projects to populate the selection list
    zoo_projs = [(prj.projid, "%s (%d)" % (prj.title, prj.projid))
                 for prj in ecotaxa_if.get_visible_projects()]

    # Sort by projid in descending order
    zoo_projs_sorted = sorted(zoo_projs, key=lambda x: x[0], reverse=True)
    
    new_prj_label = 'Create a new EcoTaxa project with same title'
    UvpPrjForm.projid = SelectField('Ecotaxa Project',
                                    choices=[(-1, new_prj_label), (0, '')] + zoo_projs_sorted,
                                    coerce=int)
    UvpPrjForm.remote_type = SelectField('Remote type', choices=[(x, x) for x in ("", "ARGO", "TSV LOV")])
    UvpPrjForm.enable_descent_filter = SelectField('Enable descent filter',
                                                   choices=[("", ""), ("Y", "Yes"), ("N", "No")])
    form = UvpPrjForm(request.form, model)
    if gvp('delete') == 'Y':
        try:
            db.session.delete(model)
            db.session.commit()
            return redirect("%sprj/" % PART_URL)
        except:
            flash("You can delete a project only if doesn't have any data (sample,...)", 'error')
            db.session.rollback()
            return redirect("%sprj/" % PART_URL + str(model.pprojid))
    if request.method == 'POST' and form.validate():
        if pprojid == 0:
            model.pprojid = None
            db.session.add(model)
        for k, v in form.data.items():
            setattr(model, k, v)
        if model.projid == 0:  # 0 permet de dire 'aucun projet' car WTForm ne sait pas gérer None avec coerce=int
            model.projid = None
        if model.projid == -1:  # création d'un projet EcoTaxa avec le même titre
            model.projid = None
            new_projid = ecotaxa_if.create_new_project(model.ptitle)
            if new_projid is None:
                flash("Could not create EcoTaxa project, check your rights.", "error")
            else:
                flash("EcoTaxa project %d created." % new_projid)
            model.projid = new_projid
        db.session.commit()
        return redirect("%sprj/" % PART_URL + str(model.pprojid))
    return part_PrintInCharte(ecotaxa_if, render_template("part/prjedit.html", form=form, prjid=model.pprojid))


@part_app.route('/readprojectmeta', methods=['get', 'post'])
def part_readprojectmeta():
    res = {}
    ServerRoot = app.ServerLoadArea
    DossierUVPPath = ServerRoot / gvg('path')
    DirName = DossierUVPPath.name
    CruiseFile = DossierUVPPath / "config/cruise_info.txt"
    # part_app.logger.info("CruiseFile=%s",CruiseFile.as_posix())
    if CruiseFile.exists():
        CruiseInfoData = DecodeEqualList(CruiseFile.open('r').read())
        res['op_name'] = CruiseInfoData.get('op_name')
        res['op_email'] = CruiseInfoData.get('op_email')
        res['cs_name'] = CruiseInfoData.get('cs_name')
        res['cs_email'] = CruiseInfoData.get('cs_email')
        res['do_name'] = CruiseInfoData.get('do_name')
        res['do_email'] = CruiseInfoData.get('do_email')
        res['prj_info'] = CruiseInfoData.get('gen_info')
        res['prj_acronym'] = CruiseInfoData.get('acron')
    # ConfigFile = DossierUVPPath / "config/uvp5_settings/uvp5_configuration_data.txt"
    # if ConfigFile.exists():
    #     ConfigInfoData = part_app.DecodeEqualList(ConfigFile.open('r').read())
    #     res['default_aa']=ConfigInfoData.get('aa_calib')
    #     res['default_exp'] = ConfigInfoData.get('exp_calib')
    #     res['default_volimage'] = ConfigInfoData.get('img_vol')

    m = re.search(R"([^_]+)_(.*)", DirName)
    if m.lastindex == 2:
        FichierHeader = DossierUVPPath / "meta" / (m.group(1) + "_header_" + m.group(2) + ".txt")
        res['instrumtype'] = m.group(1)
        m = re.search(R"([^_]+)", m.group(2))
        res['default_instrumsn'] = m.group(1)
        if FichierHeader.exists():
            LstSamples = []
            with FichierHeader.open(encoding="latin_1") as FichierHeaderHandler:
                F = csv.DictReader(FichierHeaderHandler, delimiter=';')
                for r in F:
                    LstSamples.append(r)
                    # print(LstSamples)
            if len(LstSamples) > 0:
                res['cruise'] = LstSamples[0].get('cruise')
                res['ship'] = LstSamples[0].get('ship')
        if res['instrumtype'] == 'uvp5':
            res['default_depthoffset'] = 1.2
    return json.dumps(res)
