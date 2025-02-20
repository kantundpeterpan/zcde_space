# Week 2 - Workflow orchestration
Heiner Atze

# Introduction to Workflow orchestration in kestra - Taxi data to Postgres

This is a breakdown of the contents of the
[`02_postgres_taxi.yaml`](https://github.com/DataTalksClub/data-engineering-zoomcamp/blob/main/02-workflow-orchestration/flows/02_postgres_taxi_scheduled.yaml)
flow.

## Input parameters

``` yaml
inputs:
  - id: taxi
      type: SELECT
      displayName: Select taxi type
      values: [yellow, green]
      defaults: yellow
```

Possible values for the `type` of the input parameters are : `STRING`,
`INT`, `FLOAT`, `BOOLEAN`, `DATETIME`, `DATE`, `TIME`, `DURATION`,
`SELECT`, `MULTISELECT`, `ARRAY`, `JSON`, `YAML`, `FILE`, `URI`,
`SECRET`.

## Variable definition based on input parameters

``` yaml
variables:
  file: "{{inputs.taxi}}_tripdata_{{inputs.year}}-{{inputs.month}}.csv"
  staging_table: "public.{{inputs.taxi}}_tripdata_staging"
  table: "public.{{inputs.taxi}}_tripdata"
  data: "{{outputs.extract.outputFiles[inputs.taxi ~ '_tripdata_' ~ inputs.year ~ '-' ~ inputs.month ~ '.csv']}}"
```

`inputs` can be used in string literals by wrappping them in `{{}}`. The
`~` operator concatenates strings.

A detailed look at the `data` field:

``` yaml
data: "{{'direct.outputFiles[inputs.taxi ~ '_tripdata_' ~ inputs.year ~ '-' ~ inputs.month ~ '.csv']'}}"
```

**Path Construction Elements**

- `direct.outputFiles` references the output files from a direct storage
  location
- Square bracket notation `[]` is used to access a specific file
- The expression inside the brackets builds the filename dynamically

**String Concatenation**

- The tilde operator `~` joins multiple string components:
  - `inputs.taxi` (taxi type)
  - `'_tripdata_'` (static text)
  - `inputs.year` (year value)
  - `'-'` (hyphen separator)
  - `inputs.month` (month value)
  - `'.csv'` (file extension)

This field constructs a path to access a specific CSV file in Kestra’s
storage system, combining input variables and static text to form the
complete filename. The resulting path can then be used to reference the
file in subsequent tasks or operations.

## Tasks

### Set task label

``` yaml
tasks:
  tasks:
  - id: set_label
    type: io.kestra.plugin.core.execution.Labels
    labels:
      file: "{{render(vars.file)}}"
      taxi: "{{inputs.taxi}}"
```

So far so good. An interesting point here is the `render(vars.file)` The
`render()` function is crucial here because:

- It ensures that any expressions inside the `vars.file` variable are
  properly evaluated at runtime
- Without the `render()` function, any expressions inside the variable
  would be treated as plain text rather than being evaluated
- This is particularly important when the variable contains dynamic
  content or expressions that need to be processed

For example, if `vars.file` contains an expression like `"{{now()}}"`,
using `render()` ensures the current timestamp is inserted rather than
the literal string “{{now()}}”.

### download the `.csv.gz` and unzip

``` yaml
  - id: extract
    type: io.kestra.plugin.scripts.shell.Commands
    outputFiles:
      - "*.csv"
    taskRunner:
      type: io.kestra.plugin.core.runner.Process
    commands:
      - wget -qO- https://github.com/DataTalksClub/nyc-tlc-data/releases/download/{{inputs.taxi}}/{{render(vars.file)}}.gz | gunzip > {{render(vars.file)}}
```

### Push the data from `.csv` to `SQL`

In order for this to work, credentials for the SQL database need to be
defined

``` yaml
pluginDefaults:
  - type: io.kestra.plugin.jdbc.postgresql
    values:
      url: jdbc:postgresql://postgres:5432/postgres-zoomcamp
      username: kestra
      password: k3str4
```

#### pgadmin setup for some interactivity

Here `postgres` can be used as the hostname if `kestra` was started
using the `docker-compose.yaml` file. I also attached `pgadmin4` by
modifying the `docker-compose` file from week 1.

``` yaml
services:
  pgadmin:
    image: dpage/pgadmin4
    environment:
      - PGADMIN_DEFAULT_EMAIL=user@domain.com
      - PGADMIN_DEFAULT_PASSWORD=catsarecool
    ports:
      - "127.0.0.1:8083:80"
    volumes:
      - pgadmin_data:/var/lib/pgadmin
    networks:
      # attach to kestra network
      - 02-workflow-orchestration_default

volumes:
  pgadmin_data:
    driver: local

networks:
  02-workflow-orchestration_default:
    external: true
```

#### Create the final table

This table has two additional columns: `unique_row_id` and `filename`.
For now it is empty.

``` yaml
- id: green_create_table
        type: io.kestra.plugin.jdbc.postgresql.Queries
        sql: |
          CREATE TABLE IF NOT EXISTS {{render(vars.table)}} (
              unique_row_id          text,
              filename               text,
              VendorID               text,
              lpep_pickup_datetime   timestamp,
              lpep_dropoff_datetime  timestamp,
              store_and_fwd_flag     text,
              RatecodeID             text,
              PULocationID           text,
              DOLocationID           text,
              passenger_count        integer,
              trip_distance          double precision,
              fare_amount            double precision,
              extra                  double precision,
              mta_tax                double precision,
              tip_amount             double precision,
              tolls_amount           double precision,
              ehail_fee              double precision,
              improvement_surcharge  double precision,
              total_amount           double precision,
              payment_type           integer,
              trip_type              integer,
              congestion_surcharge   double precision
          );
```

#### Create a staging table

This will be a table that is used to copy in the data from the `.csv`
file, add `unique_row_id` and `filename` and then merge it to the final
table.

``` yaml
- id: green_create_staging_table
        type: io.kestra.plugin.jdbc.postgresql.Queries
        sql: |
          CREATE TABLE IF NOT EXISTS {{render(vars.staging_table)}} (
              unique_row_id          text,
              filename               text,
              VendorID               text,
              ...
              ...
              ...            
              trip_type              integer,
              congestion_surcharge   double precision
          );
```

*truncation*

``` yaml
- id: green_truncate_staging_table
        type: io.kestra.plugin.jdbc.postgresql.Queries
        sql: |
          TRUNCATE TABLE {{render(vars.staging_table)}};
```

*copy data from csv*

``` yaml
- id: green_copy_in_to_staging_table
        type: io.kestra.plugin.jdbc.postgresql.CopyIn
        format: CSV
        from: "{{render(vars.data)}}"
        table: "{{render(vars.staging_table)}}"
        header: true
        columns: [VendorID,lpep_pickup_datetime,lpep_dropoff_datetime,store_and_fwd_flag,RatecodeID,PULocationID,DOLocationID,passenger_count,trip_distance,fare_amount,extra,mta_tax,tip_amount,tolls_amount,ehail_fee,improvement_surcharge,total_amount,payment_type,trip_type,congestion_surcharge]
```

*add new columns*

``` yaml
- id: green_add_unique_id_and_filename
        type: io.kestra.plugin.jdbc.postgresql.Queries
        sql: |
          UPDATE {{render(vars.staging_table)}}
          SET 
            unique_row_id = md5(
              COALESCE(CAST(VendorID AS text), '') ||
              COALESCE(CAST(lpep_pickup_datetime AS text), '') || 
              COALESCE(CAST(lpep_dropoff_datetime AS text), '') || 
              COALESCE(PULocationID, '') || 
              COALESCE(DOLocationID, '') || 
              COALESCE(CAST(fare_amount AS text), '') || 
              COALESCE(CAST(trip_distance AS text), '')      
            ),
            filename = '{{render(vars.file)}}';
```

*merge data from staging table to final table*

``` yaml
- id: green_merge_data
        type: io.kestra.plugin.jdbc.postgresql.Queries
        sql: |
          MERGE INTO {{render(vars.table)}} AS T
          USING {{render(vars.staging_table)}} AS S
          ON T.unique_row_id = S.unique_row_id
          WHEN NOT MATCHED THEN
            INSERT (
              unique_row_id, filename, VendorID, lpep_pickup_datetime, lpep_dropoff_datetime,
              store_and_fwd_flag, RatecodeID, PULocationID, DOLocationID, passenger_count,
              trip_distance, fare_amount, extra, mta_tax, tip_amount, tolls_amount, ehail_fee,
              improvement_surcharge, total_amount, payment_type, trip_type, congestion_surcharge
            )
            VALUES (
              S.unique_row_id, S.filename, S.VendorID, S.lpep_pickup_datetime, S.lpep_dropoff_datetime,
              S.store_and_fwd_flag, S.RatecodeID, S.PULocationID, S.DOLocationID, S.passenger_count,
              S.trip_distance, S.fare_amount, S.extra, S.mta_tax, S.tip_amount, S.tolls_amount, S.ehail_fee,
              S.improvement_surcharge, S.total_amount, S.payment_type, S.trip_type, S.congestion_surcharge
            );
```

### Remove `.csv` file

``` yaml
- id: purge_files
    type: io.kestra.plugin.core.storage.PurgeCurrentExecutionFiles
    description: This will remove output files. If you'd like to explore Kestra outputs, disable it.
```

### Add conditional logic for green vs. yellow taxis

``` yaml
tasks:
  ...
  - id: if_green_taxi
  type: io.kestra.plugin.core.flow.If
  condition: "{{inputs.taxi == 'green'}}"
  then:
    - id: green_create_table
    ...
    ...
```

# Scheduled flows and backfills

## Trigger definition

``` yaml
triggers:
  - id: green_schedule
    type: io.kestra.plugin.core.trigger.Schedule
    cron: "0 9 1 * *"
    inputs:
      taxi: green
```

see [crontab expression generator](https://crontab.guru/#0_9_1_*_*)

# Orchestra dbt models with Postgres

see also week 4

# ETL pipeline on Google Cloud

## Variable setup using key-value store of a namespace

Setup a google service account and store the credentials and details
using the key-value store of the respective namespace either directly or
set the key,value-pairs in a separate flow.

``` yaml
id: 04_gcp_kv
namespace: zoomcamp

tasks:
  - id: gcp_creds
    type: io.kestra.plugin.core.kv.Set
    key: GCP_CREDS
    kvType: JSON
    value: |
      {
        "type": "service_account",
        "project_id": "...",
      }
...
...
```

## Use the key-value store to for GCP setup

In a separate flow, resources can be launched using the credentials and
information from the key-value store.

``` yaml
tasks:
  - id: create_gcs_bucket
    type: io.kestra.plugin.gcp.gcs.CreateBucket
    ifExists: SKIP
    storageClass: REGIONAL
    name: "{{kv('GCP_BUCKET_NAME')}}" # make sure it's globally unique!
...
```

## Load the taxi data to the bucket and import to BigQuery

This is very similar to the flow using Postgres.

### Upload a file to GCS, move data to BigQuery

``` yaml
id: 06_gcp_taxi
namespace: zoomcamp
description: |
  The CSV Data used in the course: https://github.com/DataTalksClub/nyc-tlc-data/releases

inputs:

... # same as before

variables:
  file: "{{inputs.taxi}}_tripdata_{{inputs.year}}-{{inputs.month}}.csv"
  # target file in the GCP bucket
  gcs_file: "gs://{{kv('GCP_BUCKET_NAME')}}/{{vars.file}}"
  # table name for BigQuery
  table: "{{kv('GCP_DATASET')}}.{{inputs.taxi}}_tripdata_{{inputs.year}}_{{inputs.month}}"
  data: "{{outputs.extract.outputFiles[inputs.taxi ~ '_tripdata_' ~ inputs.year ~ '-' ~ inputs.month ~ '.csv']}}"

tasks:
  - id: set_label

    ...

  - id: extract
    
    ...

  - id: upload_to_gcs
    type: io.kestra.plugin.gcp.gcs.Upload
    from: "{{render(vars.data)}}"
    to: "{{render(vars.gcs_file)}}"
```

The following steps are:

1.  create a main table
2.  load the `.csv` from the bucket to an external table in the BigQuery
    dataset
3.  copy the data in the external table into a new table and add the
    `unique_id` and `filename` columns
4.  merge the temporary table to the main table

# Use `dbt` with BigQuery

see also week 4, this flow executes what will be worked in there in dbt

# Deploy workflows using Git

Resources

- [Install Kestra on Google
  Cloud](https://go.kestra.io/de-zoomcamp/gcp-install)
- [Moving from Development to
  Production](https://go.kestra.io/de-zoomcamp/dev-to-prod)
- [Using Git in Kestra](https://go.kestra.io/de-zoomcamp/git)
- [Deploy Flows with GitHub
  Actions](https://go.kestra.io/de-zoomcamp/deploy-github-actions)

# Homework

``` r
library(DBI)

# Get the key path from environment variable
key_path <- Sys.getenv("BIGQUERY_KEY_PATH")

# Authenticate using the JSON key file
bigrquery::bq_auth(path = key_path)

con <- dbConnect(
    bigrquery::bigquery(),
    project = "workspaceaddon-436615",
    dataset = "zoomcamp",
    billing = "workspaceaddon-436615"
)
```

## Question 1

Within the execution for `Yellow` Taxi data for the year `2020` and
month `12`: what is the uncompressed file size (i.e. the output file
`yellow_tripdata_2020-12.csv` of the `extract` task)?

- [x] 128.3 MB
- [ ] 134.5 MB
- [ ] 364.7 MB
- [ ] 692.6 MB

## Question 2

What is the rendered value of the variable `file` when the inputs `taxi`
is set to `green`, `year` is set to `2020`, and `month` is set to `04`
during execution?

- [ ] `{inputs.taxi}_tripdata_{{inputs.year}}-{{inputs.month}}.csv`
- [x] `green_tripdata_2020-04.csv`
- [ ] `green_tripdata_04_2020.csv`
- [ ] `green_tripdata_2020.csv`

## Question 3

How many rows are there for the `Yellow` Taxi data for all CSV files in
the year 2020?

- [ ] 13,537.299
- [x] 24,648,499
- [ ] 18,324,219
- [ ] 29,430,127

*Solution*

``` sql
SELECT 
  COUNT(*) as no_rows_yellow2020
FROM `workspaceaddon-436615.zoomcamp.yellow_tripdata`
WHERE filename LIKE '%_2020-%.csv'
```

| no_rows_yellow2020 |
|-------------------:|
|           24648499 |

## Question 4

How many rows are there for the `Green` Taxi data for all CSV files in
the year 2020?

- [ ] 5,327,301
- [ ] 936,199
- [x] 1,734,051
- [ ] 1,342,034

*Solution*

``` sql
SELECT 
  COUNT(*) as no_rows_green2020
FROM `workspaceaddon-436615.zoomcamp.green_tripdata`
WHERE filename LIKE '%_2020-%.csv'
```

| no_rows_green2020 |
|------------------:|
|           1734051 |

## Question 5

How many rows are there for the `Yellow` Taxi data for the March 2021
CSV file?

- [ ] 1,428,092
- [ ] 706,911
- [x] 1,925,152
- [ ] 2,561,031

*Solution*

``` sql
SELECT 
  COUNT(*) as no_rows_yellow2020_03
FROM `workspaceaddon-436615.zoomcamp.yellow_tripdata`
WHERE filename LIKE '%_2021-03.csv'
```

| no_rows_yellow2020_03 |
|----------------------:|
|               1925152 |

## Question 6

How would you configure the timezone to New York in a Schedule trigger?

- [ ] Add a `timezone` property set to `EST` in the `Schedule` trigger
  configuration  
- [x] Add a `timezone` property set to `America/New_York` in the
  `Schedule` trigger configuration
- [ ] Add a `timezone` property set to `UTC-5` in the `Schedule` trigger
  configuration
- [ ] Add a `location` property set to `New_York` in the `Schedule`
  trigger configuration
