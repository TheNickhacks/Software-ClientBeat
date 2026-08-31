#!/bin/bash
set -e
echo "=== Client Beat entrypoint ==="
echo "Esperando servicios..."
sleep 3
if [ "$#" -eq 0 ]; then
    echo "Iniciando servidor Django en 0.0.0.0:8000"
    exec python manage.py runserver 0.0.0.0:8000
else
    exec "$@"
fi