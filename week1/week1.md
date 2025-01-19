---
title: Data Engineering Zoomcamp
subtilte: Week 1 - Docker, GCP
author: Heiner Atze
---

# Introduction to docker

## Docker setup

Setup up a Docker container based on the python image, use the entry point `bash` to install pandas.

``` bash
# On host
docker run -it --entrypoint=bash python:3.9
# Within docker
pip install pandas 
# etc. pp. ... this is not persistent
```

Thus, let's create a Dockerfile

``` dockerfile
FROM python:3.9

RUN pip install pandas

ENTRYPOINT [ "bash" ]
```

Use it to build the container

``` bash
# build from dockerfile
docker build -t test:pandas .
```

## Build a toy pipeline

### Create python script

Let's start to prepare a data pipeline.

``` python
# pipeline.py
import pandas as pd

###
# --- the fance stuff ----
###

print('job finished successfully')
```

Make the `pipeline` available to the docker container

``` dockerfile
#...
WORKDIR /app
COPY pipeline.py pipeline.py
#....
```

### Get a bit more fancy

``` python
# pipeline.py
import sys
import pandas as pd

print(sys.argv)

# extract first commandline arg
day = sys.argv[1]

###
# --- the fance stuff ----
###

print(f'job finished successfully {day}')
```

Change the docker file so that the pipeline is run by the container.

``` dockerfile
#...
ENTRYPOINT ["python", "pipeline.py"]
#....
```