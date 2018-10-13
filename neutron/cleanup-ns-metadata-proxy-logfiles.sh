#!/usr/bin/env bash

tmpfile=$(mktemp)

pgrep -af "haproxy -f /var/lib/neutron/ns-metadata-proxy"| while read process; do
    tmp=${process##*/}
    uuid=${tmp%.conf}
    echo $uuid >> $tmpfile
done

docker exec -t neutron_openvswitch_agent ls -1 /var/log/kolla/neutron/ | grep ns-metadata-proxy | while read logfile; do
    tmp=${logfile#*neutron-ns-metadata-proxy-}
    uuid=${tmp%.log*}

    if ! grep -Fxq "$uuid" $tmpfile; then
        docker exec -t neutron_openvswitch_agent rm /var/log/kolla/neutron/neutron-ns-metadata-proxy-$uuid.log
    fi
done

rm $tmpfile
