from appli import database,app,g
from os.path import dirname, realpath,join
from pathlib import Path

# Permet de générer le fichier taxonomy.tsv pour pouvoir l'importer lors de la creation de la base
# Ne devrait être executé que occasionnelement

with app.app_context():
    g.db = None
    HERE = Path(dirname(realpath(__file__)))
    TargetFile=realpath(join(HERE,"..", "..", "data","taxonomy.tsv"))
    sql="copy taxonomy(id, parent_id, name, id_source, display_name, lastupdate_datetime, id_instance, rename_to, source_url, source_desc, creator_email, creation_datetime, nbrobj, nbrobjcum) to '"+TargetFile+"'"
    database.ExecSQL(sql)