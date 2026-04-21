#!/bin/bash
set -e

# Install and start PostgreSQL
apt-get update -qq && apt-get install -y -qq postgresql postgresql-client > /dev/null 2>&1

# Start Postgres
pg_ctlcluster 16 main start

# Set password and configure auth
su - postgres -c "psql -c \"ALTER USER postgres PASSWORD 'postgres';\""
sed -i 's/local\s*all\s*all\s*peer/local all all md5/' /etc/postgresql/16/main/pg_hba.conf
sed -i 's|host\s*all\s*all\s*127.0.0.1/32\s*scram-sha-256|host all all 127.0.0.1/32 md5|' /etc/postgresql/16/main/pg_hba.conf
pg_ctlcluster 16 main reload

# Seed the greetings table
PGPASSWORD=postgres psql -U postgres -h 127.0.0.1 -c "
CREATE TABLE IF NOT EXISTS greetings (
    id SERIAL PRIMARY KEY,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
INSERT INTO greetings (message) VALUES ('Hello from startup!');
"

echo "✓ PostgreSQL is ready"

# Start the app
exec gunicorn --bind 0.0.0.0:8080 app:app
