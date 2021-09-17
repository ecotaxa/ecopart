# Dictionnaire des données (simplifié)

La plupart des champs sont informatifs ou parlent d'eux même, seul les champs remarquables sont décrits ici.
## part_projects
Contient la liste des projets particulaires
* pprojid : ID du projet particule
* projid : ID du projet EcoTaxa lié (optionnel)
* ptitle : titre du projet particule
* rawfolder : dossier sur le serveur contenant les fichiers particulaires bruts originaux à importer
* remoteXXX : informations de connexion pour se connecter au serveur distant pour les capteurs deposant leurs informations sur un serveur distant

## part_samples
Contient la liste des samples particulaires associés à un projet
* psampleid : ID du sample particulaire
* sampleid : ID du sample lié dans EcoTaxa
* pprojid : lien vers le projet particulaire
* profileid : Identifiant du sample dans la chaine amont
* organizedbydeepth : Spécifie si c'est un sample en profondeur/pression ou temporel, influe sur la façon de desinner les graphes et agreger les données

## part_histopart_det

Contient les histogrammes particulaires détaillés de chaque sample agrégés par tranche d'eau de 5 mètres ou d'une heure.
* psampleid : ID du sample particulaire
* lineno : Identifiant de la ligne d'histogramme. Champ technique pour faire la clé primaire
* depth : Profondeur moyenne de la tranche d'eau. Pour les samples en pression ce sont des tranches d'eau de 5 mètres et le milieu est à 2.5, d'où normalement les valeurs 2.5, 7.5, 12.5, .... Pour les samples temporels c'est la profondeur moyenne des images
* datetime : Date/heure moyenne de la tranche d'eau. Pour les samples temporels c'est le milieu de l'heure puisque les données sont agrégées par heure.
* watervolume : Volume d'eau de l'agregation = `Nbr Image * Volume d'une image`
* class01->45 : Nombre de particules pour chacune des tranches, les tranches sont délimitées par la variable `PartDetClassLimit`
* biovol01->45 : Volume total des particules de cette classe

## part_histopart_reduit
Contient les histogrammes particulaires réduit de chaque sample, en 15 classes au lieu de 45. Les limites de taille de particules sont dans la variable `PartRedClassLimit`

## part_ctd
Contient les lignes des fichiers CTD sans transformation ni agregation.
* psampleid : ID du sample particulaire
* lineno : N° de la ligne dans le fichier CTD
* depth : champ depth dans le fichier CTD
* datetime : champ datetime dans le fichier CTD
* chloro_fluo et suivants : Champs normalisés des fichiers CTD
* extrames01->20 : Champs non normalisés, mapping dans `part_samples.ctd_desc`

## part_histocat
Contient les histogrames par catégorie Zoo. 
* psampleid : ID du sample particulaire
* classif_id : Id Taxonomique EcoTaxa
* lineno : Identifiant de la ligne d'histogramme. Champ technique pour faire la clé primaire
* depth : Idem aux histogrames particulaires
* datetime : Idem aux histogrames particulaires
* watervolume : Volume de la tranche d'eau particulaires
* nbr : Nbr d'objet
* avgesd : ESD moyen des Objets
* totalbiovolume : BioVolume Total des objets

## part_histocat_lst
Contient les catégories Zoologiques présente dans chaque sample afin de faire des recherches plus performantes
* psampleid : ID du sample particulaire
* classif_id : Id Taxonomique EcoTaxa

## Autres tables
Partagées avec EcoTaxa : Utilisateurs, Taches, ...