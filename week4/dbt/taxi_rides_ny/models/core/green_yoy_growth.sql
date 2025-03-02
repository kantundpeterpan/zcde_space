with

green_2019 as (
    select
      year, quarter,
      sum(total_amount) as quarter_total
    from {{ref("facts_trips")}}
    where service_type = 'Green' and year = 2019 
    group by year, quarter
),

green_2020 as (
    select 
      year, quarter,
      sum(total_amount) as quarter_total
    from {{ref("facts_trips")}}
    where service_type = 'Green' and year = 2020 
    group by year, quarter
)

select
  g20.quarter,
  (g20.quarter_total - g19.quarter_total) / g19.quarter_total as yoy
FROM green_2020 g20
INNER JOIN green_2019 g19
ON g20.quarter = g19.quarter