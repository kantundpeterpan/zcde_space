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

------------------------------------------------------------------------

<details>
<summary>
Setup quarto SQL connection
</summary>

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

</details>

------------------------------------------------------------------------

``` sql
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
LIMIT 10
```

| index | VendorID | tpep_pickup_datetime | tpep_dropoff_datetime | passenger_count | trip_distance | RatecodeID | store_and_fwd_flag | PULocationID | DOLocationID | payment_type | fare_amount | extra | mta_tax | tip_amount | tolls_amount | improvement_surcharge | total_amount | congestion_surcharge | index | LocationID | Borough | Zone | service_zone | index | LocationID | Borough | Zone | service_zone |
|---:|---:|:---|:---|---:|---:|---:|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---|:---|:---|---:|---:|:---|:---|:---|
| 0 | 1 | 2021-01-01 00:30:10 | 2021-01-01 00:36:12 | 1 | 2.10 | 1 | N | 142 | 43 | 2 | 8.0 | 3.0 | 0.5 | 0.00 | 0 | 0.3 | 11.80 | 2.5 | 141 | 142 | Manhattan | Lincoln Square East | Yellow Zone | 42 | 43 | Manhattan | Central Park | Yellow Zone |
| 1 | 1 | 2021-01-01 00:51:20 | 2021-01-01 00:52:19 | 1 | 0.20 | 1 | N | 238 | 151 | 2 | 3.0 | 0.5 | 0.5 | 0.00 | 0 | 0.3 | 4.30 | 0.0 | 237 | 238 | Manhattan | Upper West Side North | Yellow Zone | 150 | 151 | Manhattan | Manhattan Valley | Yellow Zone |
| 2 | 1 | 2021-01-01 00:43:30 | 2021-01-01 01:11:06 | 1 | 14.70 | 1 | N | 132 | 165 | 1 | 42.0 | 0.5 | 0.5 | 8.65 | 0 | 0.3 | 51.95 | 0.0 | 131 | 132 | Queens | JFK Airport | Airports | 164 | 165 | Brooklyn | Midwood | Boro Zone |
| 3 | 1 | 2021-01-01 00:15:48 | 2021-01-01 00:31:01 | 0 | 10.60 | 1 | N | 138 | 132 | 1 | 29.0 | 0.5 | 0.5 | 6.05 | 0 | 0.3 | 36.35 | 0.0 | 137 | 138 | Queens | LaGuardia Airport | Airports | 131 | 132 | Queens | JFK Airport | Airports |
| 4 | 2 | 2021-01-01 00:31:49 | 2021-01-01 00:48:21 | 1 | 4.94 | 1 | N | 68 | 33 | 1 | 16.5 | 0.5 | 0.5 | 4.06 | 0 | 0.3 | 24.36 | 2.5 | 67 | 68 | Manhattan | East Chelsea | Yellow Zone | 32 | 33 | Brooklyn | Brooklyn Heights | Boro Zone |
| 5 | 1 | 2021-01-01 00:16:29 | 2021-01-01 00:24:30 | 1 | 1.60 | 1 | N | 224 | 68 | 1 | 8.0 | 3.0 | 0.5 | 2.35 | 0 | 0.3 | 14.15 | 2.5 | 223 | 224 | Manhattan | Stuy Town/Peter Cooper Village | Yellow Zone | 67 | 68 | Manhattan | East Chelsea | Yellow Zone |
| 6 | 1 | 2021-01-01 00:00:28 | 2021-01-01 00:17:28 | 1 | 4.10 | 1 | N | 95 | 157 | 2 | 16.0 | 0.5 | 0.5 | 0.00 | 0 | 0.3 | 17.30 | 0.0 | 94 | 95 | Queens | Forest Hills | Boro Zone | 156 | 157 | Queens | Maspeth | Boro Zone |
| 7 | 1 | 2021-01-01 00:12:29 | 2021-01-01 00:30:34 | 1 | 5.70 | 1 | N | 90 | 40 | 2 | 18.0 | 3.0 | 0.5 | 0.00 | 0 | 0.3 | 21.80 | 2.5 | 89 | 90 | Manhattan | Flatiron | Yellow Zone | 39 | 40 | Brooklyn | Carroll Gardens | Boro Zone |
| 8 | 1 | 2021-01-01 00:39:16 | 2021-01-01 01:00:13 | 1 | 9.10 | 1 | N | 97 | 129 | 4 | 27.5 | 0.5 | 0.5 | 0.00 | 0 | 0.3 | 28.80 | 0.0 | 96 | 97 | Brooklyn | Fort Greene | Boro Zone | 128 | 129 | Queens | Jackson Heights | Boro Zone |
| 9 | 1 | 2021-01-01 00:26:12 | 2021-01-01 00:39:46 | 2 | 2.70 | 1 | N | 263 | 142 | 1 | 12.0 | 3.0 | 0.5 | 3.15 | 0 | 0.3 | 18.95 | 2.5 | 262 | 263 | Manhattan | Yorkville West | Yellow Zone | 141 | 142 | Manhattan | Lincoln Square East | Yellow Zone |

*Select columns of interest and merge `Zone` and `Borough`*

``` sql
--using cartesian product
SELECT 
  t.tpep_pickup_datetime,
  t.tpep_dropoff_datetime,
  lpu."Zone" || ' / ' || lpu."Borough" as pickup_loc,
  ldo."Zone" || ' / ' || ldo."Borough" as dropoff_loc
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

| tpep_pickup_datetime | tpep_dropoff_datetime | pickup_loc | dropoff_loc |
|:---|:---|:---|:---|
| 2021-01-01 00:30:10 | 2021-01-01 00:36:12 | Lincoln Square East / Manhattan | Central Park / Manhattan |
| 2021-01-01 00:51:20 | 2021-01-01 00:52:19 | Upper West Side North / Manhattan | Manhattan Valley / Manhattan |
| 2021-01-01 00:43:30 | 2021-01-01 01:11:06 | JFK Airport / Queens | Midwood / Brooklyn |
| 2021-01-01 00:15:48 | 2021-01-01 00:31:01 | LaGuardia Airport / Queens | JFK Airport / Queens |
| 2021-01-01 00:31:49 | 2021-01-01 00:48:21 | East Chelsea / Manhattan | Brooklyn Heights / Brooklyn |
| 2021-01-01 00:16:29 | 2021-01-01 00:24:30 | Stuy Town/Peter Cooper Village / Manhattan | East Chelsea / Manhattan |
| 2021-01-01 00:00:28 | 2021-01-01 00:17:28 | Forest Hills / Queens | Maspeth / Queens |
| 2021-01-01 00:12:29 | 2021-01-01 00:30:34 | Flatiron / Manhattan | Carroll Gardens / Brooklyn |
| 2021-01-01 00:39:16 | 2021-01-01 01:00:13 | Fort Greene / Brooklyn | Jackson Heights / Queens |
| 2021-01-01 00:26:12 | 2021-01-01 00:39:46 | Yorkville West / Manhattan | Lincoln Square East / Manhattan |

*Use the `JOIN` keyword*

``` sql
SELECT 
  t.tpep_pickup_datetime,
  t.tpep_dropoff_datetime,
  lpu."Zone" || ' / ' || lpu."Borough" as pickup_loc,
  ldo."Zone" || ' / ' || ldo."Borough" as dropoff_loc
FROM
  yellow_taxi_data t JOIN zones lpu
    ON t."PULocationID" = lpu."LocationID"
  JOIN zones ldo
    on t."DOLocationID" = ldo."LocationID"
LIMIT 10
```

| tpep_pickup_datetime | tpep_dropoff_datetime | pickup_loc | dropoff_loc |
|:---|:---|:---|:---|
| 2021-01-01 00:30:10 | 2021-01-01 00:36:12 | Lincoln Square East / Manhattan | Central Park / Manhattan |
| 2021-01-01 00:51:20 | 2021-01-01 00:52:19 | Upper West Side North / Manhattan | Manhattan Valley / Manhattan |
| 2021-01-01 00:43:30 | 2021-01-01 01:11:06 | JFK Airport / Queens | Midwood / Brooklyn |
| 2021-01-01 00:15:48 | 2021-01-01 00:31:01 | LaGuardia Airport / Queens | JFK Airport / Queens |
| 2021-01-01 00:31:49 | 2021-01-01 00:48:21 | East Chelsea / Manhattan | Brooklyn Heights / Brooklyn |
| 2021-01-01 00:16:29 | 2021-01-01 00:24:30 | Stuy Town/Peter Cooper Village / Manhattan | East Chelsea / Manhattan |
| 2021-01-01 00:00:28 | 2021-01-01 00:17:28 | Forest Hills / Queens | Maspeth / Queens |
| 2021-01-01 00:12:29 | 2021-01-01 00:30:34 | Flatiron / Manhattan | Carroll Gardens / Brooklyn |
| 2021-01-01 00:39:16 | 2021-01-01 01:00:13 | Fort Greene / Brooklyn | Jackson Heights / Queens |
| 2021-01-01 00:26:12 | 2021-01-01 00:39:46 | Yorkville West / Manhattan | Lincoln Square East / Manhattan |

### Data Integrity checks

*Are there `NULL` values in the `DOLocationID` or `PULocationID`
columns?*

``` sql
SELECT 
  SUM(
    CASE WHEN "PULocationID" IS NULL THEN 1
         WHEN "DOLocationID" IS NULL THEN 1
         ELSE 0 END
  ) as null_locations
FROM
  yellow_taxi_data
```

| null_locations |
|---------------:|
|              0 |

*Are there unknown locations referenced in the `DOLocationID` or
`PULocationID` columns?*

``` sql
SELECT 
  SUM(
    CASE WHEN "PULocationID" NOT IN (
        SELECT "LocationID" FROM zones
    ) THEN 1
         WHEN "DOLocationID" NOT IN (
        SELECT "LocationID" FROM zones
    ) THEN 1
         ELSE 0 END
  ) as no_unreferenced_location
FROM
  yellow_taxi_data
```

| no_unreferenced_location |
|-------------------------:|
|                        0 |

*Create some trips that reference an unknown location*

- Choose a location from the `zones` table

``` sql
SELECT 
  *
FROM
  zones
WHERE 
  "LocationID" = 142
```

| index | LocationID | Borough   | Zone                | service_zone |
|------:|-----------:|:----------|:--------------------|:-------------|
|   141 |        142 | Manhattan | Lincoln Square East | Yellow Zone  |

- Delete a location from the `zones` table

``` sql
DELETE FROM
  zones
WHERE 
  "LocationID" = 142
```

- rerun the integrity check

``` sql
SELECT 
  SUM(
    CASE WHEN "PULocationID" NOT IN (
        SELECT "LocationID" FROM zones
    ) THEN 1
         WHEN "DOLocationID" NOT IN (
        SELECT "LocationID" FROM zones
    ) THEN 1
         ELSE 0 END
  ) as no_unreferenced_location
FROM
  yellow_taxi_data
```

| no_unreferenced_location |
|-------------------------:|
|                    77846 |

- use a `LEFT JOIN` to return all trips irrespective of whether the
  `LocationID` is referenced in `zones`

``` sql
SELECT 
  t.tpep_pickup_datetime,
  t.tpep_dropoff_datetime,
  lpu."Zone" || ' / ' || lpu."Borough" as pickup_loc,
  ldo."Zone" || ' / ' || ldo."Borough" as dropoff_loc
FROM
  yellow_taxi_data t LEFT JOIN zones lpu
    ON t."PULocationID" = lpu."LocationID"
  LEFT JOIN zones ldo
    on t."DOLocationID" = ldo."LocationID"
LIMIT 10
```

| tpep_pickup_datetime | tpep_dropoff_datetime | pickup_loc | dropoff_loc |
|:---|:---|:---|:---|
| 2021-01-01 00:30:10 | 2021-01-01 00:36:12 | NA | Central Park / Manhattan |
| 2021-01-01 00:51:20 | 2021-01-01 00:52:19 | Upper West Side North / Manhattan | Manhattan Valley / Manhattan |
| 2021-01-01 00:43:30 | 2021-01-01 01:11:06 | JFK Airport / Queens | Midwood / Brooklyn |
| 2021-01-01 00:15:48 | 2021-01-01 00:31:01 | LaGuardia Airport / Queens | JFK Airport / Queens |
| 2021-01-01 00:31:49 | 2021-01-01 00:48:21 | East Chelsea / Manhattan | Brooklyn Heights / Brooklyn |
| 2021-01-01 00:16:29 | 2021-01-01 00:24:30 | Stuy Town/Peter Cooper Village / Manhattan | East Chelsea / Manhattan |
| 2021-01-01 00:00:28 | 2021-01-01 00:17:28 | Forest Hills / Queens | Maspeth / Queens |
| 2021-01-01 00:12:29 | 2021-01-01 00:30:34 | Flatiron / Manhattan | Carroll Gardens / Brooklyn |
| 2021-01-01 00:39:16 | 2021-01-01 01:00:13 | Fort Greene / Brooklyn | Jackson Heights / Queens |
| 2021-01-01 00:26:12 | 2021-01-01 00:39:46 | Yorkville West / Manhattan | NA |

- put the location back

``` sql
INSERT INTO zones (index, "LocationID", "Borough", "Zone", service_zone)
  VALUES(141, 142, 'Manhattan', 'Lincoln Square East', 'Yellow Zone')
```

## Count trips per day

``` sql
SELECT 
  -- DATE_TRUNC('DAY', t.tpep_dropoff_datetime) as day
  CAST(t.tpep_dropoff_datetime AS DATE) as "day",
  "DOLocationID",
  COUNT(1) as "count",
  MAX(total_amount) as max_amount,
  MAX(passenger_count) max_no_pass
FROM
  yellow_taxi_data t
WHERE EXTRACT(YEAR FROM t.tpep_dropoff_datetime) = 2021
GROUP BY
  -- CAST(t.tpep_dropoff_datetime AS DATE)
  1,2
ORDER BY "day" ASC, "DOLocationID" ASC
LIMIT 10
```

| day        | DOLocationID | count | max_amount | max_no_pass |
|:-----------|-------------:|------:|-----------:|------------:|
| 2021-01-01 |            1 |    29 |     147.30 |           6 |
| 2021-01-01 |            3 |    11 |      70.80 |           3 |
| 2021-01-01 |            4 |   149 |      66.36 |           6 |
| 2021-01-01 |            6 |     1 |      65.92 |           4 |
| 2021-01-01 |            7 |   126 |      53.75 |           6 |
| 2021-01-01 |            9 |     6 |      42.80 |           1 |
| 2021-01-01 |           10 |    44 |      68.10 |           6 |
| 2021-01-01 |           11 |     2 |      41.30 |           5 |
| 2021-01-01 |           12 |    13 |      26.16 |           3 |
| 2021-01-01 |           13 |    94 |      76.78 |           6 |

# Introduction to Terraform

- Infrastructure as code
- Terraform uses files to define resources and infrastructure
- the then be used to deploy the defined infrastructure on a chosen
  cloud providers

## Terraform key commands

- `init`

  Get the needed provides

- `plan`

  lay out what is going to happen

- `apply`

  do it

- `destroy`

  bring all resources down

### Main terraform setup

see [main.tf](./3_intro_terraform/main.tf)

- use and environment variable to the credentials for GCP

``` bash
export GOOGLE_CREDENTIALS='/home/ .... /.json'
```

- define resources

- check with `terraform plan`

- deploy with `terraform apply`

- destroy with `terraform destroy`

## Create a BigQuery dataset

## Working with Variables

use [`variables.tf`](./3_intro_terraform/variables.tf) file

variables can then be accessed using `var.` notation

# Homework

## Question 1. Understanding docker first run

Run docker with the `python:3.12.8` image in an interactive mode, use
the entrypoint `bash`.

What’s the version of `pip` in the image?

- [x] 24.3.1
- [ ] 24.2.1
- [ ] 23.3.1
- [ ] 23.2.1

*Solution*

``` bash
docker run -it --rm python:3.12.8 pip --version
```

## Question 2. Understanding Docker networking and docker-compose

Given the following `docker-compose.yaml`, what is the `hostname` and
`port` that **pgadmin** should use to connect to the postgres database?

``` yaml
services:
  db:
    container_name: postgres
    image: postgres:17-alpine
    environment:
      POSTGRES_USER: 'postgres'
      POSTGRES_PASSWORD: 'postgres'
      POSTGRES_DB: 'ny_taxi'
    ports:
      - '5433:5432'
    volumes:
      - vol-pgdata:/var/lib/postgresql/data

  pgadmin:
    container_name: pgadmin
    image: dpage/pgadmin4:latest
    environment:
      PGADMIN_DEFAULT_EMAIL: "pgadmin@pgadmin.com"
      PGADMIN_DEFAULT_PASSWORD: "pgadmin"
    ports:
      - "8080:80"
    volumes:
      - vol-pgadmin_data:/var/lib/pgadmin  

volumes:
  vol-pgdata:
    name: vol-pgdata
  vol-pgadmin_data:
    name: vol-pgadmin_data
```

- [ ] postgres:5433
- [ ] localhost:5432
- [ ] db:5433
- [ ] postgres:5432
- [x] db:5432

## Prepare Postgres

Run Postgres and load data as shown in the videos We’ll use the green
taxi trips from October 2019:

``` bash
wget https://github.com/DataTalksClub/nyc-tlc-data/releases/download/green/green_tripdata_2019-10.csv.gz
```

You will also need the dataset with zones:

``` bash
wget https://github.com/DataTalksClub/nyc-tlc-data/releases/download/misc/taxi_zone_lookup.csv
```

Download this data and put it into Postgres.

You can use the code from the course. It’s up to you whether you want to
use Jupyter or a python script.

This needed some changes to the
[`ingest_data.py`](./2_postgresql_docker/ingest_data.py) script which
now takes the datetime columns as argument.

``` bash
URL="https://github.com/DataTalksClub/nyc-tlc-data/releases/download/green/green_tripdata_2019-10.csv.gz"

docker run -it \
  --network=pg-network \
  taxi_ingest:v003 \
    --user=root \
    --password=root \
    --host=pgdatabase \
    --port=5432 \
    --db=ny_taxi \
    --table_name=green_taxi_data_2019 \
    --dt_cols="lpep_pickup_datetime,lpep_dropoff_datetime" \
    --url=${URL}
```

## Question 3. Trip Segmentation Count

During the period of October 1st 2019 (inclusive) and November 1st 2019
(exclusive), how many trips, **respectively**, happened:

1.  Up to 1 mile
2.  In between 1 (exclusive) and 3 miles (inclusive),
3.  In between 3 (exclusive) and 7 miles (inclusive),
4.  In between 7 (exclusive) and 10 miles (inclusive),
5.  Over 10 miles

*Solution*

``` sql
SELECT
  SUM(
    CASE WHEN trip_distance <= 1 THEN 1 ELSE 0 END
  ) as answer1,
  SUM(
    CASE WHEN trip_distance > 1 AND trip_distance <= 3 THEN 1 ELSE 0 END
  ) as answer2,
  SUM(
    CASE WHEN trip_distance > 3 AND trip_distance <= 7 THEN 1 ELSE 0 END
  ) as answer3,
  SUM(
    CASE WHEN trip_distance > 7 AND trip_distance <= 10 THEN 1 ELSE 0 END
  ) as answer4,
  SUM(
    CASE WHEN trip_distance > 10 THEN 1 ELSE 0 END
  ) as answer5
FROM green_taxi_data_2019
```

| answer1 | answer2 | answer3 | answer4 | answer5 |
|--------:|--------:|--------:|--------:|--------:|
|  104838 |  199013 |  109645 |   27688 |   35202 |

Answers:

- [ ] 104,802; 197,670; 110,612; 27,831; 35,281
- [ ] 104,802; 198,924; 109,603; 27,678; 35,189
- [ ] 104,793; 201,407; 110,612; 27,831; 35,281
- [ ] 104,793; 202,661; 109,603; 27,678; 35,189
- [x] 104,838; 199,013; 109,645; 27,688; 35,202

## Question 4. Longest trip for each day

Which was the pick up day with the longest trip distance? Use the pick
up time for your calculations.

Tip: For every day, we only care about one single trip with the longest
distance.

*Solution*

``` sql
SELECT
  CAST(lpep_pickup_datetime AS DATE) as "day",
  trip_distance
FROM public.green_taxi_data_2019
WHERE trip_distance = (
  SELECT 
    MAX(trip_distance)
  FROM green_taxi_data_2019
)
```

| day        | trip_distance |
|:-----------|--------------:|
| 2019-10-31 |        515.89 |

- [ ] 2019-10-11
- [ ] 2019-10-24
- [ ] 2019-10-26
- [x] 2019-10-31

## Question 5. Three biggest pickup zones

Which were the top pickup locations with over 13,000 in `total_amount`
(across all trips) for 2019-10-18?

Consider only `lpep_pickup_datetime` when filtering by date.

*Solution*

``` sql
WITH amount_per_id AS (
    SELECT
      "PULocationID",
      SUM(total_amount) as total
    FROM green_taxi_data_2019
    WHERE CAST(lpep_pickup_datetime AS date) = '2019-10-18'
    GROUP BY "PULocationID"
    ORDER BY SUM(total_amount) DESC
    FETCH FIRST 3 ROWS ONLY
)

SELECT
  z."Zone"
FROM 
  amount_per_id a
JOIN
  zones z
ON
  a."PULocationID" = z."LocationID"
```

| Zone                |
|:--------------------|
| East Harlem North   |
| East Harlem South   |
| Morningside Heights |

- [x] East Harlem North, East Harlem South, Morningside Heights
- [ ] East Harlem North, Morningside Heights
- [ ] Morningside Heights, Astoria Park, East Harlem South
- [ ] Bedford, East Harlem North, Astoria Park

## Question 6. Largest tip

For the passengers picked up in October 2019 in the zone named “East
Harlem North” which was the drop off zone that had the largest tip?

Note: it’s `tip` , not `trip`

We need the name of the zone, not the ID.

<details>
<summary>
*Solution using subqueries*
</summary>

``` sql
SELECT
  z."Zone"
FROM
  green_taxi_data_2019 y
JOIN
  zones z
ON
--get name of dropoff location
  y."DOLocationID" = z."LocationID"
--filter pickup location to East Harlem North
WHERE "PULocationID" = (
  SELECT
    "LocationID"
  FROM
    zones
  WHERE "Zone" = 'East Harlem North'
) AND
--filter on tip_amount=MAX(tip_amount)
tip_amount = (
  SELECT MAX(tip_amount) FROM green_taxi_data_2019
  WHERE "PULocationID" = (
    SELECT
      "LocationID"
    FROM
      zones
    WHERE "Zone" = 'East Harlem North'
  )
)
```

</details>

*Solution using CTEs*

``` sql
WITH 
--all trips with PU at East Harlem North
east_harlem_north AS (
    SELECT
      tip_amount,
      "DOLocationID"
    FROM
      green_taxi_data_2019
    WHERE "PULocationID" = (
      SELECT
        "LocationID"
      FROM
        zones
      WHERE "Zone" = 'East Harlem North'
    )
),
--max tip amount within these trips
max_tip AS (
  SELECT
    MAX(tip_amount) as max_tip
  FROM east_harlem_north
)

SELECT
  z."Zone"
FROM
  east_harlem_north e
JOIN
  zones z
ON
--get name of dropoff location
  e."DOLocationID" = z."LocationID"
WHERE
  e.tip_amount = (SELECT max_tip from max_tip)
```

| Zone        |
|:------------|
| JFK Airport |

- [ ] Yorkville West
- [x] JFK Airport
- [ ] East Harlem North
- [ ] East Harlem South

## Question 7. Terraform Workflow

Which of the following sequences, **respectively**, describes the
workflow for:

1.  Downloading the provider plugins and setting up backend,
2.  Generating proposed changes and auto-executing the plan
3.  Remove all resources managed by terraform\`

Answers:

- [ ] terraform import, terraform apply -y, terraform destroy
- [ ] teraform init, terraform plan -auto-apply, terraform rm
- [ ] terraform init, terraform run -auto-approve, terraform destroy
- [x] terraform init, terraform apply -auto-approve, terraform destroy
- [ ] terraform import, terraform apply -y, terraform rm
