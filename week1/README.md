# Data Engineering Zoomcamp
Heiner Atze

# Introduction to docker

## Docker setup

Setup up a Docker container based on the python image, use the entry
point `bash` to install pandas.

``` bash
# On host
docker run -it --entrypoint=bash python:3.9
# Within docker
pip install pandas 
# etc. pp. ... this is not persistent
```

Thus, let’s create a Dockerfile

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

Let’s start to prepare a data pipeline.

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

See the [`ipynb`
notebook](./2_postgresql_docker/postgresql_pandas.ipynb) for how to load
the dataset to the PostgresSQL database.

## pgAdmin

GUI tool for working for PostgreSQL.

In order to connect pgAdmin to Postgres, both containers have to be in
the same network

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

## Data ingestion script

Convert `ipynb` to `.py` file

``` bash
jupyter nbconvert --to py ./postgresql_pandas.ipynb
mv postgresql_pandas.py ingest_data.py
```

Some clean up, and argparsing, see
[here](./2_postgresql_docker/ingest_data.py)

After deleting `yellow_taxi_data` from Postgres, run the python script

``` bash
URL="https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2021-01.csv.gz"

python ingest_data.py \
  --user=root \
  --password=root \
  --host=localhost \
  --port=5433 \
  --db=ny_taxi \
  --table_name=yellow_taxi_data \
  --url=${URL}
```

## Containerization of the data ingestion

Build the docker container for data ingestion

``` dockerfile
FROM python:3.9

WORKDIR /app
COPY ingest_data.py ingest_data.py

RUN pip install pandas sqlalchemy psycopg2

ENTRYPOINT [ "python", "ingest_data.py" ]
```

Run the container in the `pg-network`, fails otherwise to find th
Postgres server

``` bash
docker run -it \
  --network=pg-network \
  taxi_ingest:v001 \
    --user=root \
    --password=root \
    --host=pg-database \
    --port=5432 \
    --db=ny_taxi \
    --table_name=yellow_taxi_data \
    --url=${URL}
```

## Docker compose - Bringing the containers together

see [docker-compose.yml](./2_postgresql_docker/docker-compose.yml)

## Some SQL

Pull the zone lookup table to postgres using the data ingestion
container

- [x] remove `parse_dates` from `pipeline.py`

``` bash
URL="https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"

docker run -it \
  --network=pg-network \
  taxi_ingest:v001 \
    --user=root \
    --password=root \
    --host=pg-database \
    --port=5432 \
    --db=ny_taxi \
    --table_name=yellow_taxi_data \
    --url=${URL}
```

### Join zones and trip tables

``` r
library(DBI)
con <- DBI::dbConnect( 
               RPostgres::Postgres(),
               dbname = "ny_taxi", 
               host = "localhost", 
               port = "5433", 
               user = "root",
               password = "root"
            )
```

``` sql
--using cartesian product
SELECT 
  "VendorID", tpep_pickup_datetime
FROM
  yellow_taxi_data t,
  --location pickup lpu
  zones lpu,
  --location dropoff
  zones ldo
WHERE
--selection on joining conditions
  t."PULocationID" = lpu."LocationID" AND
  t."DOLocationID" = ldo."LocationID"
LIMIT 10
```

| VendorID | tpep_pickup_datetime |
|---------:|:---------------------|
|        1 | 2021-01-01 00:30:10  |
|        1 | 2021-01-01 00:51:20  |
|        1 | 2021-01-01 00:43:30  |
|        1 | 2021-01-01 00:15:48  |
|        2 | 2021-01-01 00:31:49  |
|        1 | 2021-01-01 00:16:29  |
|        1 | 2021-01-01 00:00:28  |
|        1 | 2021-01-01 00:12:29  |
|        1 | 2021-01-01 00:39:16  |
|        1 | 2021-01-01 00:26:12  |
