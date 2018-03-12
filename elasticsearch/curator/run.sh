#!/usr/bin/env bash

if [[ $# -lt 1 ]]; then
    echo usage: $0 actions/ACTION.yml
    exit 1
fi

if [[ ! -e $1 ]]; then
    echo "action file $1 does not exist"
    exit 1
fi

docker run \
    --rm \
    -e LC_ALL=C.UTF-8 \
    -e LANG=C.UTF-8 \
    -v $(pwd)/configuration:/usr/share/elasticsearch/.curator:ro \
    -v $(pwd)/actions:/usr/share/elasticsearch/actions \
    -t osism/elasticsearch:ocata-latest \
    /usr/bin/curator /usr/share/elasticsearch/$1
