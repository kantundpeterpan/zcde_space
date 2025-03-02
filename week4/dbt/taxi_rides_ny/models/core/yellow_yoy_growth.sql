with

yellow_2019 as (
    select
      year, quarter,
      sum(total_amount) as quarter_total
    from {{ref("facts_trips")}}
    where service_type = 'Yellow' and year = 2019 
    group by year, quarter
),

yellow_2020 as (
    select 
      year, quarter,
      sum(total_amount) as quarter_total
    from {{ref("facts_trips")}}
    where service_type = 'Yellow' and year = 2020 
    group by year, quarter
)

select
  y20.quarter,
  (y20.quarter_total - y19.quarter_total) / y19.quarter_total as yoy
FROM yellow_2020 y20
INNER JOIN yellow_2019 y19
ON y20.quarter = y19.quarter