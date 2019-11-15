#!/usr/bin/env bash

echo "$@"

echo "Running supervisord in background"
/usr/bin/supervisord -c /etc/supervisor/supervisord.conf &

echo "Waiting for xvfb"
sleep 10

echo "Prepare setup"

qgis_setup.sh inasafe
pip3 install -r /tests_directory/REQUIREMENTS.txt
pip3 install -r /tests_directory/REQUIREMENTS_TESTING.txt


echo "QGIS container started up"

# run command
exec "$@"