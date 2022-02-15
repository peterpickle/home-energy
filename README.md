# home-energy

## Setup

### Redis database

1. Install redis
2. Install redis time series
3. Create rules
   - For Redis time series, rules need to be created.
     Execute each rule in the redis-cli beofr starting one of the input scripts.

#### Commands

Elektricity

Per second, keep 1 week.
Per minute, keep 6 months.
Per 15 minutes, keep forever.

```
TS.CREATE electricity_down_sec RETENTION 604800000 DUPLICATE_POLICY SUM LABELS dir down granularity 1s

TS.CREATE electricity_down_1min RETENTION 15768000000 LABELS dir down granularity 1m
TS.CREATERULE electricity_down_sec electricity_down_1min AGGREGATION avg 60000

TS.CREATE electricity_down_15min LABELS dir down granularity 15m
TS.CREATERULE electricity_down_sec electricity_down_15min AGGREGATION avg 900000

TS.CREATE electricity_down_1h LABELS dir down granularity 1h
TS.CREATERULE electricity_down_sec electricity_down_1h AGGREGATION avg 3600000


TS.CREATE electricity_up_sec RETENTION 604800000 DUPLICATE_POLICY SUM LABELS dir up granularity 1s

TS.CREATE electricity_up_1min RETENTION 15768000000 LABELS dir up granularity 1m
TS.CREATERULE electricity_up_sec electricity_up_1min AGGREGATION avg 60000

TS.CREATE electricity_up_15min LABELS dir up granularity 15m
TS.CREATERULE electricity_up_sec electricity_up_15min AGGREGATION avg 900000

TS.CREATE electricity_up_1h LABELS dir up granularity 1h
TS.CREATERULE electricity_up_sec electricity_up_1h AGGREGATION avg 3600000
```

Production

Per minute, keep 6 months.
Per 15 minutes, keep forever.

```
TS.CREATE electricity_prod_1min RETENTION 15768000000 DUPLICATE_POLICY MAX LABELS type prod granularity 1m

TS.CREATE electricity_prod_15min LABELS type prod granularity 15m
TS.CREATERULE electricity_prod_1min electricity_prod_15min AGGREGATION avg 900000
```

Production daily

Per minute, keep 2 days.
Per day, keep forever.

```
TS.CREATE electricity_prod_gen_daily_1min RETENTION 172800000 DUPLICATE_POLICY MAX LABELS type prod value dayGen

TS.CREATE electricity_prod_gen_daily_1day LABELS type prod value dayGen granularity 1d
TS.CREATERULE electricity_prod_gen_daily_1min electricity_prod_gen_daily_1day AGGREGATION max 86400000
```

Gas

Per 5 minutes, keep 6 months.
Per 15 minutes, keep forever.

```
TS.CREATE gas_5min RETENTION 15768000000 DUPLICATE_POLICY SUM LABELS type gas granularity 5m

TS.CREATE gas_15min LABELS type gas granularity 15m
TS.CREATERULE gas_5min gas_15min AGGREGATION sum 900000
```

## Launch the application

1. start the redis-server
```
cd input
redis-server redis.conf
```

The redis-server can be started from anywhere. Just make sure to use the redis.conf file provided.
The location of the redis time series might need adjustment.
This will create a file dump.rdb. This is your database. If you remove it, your data will be lost.

2. start p1-reader

3. start production reader

4. start the GUI
   - deploy the directory'web' with django

