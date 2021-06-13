#!/bin/bash
#
# Due to Docker fs, we need to copy all sources
#
#LN rsync -avr --delete --exclude-from=not_to_copy.lst ../py/ py/
cp ../py/requirements.txt requirements.txt
cp ../link.ini .
docker build -t ln/ecopart_execenv -f execenv_image/Dockerfile .
#docker build --no-cache -t grololo06/ecotaxaback -f prod_image/Dockerfile .
# once built, replace 2.3 with the version...:
#   docker tag grololo06/ecotaxaback:latest grololo06/ecotaxaback:2.5
#   docker push grololo06/ecotaxaback:2.5
# needing before:
#   docker login
