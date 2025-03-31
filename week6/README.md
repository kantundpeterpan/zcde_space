# Week 6 - Stream processing
Heiner Atze

# Stack

- Kafka/redpanda : store incoming event data
- Apache Flink : from source (kafka, redpanda) to sink (data lake,
  warehoue)

# Docker compose setup

# Landing zone setup

# kafka / redpanda setup

- `bootstrap_server` url kafka is listening on for events
- message serialization
- `topic-name` roughly is equivalent to a table name in Kafka … or not
  really. NO schema constraints.

# Flink job setup

- `offset['earliest', 'latest', timestamp]`
- `table_name` does only exist in Flink
