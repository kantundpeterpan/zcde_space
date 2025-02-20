# Week 3 - Data warehouses, BigQuery
Heiner Atze

# Data warehousing

## OLTP /vs./ OLAP

OLTP: Online transaction processing OLAP: Online analytical processing

Data warehouses are OLAP solution used for reporting and data analysis

General contents:

- Meta data
- Summary data
- Raw data

Data marts are data collections concerning certain topics or departments
and provide clean data for analysis.

# BigQuery

- serverless data warehouse
- combined software and infrastructure
- included features:
  - machine learning
  - geospatial
  - BI
- Separates compute engine and data storage

## Create external tables from google cloud storage

``` sql
CREATE OR REPLACE EXTERNAL TABLE `workspaceaddon-436615.zoomcamp.green_tripdata2020_ext`
OPTIONS(
  format = 'CSV',
  uris = ['gs://workspaceaddon-436615/green_tripdata_2020-*.csv']
)
```

## Partitioning in BigQuery

- if one or more columns are expected to be used often for filtering,
  partitioning the table might be an advantage
- reduces cost, as less data need to be processed

``` sql
-- create a non partitioned table within bigquery from external table
CREATE OR REPLACE TABLE `workspaceaddon-436615.zoomcamp.green_tripdata2020` AS
SELECT * FROM `workspaceaddon-436615.zoomcamp.green_tripdata2020_ext`
```

``` sql
-- create a partitioned table within bigquery from external table
CREATE OR REPLACE TABLE `workspaceaddon-436615.zoomcamp.green_tripdata2020_part`
PARTITION by
  DATE(lpep_pickup_datetime) AS
SELECT * FROM `workspaceaddon-436615.zoomcamp.green_tripdata2020_ext`
```

*What is the impact?*

``` sql
-- processes 23 MB of data
SELECT DISTINCT(VendorID)
FROM `workspaceaddon-436615.zoomcamp.green_tripdata2020`
WHERE DATE(lpep_pickup_datetime) BETWEEN '2020-06-01' AND '2020-06-30';
```

``` sql
-- processes < 1 MB of Data
SELECT DISTINCT(VendorID)
FROM `workspaceaddon-436615.zoomcamp.green_tripdata2020_part`
WHERE DATE(lpep_pickup_datetime) BETWEEN '2020-06-01' AND '2020-06-30';
```

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

``` sql
-- Let's look into the partitons
SELECT table_name, partition_id, total_rows
FROM `zoomcamp.INFORMATION_SCHEMA.PARTITIONS`
WHERE table_name = 'green_tripdata2020_part'
ORDER BY total_rows DESC
LIMIT 10;
```

| table_name              | partition_id | total_rows |
|:------------------------|:-------------|-----------:|
| green_tripdata2020_part | 20200109     |      18491 |
| green_tripdata2020_part | 20200110     |      18307 |
| green_tripdata2020_part | 20200108     |      17586 |
| green_tripdata2020_part | 20200107     |      17027 |
| green_tripdata2020_part | 20200214     |      16574 |
| green_tripdata2020_part | 20200106     |      16323 |
| green_tripdata2020_part | 20200228     |      16246 |
| green_tripdata2020_part | 20200103     |      16062 |
| green_tripdata2020_part | 20200227     |      16034 |
| green_tripdata2020_part | 20200117     |      16011 |

## Combine Clustering with Partitioning

``` sql
-- create a partitioned table within bigquery from external table
CREATE OR REPLACE TABLE `workspaceaddon-436615.zoomcamp.green_tripdata2020_clus`
PARTITION by
  DATE(lpep_pickup_datetime) 
CLUSTER BY VendorID AS
SELECT * FROM `workspaceaddon-436615.zoomcamp.green_tripdata2020_ext`
```

## Partioning *vs.* Clustering

$$
\begin{array}{|l|l|}
\hline \text { Clustering } & \text { Partitoning } \\
\hline \text { Cost benefit unknown } & \text { Cost known upfront } \\
\hline \begin{array}{l}
\text { You need more granularity than partitioning } \\
\text { alone allows }
\end{array} & \text { You need partition-level management. } \\
\hline \begin{array}{l}
\text { Your queries commonly use filters or } \\
\text { aggregation against multiple particular } \\
\text { columns }
\end{array} & \text { Filter or aggregate on single column } \\
\hline \begin{array}{l}
\text { The cardinality of the number of values in a } \\
\text { column or group of columns is large }
\end{array} & \\
\hline
\end{array}
$$

BigQuery partitioning divides large tables into smaller segments based
on specific criteria like dates or ranges, which improves query
performance and reduces costs by scanning less data. Clustering, on the
other hand, organizes data by sorting and grouping it based on the
contents of up to four specified columns, storing related data together
for more efficient retrieval. While partitioning requires selecting a
single column as the partitioning key, clustering can be applied on
multiple columns, and the order of clustered columns determines the sort
order of the data. Both features can be combined to achieve more
finely-grained sorting and further query optimization However,
clustering has limitations as it can only be specified during table
creation and cannot be modified later.

*When to prefer Clustering over partitioning?*

- too small partitions \< 1 GB
- too many partitions
- too frequent data updates across all partiions

## Automatic reclustering

Upon insertion of new data, Bigquery performs automatic reclustering.
This is performed in the background and for partitioned tables within
the scope of each partition.

# BigQuery best practices

## Cost reduction

The following best practices are specific to BigQuery:

- **Use Partitioned Tables**:

  BigQuery allows you to partition tables by date (or integer range),
  significantly reducing the amount of data scanned during queries.

- **Cluster Tables**:

  Clustering in BigQuery helps organize data within a table based on
  specified columns, improving query performance by reducing the data
  scanned.

- **Use Approximate Aggregation Functions**:

  BigQuery provides functions like `APPROX_COUNT_DISTINCT()` that give
  faster, approximate results with less processing time and lower costs.

- **Leverage Materialized Views**:

  BigQuery supports materialized views, which can store and maintain
  aggregated results, reducing the cost of repeated computations on
  large datasets.

- **Use Streaming Inserts Efficiently**:

  BigQuery charges differently for streaming data into tables compared
  to batch inserts, so recommendations around these methods are specific
  to BigQuery’s pricing model.

- **Materialize Query Results in Stages**:

  Save intermediate results in tables to avoid recomputation, simplify
  complex queries, reuse data across multiple queries, and enhance
  overall query performance in BigQuery.

# BigQuery best practices

## Query performance

Here’s a concise bullet point list for BigQuery best practices related
to query performance:

## Query performance

- **Use Standard SQL**: Leverage the latest SQL features and
  optimizations.
- **Select Only Necessary Columns**: Use `SELECT` statements to only
  retrieve the data you need.
- **Limit the Number of Rows**: Use `LIMIT` to reduce the dataset size
  if not all rows are required.
- **Partition Tables**: Use table partitioning to improve query times,
  especially for large datasets.
- **Cluster Tables**: Organize tables by specific columns to enhance
  performance on filtered queries.
- \*\* Avoid SELECT \* \*\*: Specify columns instead of using `SELECT *`
  to reduce data transfer and processing time.
- **Use WITH Clauses**: Break down complex queries into simpler
  components for better readability and execution.
- **Optimize JOINs**:
  - Use appropriate join types (INNER, LEFT, etc.).
  - Avoid joining large tables if possible.
- **Query Caching**: Take advantage of cached results for repeated
  queries to save time.
- **Materialized Views**: Use materialized views to precompute and store
  complex query results.
- **Use Temporary Tables**: Consider storing intermediate results in
  temporary tables to streamline complex analyses.
- **Monitor Query Performance**: Utilize BigQuery’s built-in monitoring
  tools to identify and troubleshoot slow queries.
- **Reduce Cross-Region Queries**: If possible, ensure datasets and
  queries operate within the same region to minimize latency and cost.

### Understanding `WITH` clauses (CTEs) and prepared statements

1.  **CTEs vs. Prepared Statements**:

    - **CTEs (`WITH` clauses)** are essentially a way to simplify your
      SQL queries by creating temporary result sets that can be
      referenced within a single query. They are used to make queries
      more readable and structured.

    - **Prepared Statements** are a feature often used in database
      programming that allows you to precompile SQL statements with
      placeholders for parameters. This can enhance performance and
      security (e.g., against SQL injection attacks) by separating query
      logic from data.

2.  **Execution Context**:

    - CTEs are executed as part of the query they are defined within and
      cannot be reused or executed independently. Each time you run a
      query containing a CTE, the CTE is recomputed.
    - Prepared statements are compiled and stored in memory, allowing
      for faster repeated execution with different parameters.

3.  **Performance Considerations**:

    - If you treat `WITH` clauses like prepared statements (i.e.,
      thinking they can be reused efficiently), you might be misled
      regarding their performance. CTEs can have overhead since they are
      re-evaluated for each execution of the main query, especially in
      queries where CTEs are referenced multiple times.

4.  **Code Structure**:

    - Treating CTEs like prepared statements may lead to complex queries
      that become harder to read or maintain. Instead, use CTEs for
      clarity in breaking down queries, but do not assume they will
      function with the same efficiency or behavior as prepared
      statements.

# Internals of Bigquery

## Hardware architecture

Google BigQuery is built on a unique architecture that separates query
computation from data storage, enabling high efficiency and scalability.
This architecture leverages:

- **Colossus Storage**: This is Google’s distributed file system
  designed for high-performance storage of large datasets. Colossus
  allows BigQuery to manage and store massive amounts of data across
  multiple locations, ensuring durability and availability. Data is
  stored in a columnar format, which enhances compression and retrieval
  efficiency, especially for analytical queries.

- **Jupiter Network**: Jupiter is Google’s next-generation data center
  network that provides the high-speed interconnectivity required to
  transfer data between computing resources and storage systems. It
  enables BigQuery to efficiently handle large-scale data processing by
  facilitating quick access to data stored in Colossus. The low-latency,
  high-bandwidth capabilities of Jupiter allow for rapid execution of
  complex queries, further boosting performance for users.

Together, Colossus Storage and Jupiter Network enable BigQuery to
deliver a serverless, scalable, and efficient data warehousing solution
suitable for large-scale analytics and real-time data processing.

## Column-oriented *vs.* record-oriented storage

Column-oriented storage organizes data by columns rather than rows,
allowing for efficient access and compression of similar data types.
This structure is particularly beneficial for analytical queries that
require operations on large datasets and often involve aggregations, as
it significantly reduces the amount of data that needs to be read from
disk, making it ideal for read-heavy workloads and analytics
applications.

On the other hand, record-oriented storage structures data by rows,
storing all attributes of a record together. This format is advantageous
for transaction processing and scenarios where complete records are
accessed frequently, such as in online transaction processing (OLTP)
systems. It improves performance for operations that involve inserting,
updating, or reading entire records, making it a suitable choice for
real-time applications that require quick access to individual records.

## Internal query processing - DREMEL

Dremel is a distributed query system developed by Google, designed for
running fast and interactive SQL queries on large datasets. Here’s a
concise explanation of how Dremel computes the result of a query:

1.  **Parsing and Query Planning**: When a query is submitted, Dremel
    first parses the SQL statement to create a query execution plan.
    This includes analyzing the query structure, validating the syntax,
    and optimizing the execution path based on the schema and available
    resources.

2.  **Columnar Storage**: Dremel accesses data stored in a columnar
    format, which allows it to read only relevant columns for the query,
    significantly reducing the amount of data processed and improving
    performance.

3.  **Tree Architecture**: Dremel employs a tree-like architecture with
    multiple levels of workers. The root of the tree is responsible for
    receiving the query and distributing it to child nodes. Each node
    may further distribute tasks to its own children, allowing for
    massive parallel processing.

4.  **Execution**: Each worker node executes its part of the query using
    a combination of execution strategies, including selective reading,
    filtering, and aggregating data. The computation is highly
    parallelized, taking advantage of multiple processors to speed up
    the query execution.

5.  **Result Aggregation**: As the worker nodes complete their tasks,
    they send intermediate results back to their parent nodes. This
    process continues up the tree, with nodes aggregating results until
    the final output is returned to the root node.

6.  **Final Output**: The root node compiles the results from all child
    nodes and returns the final result to the user. This approach
    ensures that Dremel can handle large-scale queries efficiently, even
    over vast datasets.

# Machine learning using BigQuery

Google BigQuery offers powerful machine learning capabilities through
BigQuery ML (BigQuery Machine Learning), which allows you to build and
deploy machine learning models directly within the BigQuery environment
using SQL queries. This makes it accessible for data analysts and data
scientists who may not be familiar with programming in Python or R.

### Key Features

- **In-database Processing**: Train models directly on large datasets
  without the need for data export.
- **Familiar SQL Interface**: Users can leverage standard SQL syntax to
  create and interact with machine learning models.
- **Integration**: Seamlessly integrates with other Google Cloud
  services, making it easy to manage data and models.

### Code Examples

1.  **Creating a Model**: To create a linear regression model, you can
    use the following SQL statement:

    ``` sql
    CREATE OR REPLACE MODEL `your_project_id.your_dataset.your_model`
    OPTIONS(
     model_type='linear_reg',
     input_label_cols=["target"],
     DATA_SPLIT_METHOD='AUTO_SPLIT'
     ) AS
    SELECT
      feature1,
      feature2,
      target
    FROM
      `your_project_id.your_dataset.your_table`;
    ```

2.  **Evaluating a Model**: After the model is created, you can evaluate
    its performance:

    ``` sql
    SELECT
      *
    FROM
      ML.EVALUATE(MODEL `your_project_id.your_dataset.your_model`,
      (
        SELECT
          feature1,
          feature2,
          target
        FROM
          `your_project_id.your_dataset.your_table`));
    ```

3.  **Making Predictions**: Once the model is trained, you can use it to
    make predictions on new data:

    ``` sql
    SELECT
      *
    FROM
      ML.PREDICT(MODEL `your_project_id.your_dataset.your_model`,
      (
        SELECT
          feature1,
          feature2
        FROM
          `your_project_id.your_dataset.new_data_table`));
    ```

### Supported Algorithms

BigQuery ML supports several algorithms, including linear regression,
logistic regression, K-means clustering, and various types of neural
networks, making it versatile for numerous use cases.

### Conclusion

Google BigQuery ML simplifies the process of building and deploying
machine learning models, allowing users to harness the power of Google
Cloud’s big data capabilities with their existing SQL skills. This
integration is particularly useful for organizations looking to leverage
data for predictive analytics without the overhead of complex machine
learning infrastructure.’

## Deployment

Here’s a concise guide to deploy a BigQuery ML model with TensorFlow
Serving:

Prep step - Get the model out of BigQuery

There are 3 main ways to export a BigQuery ML model to a Cloud Storage
bucket:

1.  Using the Console:

``` bash
- Open BigQuery in Google Cloud Console
- Navigate to Resources > Your Project > Dataset
- Click on your model
- Click "Export Model"
- Select Cloud Storage location
- Click "Export"
```

2.  Using SQL:

``` sql
EXPORT MODEL `myproject.mydataset.mymodel` 
OPTIONS(URI = 'gs://bucket/path/to/saved_model/')
```

3.  Using bq command-line:

``` bash
bq extract --model \
'mydataset.mymodel' \
gs://example-bucket/mymodel_folder
```

The exported model will be in TensorFlow SavedModel format by
default\[1\]. Make sure you have the necessary permissions to access the
BigQuery ML model and write to the Cloud Storage bucket\[1\]. The
BigQuery dataset and the Cloud Storage bucket must be in the same
location\[1\].

Citations: \[1\] https://cloud.google.com/bigquery/docs/exporting-models
\[2\]
https://codelabs.developers.google.com/codelabs/bqml-vertex-prediction
\[3\] https://beam.apache.org/documentation/patterns/bqml/ \[4\]
https://wiki.sfeir.com/googlecloudplatform/bigdata/bigquery/bigqueryml/
\[5\]
https://www.googlecloudcommunity.com/gc/Infrastructure-Compute-Storage/Export-BigQuery-table-to-Google-Cloud-Storage-in-a-separate/m-p/700490
\[6\] https://cloud.google.com/bigquery/docs/export-model-tutorial \[7\]
https://stackoverflow.com/questions/78517490/bigquery-ml-model-to-predict-outside-bq
\[8\]
https://stackoverflow.com/questions/48127069/using-google-ml-engine-with-bigquery

1.  Prepare model directory:

``` bash
mkdir -p /models/mymodel/1
gsutil cp -r gs://your-bucket/model/* /models/mymodel/1/
```

2.  Create directory structure:

<!-- -->

    /models/
      └── mymodel/
          └── 1/
              ├── saved_model.pb
              └── variables/

3.  Deploy with Docker:

``` bash
docker pull tensorflow/serving
docker run -t --rm -p 8501:8501 \
    -v "/models:/models" \
    -e MODEL_NAME=mymodel \
    tensorflow/serving
```

4.  Test deployment:

``` bash
curl -X POST http://localhost:8501/v1/models/mymodel:predict \
    -d '{"instances": [your_input_data]}'
```

Note: Ensure model version directory (1) contains saved_model.pb and
variables directory from BigQuery ML export.

# Homework

## Preparation - load the data to GCS using Kestra

``` yaml
id: taxi_parquet
namespace: zoomcamp

inputs:
  - id: taxi
    type: SELECT
    displayName: Select taxi type
    values: [yellow, green]
    defaults: yellow

  - id: year
    type: INT
    displayName: Year
    defaults: 2024

  - id: month
    type: SELECT
    values: [1,2,3,4,5,6,7,8,9,10,11,12]
    displayName: month
    defaults: 1

variables:
  file: "{{inputs.taxi}}_tripdata_{{inputs.year}}-{{inputs.month |  number('INT') | numberFormat('00')}}.parquet"
  gcs_file: "gs://{{kv('GCP_BUCKET_NAME')}}/{{vars.file}}"
  table: "{{kv('GCP_DATASET')}}.{{inputs.taxi}}_tripdata_{{inputs.year}}-{{inputs.month |  number('INT') | numberFormat('00')}}"
  data: "{{outputs.extract.outputFiles[render(vars.file)]}}"

# inputs.taxi ~ '_tripdata_' ~ inputs.year ~ '-' ~ inputs.month |  number('INT') | numberFormat('00') ~ '.parquet'

tasks:
  - id: set_label
    type: io.kestra.plugin.core.execution.Labels
    labels:
      file: "{{render(vars.file)}}"
      taxi: "{{inputs.taxi}}"

  - id: extract
    type: io.kestra.plugin.scripts.shell.Commands
    outputFiles:
      - "*.parquet"
    taskRunner:
      type: io.kestra.plugin.core.runner.Process
    commands:
      - wget -q https://d37ci6vzurychx.cloudfront.net/trip-data/{{render(vars.file)}}

  - id: upload_to_gcs
    type: io.kestra.plugin.gcp.gcs.Upload
    from: "{{render(vars.data)}}"
    to: "{{render(vars.gcs_file)}}"

  - id: purge_files
    type: io.kestra.plugin.core.storage.PurgeCurrentExecutionFiles
    description: To avoid cluttering your storage, we will remove the downloaded files

pluginDefaults:
  - type: io.kestra.plugin.gcp
    values:
      serviceAccount: "{{kv('GCP_CREDS')}}"
      projectId: "{{kv('GCP_PROJECT_ID')}}"
      location: "{{kv('GCP_LOCATION')}}"
      bucket: "{{kv('GCP_BUCKET_NAME')}}"
```

- Creating external tables:

  - one by one

    ``` sql
    CREATE EXTERNAL TABLE `workspaceaddon-436615.zoomcamp.yellow_trip_data_2024-01` AS
    OPTIONS(
        format ="parquet",
        uris = ['gs://workspaceaddon-436615/yellow_tripdata_2024-01.parquet']
        );
    ```

  - using a for loop

    ``` sql
    BEGIN
      FOR month_number IN (
        SELECT FORMAT('%02d', num) as month
        FROM UNNEST(GENERATE_ARRAY(3, 6)) as num
      ) DO
        EXECUTE IMMEDIATE FORMAT("""
          CREATE EXTERNAL TABLE `workspaceaddon-436615.zoomcamp.yellow_trip_data_2024-%s`
          OPTIONS(
            format = "parquet",
            uris = ['gs://workspaceaddon-436615/yellow_tripdata_2024-%s.parquet']
          )
        """, month_number.month, month_number.month
        );
      END FOR;
    END;
    ```

  - Materialize Tables

``` sql
BEGIN
  FOR month_number IN (
    SELECT FORMAT('%02d', num) as month
    FROM UNNEST(GENERATE_ARRAY(1, 6)) as num
  ) DO
    EXECUTE IMMEDIATE FORMAT("""
      CREATE TABLE `workspaceaddon-436615.zoomcamp.yellow_trip_data_2024-%s` AS
      SELECT * FROM `workspaceaddon-436615.zoomcamp.yellow_trip_data_2024-%s_ext`
    """, month_number.month, month_number.month
    );
  END FOR;
END;
```

## Question 1:

What is count of records for the 2024 Yellow Taxi Data?

``` sql

-- union all tables
EXECUTE IMMEDIATE (
  WITH months AS (
    SELECT FORMAT('SELECT COUNT(*) as count FROM `workspaceaddon-436615.zoomcamp.yellow_trip_data_2024-%02d`', num) as query
    FROM UNNEST(GENERATE_ARRAY(1, 6)) as num
  )
  SELECT 'SELECT SUM(count) as total_records FROM (' || STRING_AGG(query, ' UNION ALL ') || ')'
  FROM months
);

```

- [ ] 65,623
- [ ] 840,402
- [x] 20,332,093
- [ ] 85,431,289

## Question 2:

Write a query to count the distinct number of PULocationIDs for the
entire dataset on both the tables.</br> What is the **estimated amount**
of data that will be read when this query is executed on the External
Table and the Table?

``` sql
SELECT COUNT(DISTINCT PULocationIDs)
FROM `workspaceaddon-436615.zoomcamp.yellow_trip_data_2024_ext`
```

``` sql
SELECT COUNT(DISTINCT PULocationIDs)
FROM `workspaceaddon-436615.zoomcamp.yellow_trip_data_2024`
```

- [ ] 18.82 MB for the External Table and 47.60 MB for the Materialized
  Table
- [x] 0 MB for the External Table and 155.12 MB for the Materialized
  Table
- [ ] 2.14 GB for the External Table and 0MB for the Materialized Table
- [ ] 0 MB for the External Table and 0MB for the Materialized Table

## Question 3:

Write a query to retrieve the PULocationID from the table (not the
external table) in BigQuery. Now write a query to retrieve the
PULocationID and DOLocationID on the same table. Why are the estimated
number of Bytes different?

- BigQuery is a columnar database, and it only scans the specific
  columns requested in the query. Querying two columns (PULocationID,
  DOLocationID) requires reading more data than querying one column
  (PULocationID), leading to a higher estimated number of bytes
  processed.

- BigQuery duplicates data across multiple storage partitions, so
  selecting two columns instead of one requires scanning the table
  twice, doubling the estimated bytes processed.

- BigQuery automatically caches the first queried column, so adding a
  second column increases processing time but does not affect the
  estimated bytes scanned.

- When selecting multiple columns, BigQuery performs an implicit join
  operation between them, increasing the estimated bytes processed

## Question 4:

How many records have a fare_amount of 0?

``` sql
SELECT COUNT(*)
FROM `workspaceaddon-436615.zoomcamp.yellow_trip_data_2024`
WHERE fare_amount = 0
```

- [ ] 128,210
- [ ] 546,578
- [ ] 20,188,016
- [x] 8,333

## Question 5:

What is the best strategy to make an optimized table in Big Query if
your query will always filter based on tpep_dropoff_datetime and order
the results by VendorID (Create a new table with this strategy)

- [x] Partition by tpep_dropoff_datetime and Cluster on VendorID
- [ ] Cluster on by tpep_dropoff_datetime and Cluster on VendorID
- [ ] Cluster on tpep_dropoff_datetime Partition by VendorID
- [ ] Partition by tpep_dropoff_datetime and Partition by VendorID

``` sql
CREATE TABLE `workspaceaddon-436615.zoomcamp.yellow_trip_data_2024_clus`
PARTITION BY DATE(tpep_dropoff_datetime)
CLUSTER BY VendorID AS (
SELECT * FROM `workspaceaddon-436615.zoomcamp.yellow_trip_data_2024`
)
```

## Question 6:

Write a query to retrieve the distinct VendorIDs between
tpep_dropoff_datetime 2024-03-01 and 2024-03-15 (inclusive)</br>

Use the materialized table you created earlier in your from clause and
note the estimated bytes. Now change the table in the from clause to the
partitioned table you created for question 5 and note the estimated
bytes processed. What are these values? </br>

``` sql
SELECT DISTINCT VendorID
FROM `workspaceaddon-436615.zoomcamp.yellow_trip_data_2024`
WHERE DATE(tpep_dropoff_datetime) BETWEEN '2024-03-01' AND '2024-03-15'
```

Choose the answer which most closely matches.</br>

- [ ] 12.47 MB for non-partitioned table and 326.42 MB for the
  partitioned table
- [x] 310.24 MB for non-partitioned table and 26.84 MB for the
  partitioned table
- [ ] 5.87 MB for non-partitioned table and 0 MB for the partitioned
  table
- [ ] 310.31 MB for non-partitioned table and 285.64 MB for the
  partitioned table

## Question 7:

Where is the data stored in the External Table you created?

- [ ] Big Query
- [ ] Container Registry
- [x] GCP Bucket
- [ ] Big Table

## Question 8:

It is best practice in Big Query to always cluster your data:

- [ ] True
- [x] False
