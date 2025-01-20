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

# PostgreSQL in docker

## Run container

``` bash
docker run -it --rm \
  -e POSTGRES_DB="ny_taxi" \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -v $(pwd)/ny_taxi_postgres_data/:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:13
```

## `pgcli`

``` bash
pgcli -h localhost -p 5433 -u root -d ny_taxi
```

See the [`ipynb` notebook](./2_postgresql_docker/postgresql_pandas.ipynb) for how to load the dataset to the PostgresSQL database.

## pgAdmin

GUI tool for working for PostgreSQL.


In order to connect pgAdmin to Postgres, both containers have to be in the same network

``` bash
docker network create pg-network
```

*Setup in docker*

``` bash
docker run -it \
  -p 127.0.0.1:8081:80 \
  -e PGADMIN_DEFAULT_EMAIL=user@domain.com \
  -e PGADMIN_DEFAULT_PASSWORD=catsarecool \
  --network=pg-network \
  --name=pgadmin \
  dpage/pgadmin4
```

*Restart Postgres container* in the same network

``` bash
docker run -it --rm \
  -e POSTGRES_DB="ny_taxi" \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -v $(pwd)/ny_taxi_postgres_data/:/var/lib/postgresql/data \
  -p 5433:5432 \
  --network=pg-network \
  --name=pg-database \
  postgres:13
```