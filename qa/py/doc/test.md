Le répertoire `test` contient des tests

`test_import.py` permet de tester que les imports des fichiers générés par la génération sont conforme en les comparant au projets de références et en testant des valeurs absolues dependantes des jeux de test.

`test_export.py` permet de tester que les export génère les mêmes données que les exports historiques. Permet de valider que le refactoring donne les mêmes résultats.