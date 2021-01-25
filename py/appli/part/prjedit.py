from pathlib import Path
from flask import json, redirect
from flask import render_template, flash, request, g
from flask_login import current_user
from flask_security import login_required
from wtforms import Form, StringField, validators, IntegerField, FloatField, SelectField, TextAreaField
import appli
import appli.part.database as partdatabase
import csv
import re
from appli import app, PrintInCharte, database, gvg, gvp, ErrorFormat
from appli.database import db


class UvpPrjForm(Form):
    ptitle = StringField("Particle Project title")
    rawfolder = StringField("rawfolder")
    ownerid = StringField("Project Owner name")
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


@app.route('/part/prjedit/<int:pprojid>', methods=['get', 'post'])
@login_required
def part_prjedit(pprojid):
    g.headcenter = "<h3>Particle Project Metadata edition</h3>"
    if pprojid > 0:
        model = db.session.query(partdatabase.part_projects).filter_by(pprojid=pprojid).first()
        if model.ownerid != current_user.id and not current_user.has_role(database.AdministratorLabel):
            return PrintInCharte(ErrorFormat("Access Denied"))
    else:
        if not (current_user.has_role(database.AdministratorLabel) or current_user.has_role(
                database.ProjectCreatorLabel)):
            return PrintInCharte(ErrorFormat("Access Denied"))
        model = partdatabase.part_projects()
        model.pprojid = 0
        model.ownerid = current_user.id
        # model.default_depthoffset=1.2
        model.public_visibility_deferral_month = app.config.get('PART_DEFAULT_VISIBLE_DELAY', '')
        model.public_partexport_deferral_month = app.config.get('PART_DEFAULT_GENERAL_EXPORT_DELAY', '')
        model.public_zooexport_deferral_month = app.config.get('PART_DEFAULT_PLANKTON_EXPORT_DELAY', '')

    UvpPrjForm.ownerid = SelectField('Project Owner',
                                     choices=database.GetAll("SELECT id,name FROM users ORDER BY trim(lower(name))"),
                                     coerce=int)
    UvpPrjForm.instrumtype = SelectField('Instrument type',
                                         choices=[(x, x) for x in ("", "uvp5", "uvp6", "lisst", "uvp6remote")])
    UvpPrjForm.projid = SelectField('Ecotaxa Project',
                                    choices=[(0, ''), (-1, 'Create a new EcoTaxa project')] + database.GetAll("""
                                                SELECT projid,concat(title,' (',cast(projid as varchar),')') 
                                                FROM projects ORDER BY lower(title)"""),
                                    coerce=int)
    UvpPrjForm.remote_type = SelectField('Remote type', choices=[(x, x) for x in ("", "ARGO", "TSV LOV")])
    UvpPrjForm.enable_descent_filter = SelectField('Enable descent filter',
                                                   choices=[("", ""), ("Y", "Yes"), ("N", "No")])
    form = UvpPrjForm(request.form, model)
    if gvp('delete') == 'Y':
        try:
            db.session.delete(model)
            db.session.commit()
            return redirect("/part/prj/")
        except:
            flash("You can delete a project only if doesn't have any data (sample,...)", 'error')
            db.session.rollback()
            return redirect("/part/prj/" + str(model.pprojid))
    if request.method == 'POST' and form.validate():
        if pprojid == 0:
            model.pprojid = None
            db.session.add(model)
        for k, v in form.data.items():
            setattr(model, k, v)
        if model.projid == 0:  # 0 permet de dire aucun projet WTForm ne sait pas gére None avec coerce=int
            model.projid = None
        if model.projid == -1:  # création d'un projet Ecotaxa
            model.projid = None
            ecotaxa_project = database.Projects()
            ecotaxa_project.title = model.ptitle  # Nommé comme le projet Particle
            db.session.add(ecotaxa_project)
            db.session.commit()
            ecotaxa_project_member = database.ProjectsPriv()
            ecotaxa_project_member.projid = ecotaxa_project.projid  # L'utilisateur courant est Manager de ce projet
            ecotaxa_project_member.member = current_user.id
            ecotaxa_project_member.privilege = 'Manage'
            db.session.add(ecotaxa_project_member)
            model.projid = ecotaxa_project.projid  # On affecte le nouveau projet au projet Particle.
        db.session.commit()
        return redirect("/part/prj/" + str(model.pprojid))
    # noinspection PyUnresolvedReferences
    return PrintInCharte(render_template("part/prjedit.html", form=form, prjid=model.pprojid))


@app.route('/part/readprojectmeta', methods=['get', 'post'])
@login_required
def part_readprojectmeta():
    res = {}
    server_root = Path(app.config['SERVERLOADAREA'])
    dossier_uvp_path = server_root / gvg('path')
    dir_name = dossier_uvp_path.name
    cruise_file = dossier_uvp_path / "config/cruise_info.txt"
    # app.logger.info("CruiseFile=%s",CruiseFile.as_posix())
    if cruise_file.exists():
        cruise_info_data = appli.DecodeEqualList(cruise_file.open('r').read())
        res['op_name'] = cruise_info_data.get('op_name')
        res['op_email'] = cruise_info_data.get('op_email')
        res['cs_name'] = cruise_info_data.get('cs_name')
        res['cs_email'] = cruise_info_data.get('cs_email')
        res['do_name'] = cruise_info_data.get('do_name')
        res['do_email'] = cruise_info_data.get('do_email')
        res['prj_info'] = cruise_info_data.get('gen_info')
        res['prj_acronym'] = cruise_info_data.get('acron')
    # ConfigFile = DossierUVPPath / "config/uvp5_settings/uvp5_configuration_data.txt"
    # if ConfigFile.exists():
    #     ConfigInfoData = appli.DecodeEqualList(ConfigFile.open('r').read())
    #     res['default_aa']=ConfigInfoData.get('aa_calib')
    #     res['default_exp'] = ConfigInfoData.get('exp_calib')
    #     res['default_volimage'] = ConfigInfoData.get('img_vol')

    m = re.search(R"([^_]+)_(.*)", dir_name)
    if m.lastindex == 2:
        fichier_header = dossier_uvp_path / "meta" / (m.group(1) + "_header_" + m.group(2) + ".txt")
        res['instrumtype'] = m.group(1)
        m = re.search(R"([^_]+)", m.group(2))
        res['default_instrumsn'] = m.group(1)
        if fichier_header.exists():
            lst_samples = []
            with fichier_header.open(encoding="latin_1") as FichierHeaderHandler:
                f = csv.DictReader(FichierHeaderHandler, delimiter=';')
                for r in f:
                    lst_samples.append(r)
                    # print(LstSamples)
            if len(lst_samples) > 0:
                res['cruise'] = lst_samples[0].get('cruise')
                res['ship'] = lst_samples[0].get('ship')
        if res['instrumtype'] == 'uvp5':
            res['default_depthoffset'] = 1.2
    return json.dumps(res)
