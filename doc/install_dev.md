# Installation d'un poste de developpement
Exemple sur la base de Ubuntu 21.04

Installer pycharm 

Installer GIT
```bash
apt-get install git
```


Installer Postgresql 13
```bash
apt-get install postgresql-13
```

Initialiser un password au user postgres
```bash
sudo -u postgres psql
psql (13.4 (Ubuntu 13.4-0ubuntu0.21.04.1))
postgres=# \password
Enter new password: ecopart
Enter it again: ecopart
postgres=# \q
```
Créer le repertoire /ecopart pour mettre l'application
```bash
sudo -i
mkdir /ecopart;chmod 777 /ecopart;chown laurent /ecopart
apt install python3.9-venv
mkdir /ecopartvenv;chmod 777 /ecopartvenv;chown laurent /ecopartvenv
mkdir /ecopartvenvtest;chmod 777 /ecopartvenvtest;chown laurent /ecopartvenvtest
exit
cd /ecopart
git clone https://github.com/ecotaxa/ecopart.git /ecopart
python3 -m venv /ecopartvenv
python3 -m venv /ecopartvenvtest
source /ecopartvenv/bin/activate
pip install -r /ecopart/py/requirements.txt
source /ecopartvenvtest/bin/activate
pip install -r /ecopart/qa/py/requirements.txt
sudo -u postgres psql -c "create database ecopart_tu1;"
mkdir /ecopart/ftparea
chmod -R 777 /ecopart
```
Dans PyCharm 
* Faire un checkout dans /ecopart
* File / Open /ecopart/py
* déclarer l'interpreteur /ecopartvenv
* Copier config-model.cfg en config.cfg et le remplir
  * DB_DATABASE="ecopart_tu1"
  * DB_USER="postgres"
  * DB_PASSWORD="ecopart"
  * SERVERLOADAREA='/ecopart'
  * Fixer SECRET_KEY
* File / Open /ecopart/qa/py
* déclarer l'interpreteur /ecopartvenvtest
* File / settings/project structure/Add Content root -> /ecopart/py

Initialiser la base de données et générer les fichiers d'import pour les tests d'import en lançant qa/py/gendb/GenerateDB.py

Pour lancer l'application, executer /ecopart/py/runserver.py

Login  admin / ecotaxa

Pour tester que ça marche choisir le projet 2 et générer les graphe reduit des classes 6 à 8 et on doit voir un résultat simlaire à cette image https://github.com/ecotaxa/ecopart/blob/master/qa/py/doc/redgraph.png, de façon générale comparer avec https://github.com/ecotaxa/ecopart/blob/master/qa/py/doc/gendb.md

# Test unitaires
Il faut d'abord lancer test_import.py qui fini d'initialiser la base de donnée.

test_export.py permet de comparer les export à un jeu d'export de référence. Il y a des problemes d'arrondi donc la comparaison n'est pas faitr de façon textuelle mais en vérifiant les valeurs avec une tolerance.

# Problemes en cours.
Sous Windows python 3.6 tous les tests fonctionnent.

Sous Linux
* il faut adapter le programme utilisé dans dans la fonction ShowOnWinmerge
* Les tests remote utilisant un mock http et ftp ne marche pas 
