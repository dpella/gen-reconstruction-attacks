# Distributed System Architecture Stress & Failure
This folder contains the datasets generated as part of the experiments using our algorithm to generate vulnerables datasets.
For this specific case, we set the sensible attribute to be `avg_latency_ms`.

## Datasets
- `distributed_system_100%.csv`: Dataset for Distributed System Architecture with 100% of vulnerables records.

## Vulnerable Queries:
The vulnerable queries used to identify vulnerables records are:
```sql
SELECT AVG(avg_latency_ms) FROM table WHERE architecture_type = 'serverless';
SELECT AVG(avg_latency_ms) FROM table WHERE deployment_type = 'on_cloud';
SELECT AVG(avg_latency_ms) FROM table WHERE communication_type = 'async';
SELECT AVG(avg_latency_ms) FROM table WHERE num_databases = '2';
SELECT AVG(avg_latency_ms) FROM table WHERE num_databases = '3';
SELECT AVG(avg_latency_ms) FROM table WHERE (num_services >= 20 AND num_services < 40);
SELECT AVG(avg_latency_ms) FROM table WHERE ((num_services >= 10 AND num_services < 20) OR (num_services >= 30 AND num_services < 40));
SELECT AVG(avg_latency_ms) FROM table WHERE ((num_services >= 5 AND num_services < 10) OR (num_services >= 15 AND num_services < 20) OR (num_services >= 25 AND num_services < 30) OR (num_services >= 35 AND num_services < 40));
SELECT AVG(avg_latency_ms) FROM table WHERE (request_per_second >= 1000 AND request_per_second < 2000);
SELECT AVG(avg_latency_ms) FROM table WHERE ((request_per_second >= 500 AND request_per_second < 1000) OR (request_per_second >= 1500 AND request_per_second < 2000));
SELECT AVG(avg_latency_ms) FROM table WHERE ((request_per_second >= 250 AND request_per_second < 500) OR (request_per_second >= 750 AND request_per_second < 1000) OR (request_per_second >= 1250 AND request_per_second < 1500) OR (request_per_second >= 1750 AND request_per_second < 2000));
SELECT AVG(avg_latency_ms) FROM table WHERE ((request_per_second >= 125 AND request_per_second < 250) OR (request_per_second >= 375 AND request_per_second < 500) OR (request_per_second >= 625 AND request_per_second < 750) OR (request_per_second >= 875 AND request_per_second < 1000) OR (request_per_second >= 1125 AND request_per_second < 1250) OR (request_per_second >= 1375 AND request_per_second < 1500) OR (request_per_second >= 1625 AND request_per_second < 1750) OR (request_per_second >= 1875 AND request_per_second < 2000));
SELECT AVG(avg_latency_ms) FROM table WHERE (avg_payload >= 50 AND avg_payload < 100);
SELECT AVG(avg_latency_ms) FROM table WHERE ((avg_payload >= 25 AND avg_payload < 50) OR (avg_payload >= 75 AND avg_payload < 100));
SELECT AVG(avg_latency_ms) FROM table WHERE (memory_utilization_percent >= 40 AND memory_utilization_percent < 80);
SELECT AVG(avg_latency_ms) FROM table WHERE ((memory_utilization_percent >= 20 AND memory_utilization_percent < 40) OR (memory_utilization_percent >= 60 AND memory_utilization_percent < 80));
SELECT AVG(avg_latency_ms) FROM table WHERE ((memory_utilization_percent >= 10 AND memory_utilization_percent < 20) OR (memory_utilization_percent >= 30 AND memory_utilization_percent < 40) OR (memory_utilization_percent >= 50 AND memory_utilization_percent < 60) OR (memory_utilization_percent >= 70 AND memory_utilization_percent < 80));
SELECT AVG(avg_latency_ms) FROM table WHERE (cpu_utilization_percent >= 40 AND cpu_utilization_percent < 80);
SELECT AVG(avg_latency_ms) FROM table WHERE ((cpu_utilization_percent >= 20 AND cpu_utilization_percent < 40) OR (cpu_utilization_percent >= 60 AND cpu_utilization_percent < 80));
SELECT AVG(avg_latency_ms) FROM table WHERE ((cpu_utilization_percent >= 10 AND cpu_utilization_percent < 20) OR (cpu_utilization_percent >= 30 AND cpu_utilization_percent < 40) OR (cpu_utilization_percent >= 50 AND cpu_utilization_percent < 60) OR (cpu_utilization_percent >= 70 AND cpu_utilization_percent < 80));
SELECT AVG(avg_latency_ms) FROM table WHERE (network_latency_ms >= 200 AND network_latency_ms < 400);
SELECT AVG(avg_latency_ms) FROM table WHERE ((network_latency_ms >= 100 AND network_latency_ms < 200) OR (network_latency_ms >= 300 AND network_latency_ms < 400));
SELECT AVG(avg_latency_ms) FROM table WHERE ((network_latency_ms >= 50 AND network_latency_ms < 100) OR (network_latency_ms >= 150 AND network_latency_ms < 200) OR (network_latency_ms >= 250 AND network_latency_ms < 300) OR (network_latency_ms >= 350 AND network_latency_ms < 400));
SELECT AVG(avg_latency_ms) FROM table WHERE ((network_latency_ms >= 25 AND network_latency_ms < 50) OR (network_latency_ms >= 75 AND network_latency_ms < 100) OR (network_latency_ms >= 125 AND network_latency_ms < 150) OR (network_latency_ms >= 175 AND network_latency_ms < 200) OR (network_latency_ms >= 225 AND network_latency_ms < 250) OR (network_latency_ms >= 275 AND network_latency_ms < 300) OR (network_latency_ms >= 325 AND network_latency_ms < 350) OR (network_latency_ms >= 375 AND network_latency_ms < 400));
```