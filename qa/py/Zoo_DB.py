#
# Création en mémoire de la structure de tables EcoTaxa
#
# Note: bien évidemment, pyCharm ou autre IDE ne saura pas trop les objets contenus.
#
# L'approche naïve qui consisterait à faire un import à partir du source EcoTaxa front ne marche pas car:
# - import appli.database va faire import appli et choper l'appli flask + toutes ses dépendances
# - les versions de package de EcoPart étant + récentes (c'est bien!), l'import va planter
#
import part_app.app
from dev_paths import SPAGH_DB_DEF


class FakeDB(object):
    pass


defs = open(SPAGH_DB_DEF).readlines()
clean_defs = [a_line for a_line in defs
              if not (a_line.startswith("from appli")
                      or a_line.startswith("from .constants"))]
defs = "".join(clean_defs)
# On simule un import avec le source filtré
globals = {"db": part_app.app.db}
exec(defs, globals)

database = FakeDB()
database.__dict__ = globals
