---
author:
- Heiner Atze
authors:
- Heiner Atze
subtilte: Week 1 - Docker, GCP
title: Data Engineering Zoomcamp
toc-title: Table of contents
---

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

-   [x] remove `parse_dates` from `pipeline.py`

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

::: cell
``` {.r .cell-code}
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
:::

:::: cell
``` {.sql .cell-code}
--using cartesian product
SELECT 
  *
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
LIMIT 100
```

::: cell-output-display
  -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  index     VendorID tpep_pickup_datetime   tpep_dropoff_datetime     passenger_count   trip_distance   RatecodeID store_and_fwd_flag     PULocationID   DOLocationID   payment_type   fare_amount   extra   mta_tax   tip_amount   tolls_amount   improvement_surcharge   total_amount   congestion_surcharge   index   LocationID Borough     Zone         service_zone     index   LocationID Borough     Zone        service_zone
  ------- ---------- ---------------------- ----------------------- ----------------- --------------- ------------ -------------------- -------------- -------------- -------------- ------------- ------- --------- ------------ -------------- ----------------------- -------------- ---------------------- ------- ------------ ----------- ------------ -------------- ------- ------------ ----------- ----------- --------------
  0                1 2021-01-01 00:30:10    2021-01-01 00:36:12                     1            2.10            1 N                               142             43              2           8.0     3.0       0.5         0.00              0                     0.3          11.80                    2.5     141          142 Manhattan   Lincoln      Yellow Zone         42           43 Manhattan   Central     Yellow Zone
                                                                                                                                                                                                                                                                                                                                                Square East                                                  Park        

  1                1 2021-01-01 00:51:20    2021-01-01 00:52:19                     1            0.20            1 N                               238            151              2           3.0     0.5       0.5         0.00              0                     0.3           4.30                    0.0     237          238 Manhattan   Upper West   Yellow Zone        150          151 Manhattan   Manhattan   Yellow Zone
                                                                                                                                                                                                                                                                                                                                                Side North                                                   Valley      

  2                1 2021-01-01 00:43:30    2021-01-01 01:11:06                     1           14.70            1 N                               132            165              1          42.0     0.5       0.5         8.65              0                     0.3          51.95                    0.0     131          132 Queens      JFK Airport  Airports           164          165 Brooklyn    Midwood     Boro Zone

  3                1 2021-01-01 00:15:48    2021-01-01 00:31:01                     0           10.60            1 N                               138            132              1          29.0     0.5       0.5         6.05              0                     0.3          36.35                    0.0     137          138 Queens      LaGuardia    Airports           131          132 Queens      JFK Airport Airports
                                                                                                                                                                                                                                                                                                                                                Airport                                                                  

  4                2 2021-01-01 00:31:49    2021-01-01 00:48:21                     1            4.94            1 N                                68             33              1          16.5     0.5       0.5         4.06              0                     0.3          24.36                    2.5      67           68 Manhattan   East Chelsea Yellow Zone         32           33 Brooklyn    Brooklyn    Boro Zone
                                                                                                                                                                                                                                                                                                                                                                                                             Heights     

  5                1 2021-01-01 00:16:29    2021-01-01 00:24:30                     1            1.60            1 N                               224             68              1           8.0     3.0       0.5         2.35              0                     0.3          14.15                    2.5     223          224 Manhattan   Stuy         Yellow Zone         67           68 Manhattan   East        Yellow Zone
                                                                                                                                                                                                                                                                                                                                                Town/Peter                                                   Chelsea     
                                                                                                                                                                                                                                                                                                                                                Cooper                                                                   
                                                                                                                                                                                                                                                                                                                                                Village                                                                  

  6                1 2021-01-01 00:00:28    2021-01-01 00:17:28                     1            4.10            1 N                                95            157              2          16.0     0.5       0.5         0.00              0                     0.3          17.30                    0.0      94           95 Queens      Forest Hills Boro Zone          156          157 Queens      Maspeth     Boro Zone

  7                1 2021-01-01 00:12:29    2021-01-01 00:30:34                     1            5.70            1 N                                90             40              2          18.0     3.0       0.5         0.00              0                     0.3          21.80                    2.5      89           90 Manhattan   Flatiron     Yellow Zone         39           40 Brooklyn    Carroll     Boro Zone
                                                                                                                                                                                                                                                                                                                                                                                                             Gardens     

  8                1 2021-01-01 00:39:16    2021-01-01 01:00:13                     1            9.10            1 N                                97            129              4          27.5     0.5       0.5         0.00              0                     0.3          28.80                    0.0      96           97 Brooklyn    Fort Greene  Boro Zone          128          129 Queens      Jackson     Boro Zone
                                                                                                                                                                                                                                                                                                                                                                                                             Heights     

  9                1 2021-01-01 00:26:12    2021-01-01 00:39:46                     2            2.70            1 N                               263            142              1          12.0     3.0       0.5         3.15              0                     0.3          18.95                    2.5     262          263 Manhattan   Yorkville    Yellow Zone        141          142 Manhattan   Lincoln     Yellow Zone
                                                                                                                                                                                                                                                                                                                                                West                                                         Square East 
  -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

  : Displaying records 1 - 10
:::
::::
