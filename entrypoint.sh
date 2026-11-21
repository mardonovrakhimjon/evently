#!/bin/sh
set -e

# Wait for database if postgres is used
if [ "$USE_SQLITE" != "True" ] && [ "$USE_SQLITE" != "true" ] && [ "$USE_SQLITE" != "1" ]; then
    echo "PostgreSQL bazasiga ulanish tekshirilmoqda (${DB_HOST:-db}:${DB_PORT:-5432})..."
    python - <<'END'
import os, sys, time, socket

host = os.getenv("DB_HOST", "db")
port = int(os.getenv("DB_PORT", "5432"))

start_time = time.time()
while True:
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f"PostgreSQL ({host}:{port}) ga muvaffaqiyatli ulandi!")
            break
    except OSError:
        if time.time() - start_time > 60:
            print("PostgreSQL ga ulanishda timeout yuz berdi!", file=sys.stderr)
            sys.exit(1)
        print(f"Baza hali tayyor emas ({host}:{port}), 1 soniya kutilmoqda...")
        time.sleep(1)
END
fi

# Run migrations
echo "Migratsiyalar qo'llanilmoqda..."
python manage.py migrate --noinput

# Collect static files
echo "Statik fayllar to'planmoqda..."
python manage.py collectstatic --noinput || true

echo "Tayyorgarlik yakunlandi. Asosiy jarayon ishga tushirilmoqda: $@"
exec "$@"
