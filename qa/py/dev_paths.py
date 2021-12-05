#
# Dépendances code de test, on en a besoin pour les tourner
#
from os.path import dirname, realpath
from pathlib import Path

HERE = Path(dirname(realpath(__file__)))

# Le spaghetti, AKA python front-end.
# Le schéma de la base EcoTaxa est là
SPAGH_ROOT = Path(HERE, "../../../ecotaxa_master")
# Si l'assertion ci-dessous casse, il faut faire un checkout de https://github.com/ecotaxa/ecotaxa_dev
# et corriger le chemin ci-dessus.
assert SPAGH_ROOT.exists()

# On va chercher le source de la définition de la DB EcoTaxa, ça permet de vérifier que le checkout est bon
SPAGH_DB_DEF = Path(SPAGH_ROOT, "appli/database.py")
assert SPAGH_DB_DEF.exists()

# Le back-end FastAPI, uvicorn
BACKEND_ROOT = Path(HERE, "../../../ecotaxa_back")
assert BACKEND_ROOT.exists()

# Le script python qui lance le backend, ça permet de vérifier le checkout
BACKEND_RUN = Path(BACKEND_ROOT, "py/run.py").resolve()
assert BACKEND_RUN.exists()

# Le venv pour lancer, ça permet de vérifier le setup
BACKEND_VENV = Path(BACKEND_ROOT, "py/venv38").resolve()
assert BACKEND_VENV.is_dir() and BACKEND_VENV.exists()
