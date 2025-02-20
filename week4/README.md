# Week 4 - Analytics engineering
Heiner Atze

# Introduction to analytics engineering

- role between Data engineering and Data analysts

## Differences ETL vs. ELT

**ETL**

- more stable and compliant as data is taken from data warehouse for
  analysis without transformation
- hight costs in terms of storage and computing

**ELT**

- Faster and more flexibil due to integrated transform step
- lower costs

## (Kimball’s) Dimensional modeling

**Objective**

- Data understandable to business users
- Fast query performance

**Approach**

- Prioritize objective (and thus accepting redundant data) over
  normalization
- other approaches: Bill Inmon, Data vault

## Star Schema

- two types of tables: Facts vs. Dimensions

### Facts tables

- Measurements
- metrics
- facts

The contents of a fact table correspond to business process (“verbs”)

#### Dimension tables

Corresponding to entities and provide context to the business processd
in the associated fact table. (“nouns”)

### Dimensional model architecture

**Stage area**

- raw data
- not exposed to everyone, only knowledgeable users

**Processing area**

- raw data transformed to data models
- focused on efficiency and standards

**Presentation area**

- final presentation of the data
- exposed to final user, stakeholder

# dbt

`dbt` is a transformation workflow that allows analytics code to be
deployed following best practices from software engineering.

Layered development process

1.  Development
2.  Test and documentations
3.  Deployment (Version control, CI/CD)

## How does `dbt` work ?

Model specification is stored in a `*.sql` file containing a `SELECT`
statement without DDL nor DML

## How to use `dbt` ?

**`dbt` Core** *vs.* **`dbt` Cloud**

# Starting a `dbt` project

`dbt init` with profiles ….

# Building first `dbt` models

- Modular data modeling
- `.sql` scripts (“`dbt` models”) for data transformation

## Anatomy of dbt model

Example `my_model.sql`

Use templating to provide DDL and DML hints to `dbt`

``` sql
{{
  config(materialzed='table') --or view, incremental, ephemeral
}}

SELECT *
FROM staging.source_table
WHERE record_state = 'ACTIVE'
```

will be compiled to

``` sql
CREATE TABLE my_schema.my_model as ( -- my_model comes from the .sql filename
  SELECT *
  FROM staging.source_table
  WHERE record_state = 'ACTIVE'
)
```

- four types of materializations
  - *EPHEMERAL* : does not finally materialize, comparable to a CTE
  - *VIEW* : virtual table, on each run altered
  - *TABLE* : physical representation, on each dbt run dropped and
    recreated
  - *INCREMENTAL* : related to table, inserts only new data into the
    table

### The `FROM` clause of a `dbt` model

**Sources**

- defined in yaml files
- can be referenced in the model files using the
  `{ source('source_name', 'source_table') }` macro
- freshness can be checked

**Seeds**

- csv files in `seed` folder of repository
- equivalent to `COPY INTO` command

**Ref**

- macro to reference any underlying table or view in the data warehouse
  as defined in a `.yml` files or another `dbt` model

### Model staging area

- setup `VSCode` with `dbt` PowerUser extension
- see `models/staging/schema.yml`

# Macros

- uses `jinja` templating engine
- comments `{# ...mutltiline... #}`
- allows to operate on the results of one query to generate another
  query
- Abstraction used to create reusable code in `SQL` (roughly equivalent
  to functions in other programming languages)

Example:

1.  Macro definition

``` sql
{#
  This macro returns the description of the payment_type
#}

{% macro get_payment_type_description(payment_type) -%}

case {{ payment_type }}
  when 1 then 'Credit card'
  when 1 then 'Cash'
  --....

{%- endmacro %}
```

2.  Create `dbt` model file

``` sql
SELECT
  {{ get_payment_type_description('payment_type') }} as get_payment_type_description,
  congestion_surcharge::doube precision
FROM {{ source('staging', 'green_tripdata_2021_01') }}
WHERE vendor_id IS NOT NULL
```

3.  Compilation

use `dbt compile` from command line, in `target/compiled/...` folder

``` sql
SELECT
  case safe_cast(payment_type as INT64)  
        when 1 then 'Credit card'
        when 2 then 'Cash'
        when 3 then 'No charge'
        when 4 then 'Dispute'
        when 5 then 'Unknown'
        when 6 then 'Voided trip'
        else 'EMPTY'
  end as payment_type_desc,
FROM source -- source is constructed using CTE 
```

# Packages

- libraries as in other programming languages
- Standalone `dbt` projects, containing *e.g.* models, macros …
- defined in `packages.yml` in project source directory
- import using `dbt deps`
- check the `dbt package hub`

## `dbt utils`

1.  Definition in `packages.yml`

``` yml
packages:
  - package: dbt-labs/dbt_utils
    version: 1.3.0
```

2.  Run `dbt deps`

3.  Usage

``` sql
--...
{{ dbt_utils.generate_surrogate_key(
          [
            adapter.quote("VendorID"),
            adapter.quote("lpep_pickup_datetime")
          ]
        ) }} as tripid,
--...
```

# Variables

- Variables can be defined in the `project.yml`

  ``` yml
  vars:
    payment_type_values: [1, 2, 3, 4, 5, 6]
  ```

- or on the command line in combination with a model definition

  ``` bash
  dbt build --select <model_name> --vars '{'is_test_run': 'false'}'
  ```

  and

      -- dbt build --select <model_name> --vars '{'is_test_run': 'false'}'
      {% if var('is_test_run', default=true) %}

        limit 100

      {% endif %}

## Using `seeds` for the `taxi_zone_lookup` table

- copy the .csv file to the `seeds` folder
- `dbt build` will materialize a table in the data warehoue

**Some cleaning using and creation of a dimensions table for the zones**

- see [dim_zones.sql](./dbt/taxi_rides_ny/models/core/dim_zones.sql)

# Creating the facts table for the taxi trips

- see [fact_trips.sql](./dbt/taxi_rides_ny/models/core/facts_trips.sql)

> [!IMPORTANT]
>
> The `dev_limit` as described in the lecture DOES NOT limit the amount
> of data processed during the query/model build BUT only the size of
> the final table!
