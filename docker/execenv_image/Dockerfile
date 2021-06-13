FROM ubuntu:18.04 as builder

MAINTAINER laurent_n <ln@altidev.com>

RUN apt-get update

# postgresql-client # for psycopg2
# gcc make file cython3 # for uvloop for uvicorn needs cython needs make
# gfortran libopenblas-dev liblapack-dev requis pour scipy, mais finalement pas utile
RUN apt-get install \
    python3.8 python3-venv python3.8-dev python3.8-venv  \
    postgresql-client \
    gcc make file cython3 \
    --no-install-recommends --yes


# Get reqs from host
COPY requirements.txt ./reqs.txt

# Create venv, mandatory as we switched away from the python bundled with the OS
RUN python3.8 -m venv /venv
# Install
RUN PATH=/venv/bin pip3 install wheel
RUN PATH=/venv/bin:$PATH pip3 install -r reqs.txt

# Strip a bit...
RUN find /venv -name "*.pyc" -delete

##### Switch to target #####
FROM ubuntu:18.04 as target

# mscorefonts Pour avoir arial dans mathplotlib
# Cleanup to save on image size
RUN apt-get update && echo "ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true" | debconf-set-selections  &&\
apt-get install python3.8 python3.8-venv python3.8-distutils ttf-mscorefonts-installer \
libpq5 --no-install-recommends --yes && \
apt-get clean && \
rm -rf /var/lib/apt/lists/* && \
rm -rf /var/log/*

# Copy the venv from builder
RUN mkdir -p /venv
COPY --from=builder --chown=root:root /venv /venv

# Add venv to path
ENV PATH="/venv/bin:$PATH"

# Below should say 'Requirement already satisfied' for each package and their deps
COPY requirements.txt ./reqs.txt
RUN pip3 install -r reqs.txt

# Get source
# LN je prefere monter l'appli en link
#WORKDIR /app/
#COPY py ./
#COPY link.ini /

# Get starting script
COPY execenv_image/start.sh .
RUN chmod +x start.sh
# Make all app world-writable (for .pyc) as we run as non-root
#LN RUN chmod -R a+rw /app /venv

EXPOSE 8000
# The number of gunicorn workers
ENV WEB_CONCURRENCY=8
# Of course the path below is seen from the container. Check your mounts.
# Needed directory content:
# ./appli
# ./appli/config.cfg
# ./temptask
# ./vault
ENV LEGACY_APP='/ecotaxa_master'
#LN CMD ["./start.sh"]
CMD ["sh"]
