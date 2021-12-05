#
# Investigations fin 2021: Il y a des différences de _comportement_ entre la version production de EcoPart
# et la version contenue dans le repository ecotaxa/ecopart.
#
# La version du repository est couverte par des tests, qui ne passent pas avec le comportement de prod'.
#
# Le drapeau ci-dessous permet de basculer d'un comportement à l'autre.
#
PROD_BEHAVIOR = False
DEV_BEHAVIOR = not PROD_BEHAVIOR
