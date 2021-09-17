# Présentation générale.

Le but d'EcoPart est d'analyser des données particulaires.

Les particules sent regroupées dans 45 ou 15 classes de taille d'ESD (Diamètre équivalent sphérique) et agrégées en tranche d'eau de 5 mètres ou 1 heure pour les échantillons temporels. On calculera la concentration #/l et le BioVolume mm3 / l

Pour les particules plus grosses (>qqes mm) on utilise la classification taxonomique réalisée dans EcoTaxa et on calcule là aussi des histogrammes 

EcoPart permet de
* Importer différent format d'entrée pour les UVP5/UVP5HD (fichiers BRU),UVP6,LISST, UVP6Remote
* Générer des graphiques d'analyse simplifiés par sample pour valider la qualité ou affiner des jeux de données, la science est faite avec les exports.
* Gérer les métadonnées des samples & projets
* Faire le lien avec EcoTaxa
* Calculer les histogrammes
* Ingérer les fichiers CTD
* tracer des graphiques afin d'avoir un aperçu des données rapide sur un sample suite à son import
* Exporter les données avec différent niveau de précision.


# Import
Différentes routines sont spécifiques au format du fichier d'entrée.

Des fichiers bruts sont conservés dans le vault/partrawXXXX en format compréssé bz2.

Pour les fichiers BRU, c'est une version agregée qui pour chaque image donne le nombre d'objets par taille en pixel + 3 niveaux de gris (ExplodeGreyLevel) alors que le fichier BRU contient une ligne par objet.
UVP6/UVPAPP Utilise le même format, mais c'est juste un changement de forme puisque l'UVP6 stocke le même niveau d'information.
Transformation réalisées par `GenerateRawHistogramUVPAPP` & `GenerateRawHistogram`.
Pour les autres format ce sont les fichiers originaux.

L'import s'occupe aussi d'importer les métadonnées.

`uvp6remote_sample_import.py` intègre la partie communication avec les serveurs (HTTP ou FTP) pour récupérer les données. Executable par un cron avec `partpoolserver` sur `manage.py`.

# Calcul des histogrammes détaillés & Taxonomique

Les LISST et UVP6Remote fournissent directement des histogrammes détaillés.

Pour les UVP `GenerateParticleHistogram` calcule les histogrammes. Le champ `organizedbydeepth` implique de faire des calculs de façon assez différentes, principalement sur la façon de découper en tranche d'eau. Afin d'avoir de bonne performances, les calculs sont réalisés avec Numpy. Cette fonction génère aussi les graphiques.

Les histogrammes taxonomiques sont calculés par `GenerateTaxonomyHistogram` avec des similitudes aux histogrammes particulaires et en récuperant les volumes d'eau de ces derniers. Cependant ici on ne conserve que les tranches d'eau ou il y a des valeurs car contrairement aux particules il n'y a que quelques objets par samples.

Le code est un peu complexe, entre autre à cause de l'utilsiation de numpy, entre autre pour traiter des cas particuliers tels que pas d'image dans une tranche d'eau donnée. Pas d'image mais un objet s'y trouve. Pas mal de commentaires dans le code.

# génération des graphiques
Dans `part_drawchart` on génére une image qui aggrege tous les graphiques générés par mathplotlib. Ce choix a été fait pour des raisons de performances (afficher les graphiques de centaines de samples fait de gros volumes), mais aussi pour ne pas divulger les données détaillées en les transmettant à une librairie JavaScript.

La première partie est liée à la collecte des données en SQL.

Le code est un peu complexe entre autre pour traiter les différences depth/time, temps absolu/relatif, les types d'echelles lineaire/log, les problématiques de graphes à 0 avec des echelles logarithmique. La structure du code est relativement similaire pour les 4 types de graphes (particule réduit/detaillé, CTD, Zoo)

Les histogrammes Taxo, sont representées avec une agrégation sur des tranches non régulières stockées dans `DepthTaxoHistoLimit` qui sont calculées pour le graphique uniquement, les autres types de graphes ne font pas de calculs.

# Export
Réalisé par une tache asynchrone. Code un peu fastidieu lié à la presence de multiples options qui peuvent se combiner et qui sont apparus / disparu au fil des evolutions.
Gestion principalement de 2 formats TSV et ODV, fichiers unifiés ou séparés par sample, fichiers de synthèse.
