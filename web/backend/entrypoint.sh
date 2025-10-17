#!/bin/sh
# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until pg_isready -h ${POSTGRES_HOST:-localhost} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-agent_user} > /dev/null 2>&1; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "✅ PostgreSQL is ready!"

# Wait an additional moment for Qdrant
echo "⏳ Waiting for Qdrant..."
sleep 3

echo "🚀 Starting backend server..."
exec "$@"
