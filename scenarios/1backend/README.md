# Run benchmark

```
docker-compose up -d

# Seed database with sample data

docker-compose exec sysbench sysbench \
  --db-driver=mysql\
  --oltp-table-size=100000 \
  --oltp-tables-count=24 \
  --threads=4 \
  --mysql-host=db1 \
  --mysql-port=3306 \
  --mysql-user=sbtest1 \
  --mysql-password=password \
  --mysql-db=sbtest \
  /usr/share/sysbench/tests/include/oltp_legacy/parallel_prepare.lua \
  run

# Run benchmark

docker-compose exec sysbench sysbench \
  --db-driver=mysql \
  --threads=4 \
  --tables=24 \
  --table-size=100000 \
  --report-interval=5 \
  --rand-type=pareto \
  --forced-shutdown=1 \
  --time=300 \
  --events=0 \
  --percentile=95 \
  --mysql=user=sbtest1 \
  --mysql-password=password \
  --mysql-db=sbtest \
  --mysql-storage-engine=INNODB \
  --mysql-host=db1 \
  --mysql-port=3306 \
  --point-select=25 \
  --range_size=5 \
  --skip_trx=on \
  run
```
