#!/bin/bash
# -u 0:0 pour être root
# Add -i for having a console:
#docker run -it --rm \
echo '*************************** VERSION HEAD ****************************'
#docker run -d --restart unless-stopped \
docker run \
-u 0:0 -p 8000:8000 --rm --name ecotpart_gunicorn  \
-e "WEB_CONCURRENCY=2" \
--mount type=bind,source=${PWD}/../py,target=/app  \
ln/ecopart_execenv sh start.sh
# Add this in the end to skip the init
# bash
#--mount type=bind,source=/vieux,target=/vieux  \
#--mount type=bind,source=/var/run/postgresql,target=/var/run/postgresql  \
#--mount type=bind,source=/home/laurent/Devs/ecotaxa/SrvFics/,target=/home/laurent/Devs/ecotaxa/SrvFics \
#--mount type=bind,source=${PWD}/fake_env,target=/ecotaxa_master  \