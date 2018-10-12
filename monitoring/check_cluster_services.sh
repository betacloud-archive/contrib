#!/usr/bin/env bash

if [[ $# -lt 1 ]]; then

    echo usage: $0 CONFIGURATION
    exit 1

fi

configuration=$1
shift

if [[ ! -e $configuration ]]; then

    echo configuration file $configuration does not exist
    exit 1

else

    source $configuration

fi

cd $(dirname $configuration)

if [[ ! -e check_elasticsearch ]]; then
    wget -O check_elasticsearch https://raw.githubusercontent.com/orthecreedence/check_elasticsearch/master/check_elasticsearch
fi

if [[ ! -e check_galera_cluster ]]; then
    wget -O check_galera_cluster https://raw.githubusercontent.com/fridim/nagios-plugin-check_galera_cluster/master/check_galera_cluster
fi

if [[ ! -e check_rabbitmq_cluster ]]; then
    wget -O check_rabbitmq_cluster https://raw.githubusercontent.com/nagios-plugins-rabbitmq/nagios-plugins-rabbitmq/master/scripts/check_rabbitmq_cluster
fi

echo Elasticsearch
echo
bash check_elasticsearch -H $ADDRESS

echo
echo MariaDB
echo
bash check_galera_cluster -u prometheus -p $PASSWORD_MARIADB -H $ADDRESS

echo
echo RabbitMQ
echo
perl check_rabbitmq_cluster -H $ADDRESS -u openstack -p $PASSWORD_RABBITMQ
