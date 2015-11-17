#!/bin/bash

cd /

while :
do
    echo "Executing agent..."
    python -m zmon_agent -e $(cat /etc/entity_service_url)
    echo "sleeping..."
    sleep 60
done
