#!/bin/sh

INFLUXDB_ADMIN_TOKEN=`uuidgen| sha256sum | tail -c 32 | awk '{print $1}'`
INFLUXDB_TOKEN=`uuidgen| sha256sum | tail -c 32 | awk '{print $1}'`
GRAFANA_ADMIN_PASS=`uuidgen| sha256sum | tail -c 32 | awk '{print $1}'`

sed -E -i "s/\"GF_SECURITY_ADMIN_PASSWORD=\S+\"/\"GF_SECURITY_ADMIN_PASSWORD=$GRAFANA_ADMIN_PASS\"/g" docker-compose.yml
sed -E -i "s/token: \S+/token: $INFLUXDB_ADMIN_TOKEN/g" grafana/provisioning/datasources/influxdb.yml
sed -E -i "s/DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=\S+/DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=$INFLUXDB_ADMIN_TOKEN/g" .env
sed -E -i "s/DOCKER_INFLUXDB_INIT_PASSWORD=\S+/DOCKER_INFLUXDB_INIT_PASSWORD=$INFLUXDB_TOKEN/g" .env
