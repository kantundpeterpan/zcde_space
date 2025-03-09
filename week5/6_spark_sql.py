#!/usr/bin/env python
# coding: utf-8

# In[3]:


import pyspark
from pyspark.sql import SparkSession
import argparse

parser = argparse.ArgumentParser()

parser.add_argument('--input_green', required = True)
parser.add_argument('--input_yellow', required = True)
parser.add_argument('--output', required = True)

args = parser.parse_args()

# In[5]:

    # .master("spark://127.0.0.1:7077") \

spark = SparkSession.builder \
    .appName('pyspark-run-with-gcp-bucket2') \
    .config("spark.jars", "/home/kantundpeterpan/projects/zoomcamp/zcde_space/week5/gcs-connector-hadoop3-latest.jar") \
    .getOrCreate()


# In[6]:


# Configure GCS authentication
spark.conf.set("google.cloud.auth.service.account.enable", "true")
spark._jsc.hadoopConfiguration().set("google.cloud.auth.service.account.json.keyfile", 
                                     "/home/kantundpeterpan/projects/zoomcamp/zcde_space/week1/3_intro_terraform/workspaceaddon-436615-4bcf737409b7.json")
spark._jsc.hadoopConfiguration().set('fs.gs.impl', 'com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem')


# In[8]:



# In[15]:


bucket_url = 'gs://workspaceaddon-436615'


# In[30]:


df_green = spark.read.parquet(bucket_url + '/green/' + args.input_green)


# In[31]:


df_green.printSchema()


# In[32]:


df_green = df_green \
    .withColumnRenamed(
        "lpep_pickup_datetime", "pickup_datetime"
    ) \
    .withColumnRenamed(
        "lpep_dropoff_datetime", "dropoff_datetime"
    )


# In[36]:


df_yellow = spark.read.parquet(bucket_url + '/yellow/' + args.input_yellow) \
    .withColumnRenamed(
        "tpep_pickup_datetime", "pickup_datetime"
    ) \
    .withColumnRenamed(
        "tpep_dropoff_datetime", "dropoff_datetime"
    )


# In[37]:


# df_yellow.printSchema()


# In[42]:


from pyspark.sql import functions as F


# In[39]:


common_cols = []

for col in df_green.columns:
    if col in df_yellow.columns:
        common_cols.append(col)


# In[60]:


df_green_sel = df_green \
    .select(common_cols) \
    .withColumn("service_type", F.lit("green"))


# In[61]:


df_yellow_sel = df_yellow \
    .select(common_cols) \
    .withColumn("service_type", F.lit("yellow"))


# In[62]:


df_trips_data = df_green_sel.unionAll(df_yellow_sel)


# In[64]:


df_trips_data.groupBy("service_type").count().show()


# In[65]:


df_trips_data.registerTempTable("trips_data")


# In[ ]:


df_result = spark.sql("""
SELECT 
    -- Reveneue grouping 
    PULocationID AS revenue_zone,
    date_trunc('month', pickup_datetime) AS revenue_month, 
    service_type, 

    -- Revenue calculation 
    SUM(fare_amount) AS revenue_monthly_fare,
    SUM(extra) AS revenue_monthly_extra,
    SUM(mta_tax) AS revenue_monthly_mta_tax,
    SUM(tip_amount) AS revenue_monthly_tip_amount,
    SUM(tolls_amount) AS revenue_monthly_tolls_amount,
    SUM(improvement_surcharge) AS revenue_monthly_improvement_surcharge,
    SUM(total_amount) AS revenue_monthly_total_amount,
    SUM(congestion_surcharge) AS revenue_monthly_congestion_surcharge,

    -- Additional calculations
    AVG(passenger_count) AS avg_montly_passenger_count,
    AVG(trip_distance) AS avg_montly_trip_distance
FROM
    trips_data
GROUP BY
    1, 2, 3
""")



# In[78]:


df_result.coalesce(1).write.parquet(
    bucket_url + args.output,
    mode = 'overwrite'
    )


# In[81]:


spark.stop()

