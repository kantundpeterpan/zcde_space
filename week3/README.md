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
print(key_path)
```

    [1] "/home/kantundpeterpan/projects/zoomcamp/zcde_space/week1/3_intro_terraform/workspaceaddon-436615-4bcf737409b7.json"

``` r
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
| green_tripdata2020_part | 20200207     |      15977 |
| green_tripdata2020_part | 20200131     |      15645 |
| green_tripdata2020_part | 20200306     |      15579 |
| green_tripdata2020_part | 20200213     |      15516 |
| green_tripdata2020_part | 20200116     |      15218 |
| green_tripdata2020_part | 20200111     |      15175 |
| green_tripdata2020_part | 20200124     |      15148 |
| green_tripdata2020_part | 20200221     |      15069 |
| green_tripdata2020_part | 20200102     |      15023 |
| green_tripdata2020_part | 20200212     |      14964 |
| green_tripdata2020_part | 20200305     |      14930 |
| green_tripdata2020_part | 20200130     |      14911 |
| green_tripdata2020_part | 20200205     |      14893 |
| green_tripdata2020_part | 20200206     |      14846 |
| green_tripdata2020_part | 20200123     |      14757 |
| green_tripdata2020_part | 20200226     |      14748 |
| green_tripdata2020_part | 20200129     |      14564 |
| green_tripdata2020_part | 20200122     |      14552 |
| green_tripdata2020_part | 20200229     |      14444 |
| green_tripdata2020_part | 20200128     |      14383 |
| green_tripdata2020_part | 20200304     |      14320 |
| green_tripdata2020_part | 20200220     |      14318 |
| green_tripdata2020_part | 20200104     |      14295 |
| green_tripdata2020_part | 20200113     |      14288 |
| green_tripdata2020_part | 20200121     |      14191 |
| green_tripdata2020_part | 20200115     |      14157 |
| green_tripdata2020_part | 20200303     |      14026 |
| green_tripdata2020_part | 20200204     |      13981 |
| green_tripdata2020_part | 20200114     |      13977 |
| green_tripdata2020_part | 20200225     |      13909 |
| green_tripdata2020_part | 20200219     |      13729 |
| green_tripdata2020_part | 20200208     |      13643 |
| green_tripdata2020_part | 20200210     |      13555 |
| green_tripdata2020_part | 20200211     |      13535 |
| green_tripdata2020_part | 20200203     |      13485 |
| green_tripdata2020_part | 20200127     |      13451 |
| green_tripdata2020_part | 20200112     |      13442 |
| green_tripdata2020_part | 20200125     |      13311 |
| green_tripdata2020_part | 20200307     |      13230 |
| green_tripdata2020_part | 20200224     |      13099 |
| green_tripdata2020_part | 20200302     |      13024 |
| green_tripdata2020_part | 20200201     |      13011 |
| green_tripdata2020_part | 20200215     |      12786 |
| green_tripdata2020_part | 20200222     |      12779 |
| green_tripdata2020_part | 20200105     |      12732 |
| green_tripdata2020_part | 20200218     |      12652 |
| green_tripdata2020_part | 20200312     |      12296 |
| green_tripdata2020_part | 20200311     |      12268 |
| green_tripdata2020_part | 20200310     |      12258 |
| green_tripdata2020_part | 20200309     |      12002 |
| green_tripdata2020_part | 20200202     |      11906 |
| green_tripdata2020_part | 20200126     |      11772 |
| green_tripdata2020_part | 20200301     |      11495 |
| green_tripdata2020_part | 20200209     |      11431 |
| green_tripdata2020_part | 20200223     |      11423 |
| green_tripdata2020_part | 20200119     |      11193 |
| green_tripdata2020_part | 20200118     |      11080 |
| green_tripdata2020_part | 20200101     |      10970 |
| green_tripdata2020_part | 20200313     |      10783 |
| green_tripdata2020_part | 20200216     |      10671 |
| green_tripdata2020_part | 20200308     |      10573 |
| green_tripdata2020_part | 20200120     |       9684 |
| green_tripdata2020_part | 20200217     |       9420 |
| green_tripdata2020_part | 20200314     |       7787 |
| green_tripdata2020_part | 20200316     |       7149 |
| green_tripdata2020_part | 20200315     |       5642 |
| green_tripdata2020_part | 20200317     |       5417 |
| green_tripdata2020_part | 20200318     |       4896 |
| green_tripdata2020_part | 20200319     |       4086 |
| green_tripdata2020_part | 20200320     |       3958 |
| green_tripdata2020_part | 20201110     |       3686 |
| green_tripdata2020_part | 20200918     |       3684 |
| green_tripdata2020_part | 20201030     |       3666 |
| green_tripdata2020_part | 20201112     |       3653 |
| green_tripdata2020_part | 20201113     |       3626 |
| green_tripdata2020_part | 20201120     |       3610 |
| green_tripdata2020_part | 20201116     |       3607 |
| green_tripdata2020_part | 20201001     |       3606 |
| green_tripdata2020_part | 20201002     |       3597 |
| green_tripdata2020_part | 20201102     |       3547 |
| green_tripdata2020_part | 20201023     |       3542 |
| green_tripdata2020_part | 20201015     |       3540 |
| green_tripdata2020_part | 20201014     |       3538 |
| green_tripdata2020_part | 20201119     |       3527 |
| green_tripdata2020_part | 20201202     |       3511 |
| green_tripdata2020_part | 20201029     |       3508 |
| green_tripdata2020_part | 20201105     |       3501 |
| green_tripdata2020_part | 20201124     |       3498 |
| green_tripdata2020_part | 20201201     |       3493 |
| green_tripdata2020_part | 20201028     |       3491 |
| green_tripdata2020_part | 20201118     |       3490 |
| green_tripdata2020_part | 20200925     |       3484 |
| green_tripdata2020_part | 20201106     |       3481 |
| green_tripdata2020_part | 20201022     |       3464 |
| green_tripdata2020_part | 20201117     |       3462 |
| green_tripdata2020_part | 20200924     |       3454 |
| green_tripdata2020_part | 20201203     |       3451 |
| green_tripdata2020_part | 20201008     |       3444 |
| green_tripdata2020_part | 20201109     |       3443 |
| green_tripdata2020_part | 20201009     |       3435 |
| green_tripdata2020_part | 20201211     |       3426 |
| green_tripdata2020_part | 20200917     |       3423 |
| green_tripdata2020_part | 20201123     |       3417 |
| green_tripdata2020_part | 20200923     |       3414 |
| green_tripdata2020_part | 20201223     |       3402 |
| green_tripdata2020_part | 20201027     |       3396 |
| green_tripdata2020_part | 20201016     |       3393 |
| green_tripdata2020_part | 20201210     |       3383 |
| green_tripdata2020_part | 20201215     |       3383 |
| green_tripdata2020_part | 20200914     |       3375 |
| green_tripdata2020_part | 20200930     |       3375 |
| green_tripdata2020_part | 20201204     |       3358 |
| green_tripdata2020_part | 20201019     |       3352 |
| green_tripdata2020_part | 20201005     |       3348 |
| green_tripdata2020_part | 20201104     |       3343 |
| green_tripdata2020_part | 20201021     |       3340 |
| green_tripdata2020_part | 20200916     |       3337 |
| green_tripdata2020_part | 20200915     |       3325 |
| green_tripdata2020_part | 20201026     |       3324 |
| green_tripdata2020_part | 20201103     |       3323 |
| green_tripdata2020_part | 20201007     |       3319 |
| green_tripdata2020_part | 20201125     |       3317 |
| green_tripdata2020_part | 20201209     |       3316 |
| green_tripdata2020_part | 20201020     |       3316 |
| green_tripdata2020_part | 20200911     |       3315 |
| green_tripdata2020_part | 20200921     |       3302 |
| green_tripdata2020_part | 20201208     |       3293 |
| green_tripdata2020_part | 20201006     |       3273 |
| green_tripdata2020_part | 20200904     |       3270 |
| green_tripdata2020_part | 20200909     |       3264 |
| green_tripdata2020_part | 20201013     |       3263 |
| green_tripdata2020_part | 20201207     |       3262 |
| green_tripdata2020_part | 20201221     |       3253 |
| green_tripdata2020_part | 20200902     |       3250 |
| green_tripdata2020_part | 20201111     |       3244 |
| green_tripdata2020_part | 20200929     |       3234 |
| green_tripdata2020_part | 20200922     |       3219 |
| green_tripdata2020_part | 20201214     |       3201 |
| green_tripdata2020_part | 20200828     |       3193 |
| green_tripdata2020_part | 20200821     |       3190 |
| green_tripdata2020_part | 20200908     |       3171 |
| green_tripdata2020_part | 20200820     |       3164 |
| green_tripdata2020_part | 20201222     |       3163 |
| green_tripdata2020_part | 20200826     |       3116 |
| green_tripdata2020_part | 20200910     |       3111 |
| green_tripdata2020_part | 20200928     |       3108 |
| green_tripdata2020_part | 20200903     |       3097 |
| green_tripdata2020_part | 20200831     |       3066 |
| green_tripdata2020_part | 20200901     |       3061 |
| green_tripdata2020_part | 20200729     |       2990 |
| green_tripdata2020_part | 20200806     |       2984 |
| green_tripdata2020_part | 20200807     |       2969 |
| green_tripdata2020_part | 20200819     |       2956 |
| green_tripdata2020_part | 20200827     |       2955 |
| green_tripdata2020_part | 20201130     |       2950 |
| green_tripdata2020_part | 20201218     |       2942 |
| green_tripdata2020_part | 20200818     |       2927 |
| green_tripdata2020_part | 20201230     |       2918 |
| green_tripdata2020_part | 20200814     |       2899 |
| green_tripdata2020_part | 20201229     |       2891 |
| green_tripdata2020_part | 20200805     |       2887 |
| green_tripdata2020_part | 20200825     |       2881 |
| green_tripdata2020_part | 20200824     |       2871 |
| green_tripdata2020_part | 20200813     |       2868 |
| green_tripdata2020_part | 20200803     |       2840 |
| green_tripdata2020_part | 20200730     |       2833 |
| green_tripdata2020_part | 20200812     |       2814 |
| green_tripdata2020_part | 20201228     |       2811 |
| green_tripdata2020_part | 20200810     |       2781 |
| green_tripdata2020_part | 20201216     |       2773 |
| green_tripdata2020_part | 20200817     |       2769 |
| green_tripdata2020_part | 20200723     |       2740 |
| green_tripdata2020_part | 20200811     |       2733 |
| green_tripdata2020_part | 20201031     |       2729 |
| green_tripdata2020_part | 20200722     |       2699 |
| green_tripdata2020_part | 20200728     |       2678 |
| green_tripdata2020_part | 20201003     |       2660 |
| green_tripdata2020_part | 20201024     |       2658 |
| green_tripdata2020_part | 20201231     |       2654 |
| green_tripdata2020_part | 20200626     |       2650 |
| green_tripdata2020_part | 20200714     |       2634 |
| green_tripdata2020_part | 20200727     |       2628 |
| green_tripdata2020_part | 20200717     |       2608 |
| green_tripdata2020_part | 20201121     |       2608 |
| green_tripdata2020_part | 20200715     |       2596 |
| green_tripdata2020_part | 20200701     |       2575 |
| green_tripdata2020_part | 20200702     |       2575 |
| green_tripdata2020_part | 20201107     |       2575 |
| green_tripdata2020_part | 20200724     |       2568 |
| green_tripdata2020_part | 20200731     |       2564 |
| green_tripdata2020_part | 20200515     |       2562 |
| green_tripdata2020_part | 20201010     |       2551 |
| green_tripdata2020_part | 20200919     |       2550 |
| green_tripdata2020_part | 20200709     |       2540 |
| green_tripdata2020_part | 20200912     |       2536 |
| green_tripdata2020_part | 20200716     |       2527 |
| green_tripdata2020_part | 20200321     |       2520 |
| green_tripdata2020_part | 20200708     |       2519 |
| green_tripdata2020_part | 20200721     |       2505 |
| green_tripdata2020_part | 20200801     |       2485 |
| green_tripdata2020_part | 20201017     |       2484 |
| green_tripdata2020_part | 20201114     |       2483 |
| green_tripdata2020_part | 20200625     |       2475 |
| green_tripdata2020_part | 20200513     |       2458 |
| green_tripdata2020_part | 20200926     |       2441 |
| green_tripdata2020_part | 20200710     |       2424 |
| green_tripdata2020_part | 20200623     |       2423 |
| green_tripdata2020_part | 20200514     |       2417 |
| green_tripdata2020_part | 20200630     |       2413 |
| green_tripdata2020_part | 20200822     |       2412 |
| green_tripdata2020_part | 20200624     |       2411 |
| green_tripdata2020_part | 20200619     |       2407 |
| green_tripdata2020_part | 20201224     |       2387 |
| green_tripdata2020_part | 20200706     |       2385 |
| green_tripdata2020_part | 20200629     |       2369 |
| green_tripdata2020_part | 20201012     |       2366 |
| green_tripdata2020_part | 20200622     |       2362 |
| green_tripdata2020_part | 20200612     |       2350 |
| green_tripdata2020_part | 20200610     |       2329 |
| green_tripdata2020_part | 20200605     |       2323 |
| green_tripdata2020_part | 20200506     |       2293 |
| green_tripdata2020_part | 20200512     |       2293 |
| green_tripdata2020_part | 20200720     |       2291 |
| green_tripdata2020_part | 20200905     |       2289 |
| green_tripdata2020_part | 20200618     |       2286 |
| green_tripdata2020_part | 20200808     |       2274 |
| green_tripdata2020_part | 20200507     |       2270 |
| green_tripdata2020_part | 20200804     |       2270 |
| green_tripdata2020_part | 20200713     |       2269 |
| green_tripdata2020_part | 20200815     |       2249 |
| green_tripdata2020_part | 20200617     |       2247 |
| green_tripdata2020_part | 20201212     |       2246 |
| green_tripdata2020_part | 20200609     |       2244 |
| green_tripdata2020_part | 20201219     |       2243 |
| green_tripdata2020_part | 20200707     |       2237 |
| green_tripdata2020_part | 20200703     |       2223 |
| green_tripdata2020_part | 20200608     |       2218 |
| green_tripdata2020_part | 20200725     |       2203 |
| green_tripdata2020_part | 20200529     |       2184 |
| green_tripdata2020_part | 20200615     |       2176 |
| green_tripdata2020_part | 20200611     |       2174 |
| green_tripdata2020_part | 20200508     |       2167 |
| green_tripdata2020_part | 20200603     |       2166 |
| green_tripdata2020_part | 20200616     |       2165 |
| green_tripdata2020_part | 20200604     |       2157 |
| green_tripdata2020_part | 20201127     |       2146 |
| green_tripdata2020_part | 20201128     |       2146 |
| green_tripdata2020_part | 20200511     |       2143 |
| green_tripdata2020_part | 20200527     |       2140 |
| green_tripdata2020_part | 20201205     |       2097 |
| green_tripdata2020_part | 20200528     |       2045 |
| green_tripdata2020_part | 20200501     |       2026 |
| green_tripdata2020_part | 20200518     |       2019 |
| green_tripdata2020_part | 20201018     |       2013 |
| green_tripdata2020_part | 20200718     |       2008 |
| green_tripdata2020_part | 20201101     |       1985 |
| green_tripdata2020_part | 20200829     |       1980 |
| green_tripdata2020_part | 20200601     |       1971 |
| green_tripdata2020_part | 20201108     |       1963 |
| green_tripdata2020_part | 20200526     |       1954 |
| green_tripdata2020_part | 20200323     |       1950 |
| green_tripdata2020_part | 20200505     |       1930 |
| green_tripdata2020_part | 20200520     |       1917 |
| green_tripdata2020_part | 20200602     |       1896 |
| green_tripdata2020_part | 20200522     |       1885 |
| green_tripdata2020_part | 20200516     |       1875 |
| green_tripdata2020_part | 20201025     |       1864 |
| green_tripdata2020_part | 20200830     |       1859 |
| green_tripdata2020_part | 20200606     |       1849 |
| green_tripdata2020_part | 20200920     |       1844 |
| green_tripdata2020_part | 20200519     |       1843 |
| green_tripdata2020_part | 20201122     |       1828 |
| green_tripdata2020_part | 20200521     |       1826 |
| green_tripdata2020_part | 20201011     |       1826 |
| green_tripdata2020_part | 20200324     |       1822 |
| green_tripdata2020_part | 20200504     |       1822 |
| green_tripdata2020_part | 20200327     |       1812 |
| green_tripdata2020_part | 20200613     |       1809 |
| green_tripdata2020_part | 20201004     |       1809 |
| green_tripdata2020_part | 20200627     |       1803 |
| green_tripdata2020_part | 20200913     |       1803 |
| green_tripdata2020_part | 20200620     |       1801 |
| green_tripdata2020_part | 20200927     |       1794 |
| green_tripdata2020_part | 20201213     |       1789 |
| green_tripdata2020_part | 20200823     |       1782 |
| green_tripdata2020_part | 20201126     |       1766 |
| green_tripdata2020_part | 20201206     |       1731 |
| green_tripdata2020_part | 20200325     |       1728 |
| green_tripdata2020_part | 20200907     |       1727 |
| green_tripdata2020_part | 20200906     |       1724 |
| green_tripdata2020_part | 20200802     |       1718 |
| green_tripdata2020_part | 20200711     |       1716 |
| green_tripdata2020_part | 20201129     |       1695 |
| green_tripdata2020_part | 20200704     |       1694 |
| green_tripdata2020_part | 20201226     |       1693 |
| green_tripdata2020_part | 20201115     |       1689 |
| green_tripdata2020_part | 20200809     |       1679 |
| green_tripdata2020_part | 20200430     |       1677 |
| green_tripdata2020_part | 20200530     |       1672 |
| green_tripdata2020_part | 20200326     |       1651 |
| green_tripdata2020_part | 20201220     |       1636 |
| green_tripdata2020_part | 20200509     |       1594 |
| green_tripdata2020_part | 20200429     |       1576 |
| green_tripdata2020_part | 20200726     |       1565 |
| green_tripdata2020_part | 20200403     |       1525 |
| green_tripdata2020_part | 20200502     |       1508 |
| green_tripdata2020_part | 20200712     |       1503 |
| green_tripdata2020_part | 20200428     |       1501 |
| green_tripdata2020_part | 20200816     |       1493 |
| green_tripdata2020_part | 20200719     |       1485 |
| green_tripdata2020_part | 20200401     |       1482 |
| green_tripdata2020_part | 20200705     |       1472 |
| green_tripdata2020_part | 20200628     |       1431 |
| green_tripdata2020_part | 20200330     |       1426 |
| green_tripdata2020_part | 20201227     |       1426 |
| green_tripdata2020_part | 20200607     |       1425 |
| green_tripdata2020_part | 20200331     |       1419 |
| green_tripdata2020_part | 20200402     |       1403 |
| green_tripdata2020_part | 20200523     |       1399 |
| green_tripdata2020_part | 20200417     |       1397 |
| green_tripdata2020_part | 20200427     |       1394 |
| green_tripdata2020_part | 20200621     |       1392 |
| green_tripdata2020_part | 20200614     |       1388 |
| green_tripdata2020_part | 20200322     |       1350 |
| green_tripdata2020_part | 20200510     |       1341 |
| green_tripdata2020_part | 20200422     |       1284 |
| green_tripdata2020_part | 20200406     |       1282 |
| green_tripdata2020_part | 20200525     |       1274 |
| green_tripdata2020_part | 20200423     |       1274 |
| green_tripdata2020_part | 20200328     |       1272 |
| green_tripdata2020_part | 20200517     |       1272 |
| green_tripdata2020_part | 20200424     |       1271 |
| green_tripdata2020_part | 20200416     |       1259 |
| green_tripdata2020_part | 20200415     |       1239 |
| green_tripdata2020_part | 20200420     |       1226 |
| green_tripdata2020_part | 20200410     |       1225 |
| green_tripdata2020_part | 20200531     |       1219 |
| green_tripdata2020_part | 20200414     |       1198 |
| green_tripdata2020_part | 20200408     |       1170 |
| green_tripdata2020_part | 20200409     |       1156 |
| green_tripdata2020_part | 20200404     |       1138 |
| green_tripdata2020_part | 20200407     |       1135 |
| green_tripdata2020_part | 20200425     |       1134 |
| green_tripdata2020_part | 20201225     |       1097 |
| green_tripdata2020_part | 20200421     |       1079 |
| green_tripdata2020_part | 20200503     |       1011 |
| green_tripdata2020_part | 20200524     |       1001 |
| green_tripdata2020_part | 20200418     |        974 |
| green_tripdata2020_part | 20200413     |        972 |
| green_tripdata2020_part | 20200411     |        958 |
| green_tripdata2020_part | 20201217     |        899 |
| green_tripdata2020_part | 20200329     |        731 |
| green_tripdata2020_part | 20200405     |        712 |
| green_tripdata2020_part | 20200419     |        692 |
| green_tripdata2020_part | 20200426     |        666 |
| green_tripdata2020_part | 20200412     |        608 |
| green_tripdata2020_part | 20090101     |         25 |
| green_tripdata2020_part | 20191231     |         18 |
| green_tripdata2020_part | 20081231     |          4 |
| green_tripdata2020_part | 20100923     |          3 |
| green_tripdata2020_part | 20410817     |          1 |
| green_tripdata2020_part | 20210101     |          1 |
| green_tripdata2020_part | 20191218     |          1 |

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
