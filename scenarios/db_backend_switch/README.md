# DB Backend switch

This scenario tests effect of updating destination hostgroup in proxysql
query rules on in flight transactions.

The results are quite positive. It seems that proxysql does not kill
in flight transactions even if the related query rule got updated. Proxysql
will use the DB backend in the new query rule only for new transactions.

```
docker-compose up -d

# Seed database with sample data

sh run.sh
```
