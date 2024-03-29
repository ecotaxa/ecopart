# -*- coding: utf-8 -*-
# This file is part of Ecotaxa, see license.md in the application root directory for license informations.
# Copyright (C) 2015-2016  Picheral, Colin, Irisson (UPMC-CNRS)
from flask import Blueprint, render_template, g, request, url_for, redirect
from flask_login import current_user
from appli import app,ObjectToStr,PrintInCharte,database,db
from flask_security.decorators import roles_accepted
import appli.part
import os

# definition d'un second répertoire traité en statique en plus de static
vaultBP = Blueprint('vault', __name__, static_url_path='/vault', static_folder='../vault')
app.register_blueprint(vaultBP)

@app.route('/')
def index():
    # a terme il y aura une page de présentation, mais pour l'instant on renvoi juste vers /part/
    return redirect("/part/", code=302)
    txt="""<div style='margin:5px;'><div id="homeText"'>"""
    #lecture du message de l'application manager
    NomFichier='appli/static/home/appmanagermsg.html'
    if os.path.exists(NomFichier):
        with open(NomFichier, 'r',encoding='utf8') as f:
            message=f.read()
            if len(message)>5:
                txt+="""
                    <div class="alert alert-warning alert-dismissable" role="alert">
                        <button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>
                        <p><strong>Message from the application manager</strong></p>{0}
                    </div>
                """.format(message)
    # Lecture de la partie Haute
    NomFichier='appli/static/home/home.html'
    if not os.path.exists(NomFichier):
        NomFichier='appli/static/home/home-model.html'
    with open(NomFichier, 'r',encoding='utf8') as f:
        txt+=f.read()
    txt+="""
	</div>
	<div class="row" id="homeSelectors" style="margin-top: 20px; margin-bottom: 20px;">
		<div class="col-sm-4">
        <a href="/explore/" class="btn btn-primary btn-lg btn-block">Explore images</a>
		</div>
		<div class="col-sm-4">
        <a href="/prj/" class="btn btn-primary btn-lg  btn-block">Contribute to a project</a>
		</div>		
		<div class="col-sm-4">
        <a href="/part/" class="btn btn-primary btn-lg  btn-block">Particle module</a>
		</div>		
	</div>
"""
    NomFichier='appli/static/home/homebottom.html'
    if not os.path.exists(NomFichier):
        NomFichier='appli/static/home/homebottom-model.html'
    txt+="""<div class="row" id="homeLegal"><div class="col-sm-12">"""
    with open(NomFichier, 'r',encoding='utf8') as f:
        txt+=f.read()
    txt+="""<br><a href='/privacy'>Privacy</a></div></div></div>"""
    return PrintInCharte(txt)


@app.route('/test1')
def test1():
    txt = """Hello World! <span class="glyphicon glyphicon-search" aria-hidden="true"></span>
            <font color=red><span class="glyphicon glyphicon-search" aria-hidden="true"></span></font>
            <span class="glyphicon glyphicon-user" style="color:blue"></span>
            X<br>

           """
    txt += "Name =" + getattr(current_user,'name',"???")+"<br>"
    txt += "Id ="+str(getattr(current_user,'id',-1))+"<br>"
    txt += ObjectToStr(current_user)
    txt += "<br><img src='vault/test.jpg' width=500>"
    return render_template('layout.html',bodycontent=txt)



@app.route('/testadmin')
@roles_accepted(database.AdministratorLabel)
def testadmin():
    return "Admin OK"



@app.before_request
def before_request_security():
    # time.sleep(0.1)
    # print("URL="+request.url)
    # app.logger.info("URL="+request.url)
    g.db=None
    if "/static" in request.url:
        return
    # print(request.form)
    # current_user.is_authenticated
    g.cookieGAOK = request.cookies.get('GAOK', '')
    g.menu = []
    g.menu.append(("/part/","Home / View data"))
    if current_user.is_authenticated:
        g.menu.append(("/part/prj/","Projects management"))
    g.useradmin=False
    g.appliadmin=False
    # Todo réactiver en version finale
    # if current_user.has_role(database.AdministratorLabel) or current_user.has_role(database.ProjectCreatorLabel) :
    #     g.menu.append(("","SEP"))
    #     g.menu.append(("javascript:PostDynForm('/taxo/browse/',{updatestat:'Y'});", "Manage Taxonomy"))
    if current_user.has_role(database.AdministratorLabel) or current_user.has_role(database.UserAdministratorLabel) :
        g.menu.append(("","SEP"))
        g.menu.append(("/admin/","Admin Screen"))
        g.useradmin=True
    if current_user.has_role(database.AdministratorLabel) :
        # g.menu.append(("/Task/Create/TaskTaxoImport","Import Taxonomy"))
        g.menu.append(("/Task/listall","Task Manager"))
        g.appliadmin=True

    # Todo réactiver en version finale
    # g.menu.append(("","SEP"))
    # g.menu.append(("/change","Change Password"))

@app.teardown_appcontext
def before_teardown_commitdb(error):
    try:
        if g.db:
            try:
                g.db.commit()
            except:
                g.db.rollback()
    except Exception as e: # si probleme d'accés à g.db ou d'operation sur la transaction on passe silencieusement
        app.logger.error("before_teardown_commitdb : Unhandled exception (can be safely ignored) : {0} ".format(e))

@app.after_request
def after_request(response):
    response.headers[
        'Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' blob: data: cdnjs.cloudflare.com server.arcgisonline.com www.google.com www.gstatic.com www.google-analytics.com cdn.ckeditor.com cdn.jsdelivr.net;frame-ancestors 'self';form-action 'self';"
    return response