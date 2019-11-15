#!/usr/bin/env bash

echo "$@"

echo "Running supervisord in background"
/usr/bin/supervisord -c /etc/supervisor/supervisord.conf &

echo "Waiting for xvfb"
sleep 10

echo "Prepare setup"

qgis_setup.sh inasafe


echo "QGIS container started up"
exec "$@"