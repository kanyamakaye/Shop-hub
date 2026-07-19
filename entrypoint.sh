#!/bin/sh
set -e

if [ -n "$POSTGRES_HOST" ]; then
    echo "Waiting for database at $POSTGRES_HOST:${POSTGRES_PORT:-5432}..."
    until python -c "
import socket, sys, os
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(1)
try:
    s.connect((os.environ['POSTGRES_HOST'], int(os.environ.get('POSTGRES_PORT', 5432))))
except OSError:
    sys.exit(1)
"; do
        sleep 1
    done
    echo "Database is up."
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
