# Week 5 - Batch processing
Heiner Atze

# Batch Processing *vs.* Streaming

Batch processing refers to the execution of a series of jobs on a set of
data over a period, making it ideal for handling large datasets that are
collected over time. This approach is typically used when immediate data
processing is not required, such as generating reports or data analysis
tasks. On the other hand, streaming processing involves real-time data
handling, where data is processed continuously as it arrives. This is
particularly useful for applications that require immediate insights,
such as monitoring social media feeds or transactions in financial
systems. While batch processing offers efficiency for large datasets,
streaming allows for responsiveness and timely decision-making.

80-90% of data processing jobs are batch

Batch processing jobs are usually launched daily or weekly. Some often
used technologies include:

- Python scripts (run using orchestrator)
- SQL
- Spark
- Flink

``` mermaid
---
title: Typical Batch processing Workflow
---
flowchart LR
dl["Data Lake"] --> python1["Python"]
python1 --> db["SQL \n (dbt)"]
db --> sp["Spark"] --> python2["Python"] 
```

## Advantages of Batch jobs

Batch jobs make it easy to: - manage the workflow - trigger retries -
scale the workflow

## Disadvantages

- *delay*
- workflow runtime

# Introduction to Spark

## What is spark?

- Data processing engine

``` mermaid
graph LR
    A[("Data lake \n (S3/GCS)")] --> B[CLUSTER]
    B --> C[("Data lake \n (S3/GCS)")]
    
    subgraph B[SPARK CLUSTER]
        E[Worker 1] 
        F[Worker 2]
        G[Worker i]
        M[Worker n]
    end

    A --> D["Hive \n Presto/Athena \n\n if batch job can be \n done in SQL"]
    D --> C
```

- multilanguage
  - Python
  - Java & Scala
  - R
- can be used for batch AND stream processing

## When to use Spark ?

- everything that is beyond SQL

### ML training pipeline

``` mermaid
graph LR
    RAW[RAW DATA] --> LAKE[(LAKE)]
    LAKE --> SQL[SQL \n ATHENA]
    SQL --> SPARK[SPARK]
    SPARK --> PYTHON[PYTHON \n TRAIN ML]
    PYTHON --> MODEL
    SPARK --> a[SPARK \n APPLY ML]
    MODEL --> a
    a --> LAKE
```

# First look at SPARK

## Environment setup and spark / pySpark installation

``` bash
uv pip install pyspark
uv pip install install-jdk
```

Then using the .venv python interpreter:

``` python
import jdk
jdk.install("11")
```

Spark hello world (https://sparkmadeeasy.com/hello_world):

``` python
from pyspark.sql import SparkSession

# 1) Create a spark context
spark = SparkSession.builder.getOrCreate()

# 2) You can use `sql()` to write raw sql queries
df = spark.sql("SELECT 'Hello World' as column_1")

# 3) You can use `show()` to print your dataframe
df.show()

#  +-----------+
#  |   column_1|
#  +-----------+
#  |Hello World|
#  +-----------+
```

## Load data, create partitioned dataframe

### Initialize Spark from Jupyter

``` python
import pyspark
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .master("local[*]") \
    .appName("test") \
    .getOrCreate()
```

### Read a csv file

``` python
df = spark.read \
    .option("header", "true") \
    .csv("fhvhv_tripdata_2021-01.csv.gz")
    # .option("InferSchema", True) # slow, but infers datatypes
```

### Schema hack

Extract some 100 lines from the csv and infer the schema using `pandas`.

``` bash
gzip -d fhvhv_tripdata_2021-01.csv.gz
head -n 100 fhvhv_tripdata_2021-01.csv > fhvhv_tripdata_2021-01_head.csv
gzip fhvhv_tripdata_2021-01.csv.gz
```

``` python
import pandas as pd

df_pandas = pd.read_csv(
    'fhvhv_tripdata_2021-01_head.csv',
    parse_dates=['pickup_datetime', 'dropoff_datetime']
)

# print out the schema
spark.createDataFrame(df_pandas).schema
```

*Dataframe schema*

``` python
from pyspark.sql.types import *

schema = StructType([
    StructField('hvfhs_license_num', StringType(), True), 
    StructField('dispatching_base_num', StringType(), True), 
    StructField('pickup_datetime', TimestampType(), True), 
    StructField('dropoff_datetime', TimestampType(), True), 
    StructField('PULocationID', IntegerTyper(), True), 
    StructField('DOLocationID', IntegerType(), True), 
    StructField('SR_Flag', StingType(), True)]
)
```

### Reload dataframe with correct schema

``` python
df = spark.read \
    .option("header", "true") \
    .schema(schema) \
    .csv("fhvhv_tripdata_2021-01.csv.gz")
```

### Save partitioned dataframe

``` python
df = df.repartition(24) # lazy evaluation
df.write.parquet("fhvhv/2021/01/")
```

# Spark dataframes

## Actions *vs.* Transformations

### Transformations are lazy

- SELECT (projection)
- WHERE (selection)
- JOINS
- GROUP BY

### Actions are eager

- `.show()`
- `.take()`
- `.head()`
- `.write.`

## Why bother when there is `SQL` ?

### Import into data lake (GCS bucket) using kestra flow backfills

### Convert to partitioned parquet files using Spark

#### GCS config for Spark

``` python
spark = SparkSession.builder \
    .appName('pyspark-run-with-gcp-bucket2') \
    .config("spark.jars", "/home/kantundpeterpan/projects/zoomcamp/zcde_space/week5/gcs-connector-hadoop3-latest.jar") \
    .config("spark.sql.repl.eagerEval.enabled", True) \
    .getOrCreate()

# Configure GCS authentication
spark.conf.set("google.cloud.auth.service.account.enable", "true")
spark._jsc.hadoopConfiguration().set("google.cloud.auth.service.account.json.keyfile", 
                                     "/home/kantundpeterpan/projects/zoomcamp/zcde_space/week1/3_intro_terraform/workspaceaddon-436615-4bcf737409b7.json")
spark._jsc.hadoopConfiguration().set('fs.gs.impl', 'com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem')
```

#### Infer table schemas

``` python
yellow/green_schema = spark.read \
    .option("header", True) \
    .option("inferSchema", True) \
    .csv("gs://workspaceaddon-436615/yellow_tripdata_2021-01.csv.gz").schema
```

#### Run the conversion

``` python
year = 2020
taxi = 'yellow'

schemas = {
    'yellow':yellow_schema,
    'green':green_schema
    }

for m in range(1,13):
    df = spark.read \
        .option("header", True) \
        .schema(schemas[taxi]) \
        .csv(f"gs://workspaceaddon-436615/{taxi}_tripdata_{year}-{m:02d}.csv")
    
    output_path = f"gs://workspaceaddon-436615/{taxi}/{year}/{m:02d}"
    print(output_path)
    
    df.repartition(4) \
        .write.parquet(output_path)
```

# Spark internals

## Spark Cluster

- master and executer ndoes
- data usually stored on cloud storage (AWS, GCP)

## GroupBy in Spark

### Stage 1 - Partial GroupBy

- Partitions are distributed over executors
- Each executor performs the operations on its assigned partition
- result is only partial

### Stage 2 - Reshuffling

- Result records are redistributed among executors
- Same key $\Rightarrow$ same executor (External merge sort)
- Group by operation on reshuffled data

## Joins in Spark

…

### Join disparately sized tables

- the smaller table is completely copied over to each executor

# Spark in the Cloud

## Connect to GCS

done

## Setup a local Spark cluster

- Master setup

Either run `sbin/start-master.sh` in the `SPARK_HOME` directory or
manually start master node

``` bash
spark-class org.apache.spark.deploy.master.Master \
    -h 127.0.0.1 \
    --webui-port 8083
```

and worker(s):

``` bash
spark-class org.apache.spark.deploy.worker.Worker spark://127.0.0.1:7077
```

## Convert notebook to script

## Turn script in to CLI

## use spark-submit

``` bash
SPARK_MASTER=spark://127.0.0.1:7077
GCS_JAR= ...

spark-submit \
    --master "${SPARK_MASTER}" \
    --conf "spark.driver.extraClassPath=$GCS_JAR" \
    6_spark_sql.py \
    --input_green 2021/* \
    --input_yellow 2021/* \
    --output /data/report/2021
```

# Homework

## Imports and Spark spin up

``` python
import pyspark
from pyspark.sql import SparkSession
```

``` python
import os

from pathlib import Path
```

``` python
os.chdir(Path("projects/zoomcamp/zcde_space/week5").resolve())
```

``` python
pwd = Path(os.getcwd())
```

``` python
spark = SparkSession.builder \
    .master("local[*]") \
    .getOrCreate()
```

    25/03/10 11:29:25 WARN Utils: Your hostname, mystuff resolves to a loopback address: 127.0.1.1; using 193.168.147.155 instead (on interface eth0)
    25/03/10 11:29:25 WARN Utils: Set SPARK_LOCAL_IP if you need to bind to another address
    Setting default log level to "WARN".
    To adjust logging level use sc.setLogLevel(newLevel). For SparkR, use setLogLevel(newLevel).
    25/03/10 11:29:26 WARN NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable

``` python
df = spark.read.parquet(
    str(pwd / "yellow_tripdata_2024-10.parquet")
    )
```

## Question 2

``` python
# df.repartition(4).write.parquet(str( pwd / "homework"))
```

``` python
!ls -lh ./homework/
```

    total 90M
    -rw-r--r-- 1 kantundpeterpan kantundpeterpan   0 Mar 10 11:18 _SUCCESS
    -rw-r--r-- 1 kantundpeterpan kantundpeterpan 23M Mar 10 11:18 part-00000-4bc1ca0e-8325-44f7-b773-bf81ac796b74-c000.snappy.parquet
    -rw-r--r-- 1 kantundpeterpan kantundpeterpan 23M Mar 10 11:18 part-00001-4bc1ca0e-8325-44f7-b773-bf81ac796b74-c000.snappy.parquet
    -rw-r--r-- 1 kantundpeterpan kantundpeterpan 23M Mar 10 11:18 part-00002-4bc1ca0e-8325-44f7-b773-bf81ac796b74-c000.snappy.parquet
    -rw-r--r-- 1 kantundpeterpan kantundpeterpan 23M Mar 10 11:18 part-00003-4bc1ca0e-8325-44f7-b773-bf81ac796b74-c000.snappy.parquet

## Question 3

``` python
from pyspark.sql import functions as F
```

``` python
df.registerTempTable("oct24")
```

    /home/kantundpeterpan/projects/zoomcamp/zcde_space/week5/.venv/lib/python3.11/site-packages/pyspark/sql/dataframe.py:329: FutureWarning: Deprecated in 2.0, use createOrReplaceTempView instead.
      warnings.warn("Deprecated in 2.0, use createOrReplaceTempView instead.", FutureWarning)

``` python
df \
    .filter(
        F.to_date(df.tpep_pickup_datetime) == '2024-10-15') \
    .count()
```

    128893

## Question 4

``` python
max_dur = spark.sql("""
   SELECT
     MAX(
     EXTRACT(
        DAY FROM
         tpep_dropoff_datetime - tpep_pickup_datetime
      ) * 24 + EXTRACT(
        HOUR FROM
         tpep_dropoff_datetime - tpep_pickup_datetime
      )) as max_duration_h
   FROM oct24       
""")
```

``` python
max_dur.show()
```

    +--------------+
    |max_duration_h|
    +--------------+
    |           162|
    +--------------+

## Question 6

``` python
zones = spark.read \
    .option("header", 'true') \
    .option("inferSchema", 'true') \
    .csv(str(pwd / "taxi_zone_lookup.csv"))
```

``` python
zones.printSchema()
```

    root
     |-- LocationID: integer (nullable = true)
     |-- Borough: string (nullable = true)
     |-- Zone: string (nullable = true)
     |-- service_zone: string (nullable = true)

``` python
zones.createOrReplaceTempView("zones")
```

``` python
df.join(zones.withColumnRenamed("LocationID", "PULocationID"),
        on = "PULocationID") \
    .select("Zone") \
    .groupby("Zone") \
    .count() \
    .sort(F.asc('count')) \
    .limit(1).show()
```

    [Stage 10:=============================>                            (4 + 4) / 8]

    +--------------------+-----+
    |                Zone|count|
    +--------------------+-----+
    |Governor's Island...|    1|
    +--------------------+-----+

``` python
spark.stop()
```
