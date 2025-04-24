#!/bin/bash

# Script para migrar PostgreSQL a SQLite
# Creado: 2025-04-23

# Variables de configuración
PG_USER="postgres"
PG_HOST="localhost"
PG_PORT="5433"
PG_DATABASE="ecommerce"
PG_PASSWORD="postgres"
OUTPUT_DIR="./sqlite_migration"
SQLITE_DB="ecommerce.sqlite"

# Asegúrate de que las variables estén configuradas correctamente
# Si tienes un archivo .env, puedes usar:
# source .env

echo "=== Migración de PostgreSQL a SQLite ==="
echo "Base de datos PostgreSQL: $PG_DATABASE"
echo "Archivo SQLite destino: $SQLITE_DB"

# Crear directorio para archivos temporales
mkdir -p "$OUTPUT_DIR"
cd "$OUTPUT_DIR"

# Exportar esquema usando psql
echo "Paso 1: Extrayendo esquema de PostgreSQL..."
PGPASSWORD="$PG_PASSWORD" psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DATABASE" -f "../pg_to_sqlite.sql"

# Combinar archivos en un solo script SQL
echo "Paso 2: Combinando archivos para SQLite..."
cat sqlite_schema.sql > combined_script.sql
for data_file in *_data.sql; do
  if [ -f "$data_file" ]; then
    cat "$data_file" >> combined_script.sql
  fi
done
cat sqlite_indexes.sql >> combined_script.sql

# Añadir comando PRAGMA para mejorar rendimiento
sed -i '1s/^/PRAGMA foreign_keys = OFF;\nBEGIN TRANSACTION;\n\n/' combined_script.sql
echo -e "\nCOMMIT;\nPRAGMA foreign_keys = ON;" >> combined_script.sql

# Crear base de datos SQLite
echo "Paso 3: Creando base de datos SQLite..."
sqlite3 "$SQLITE_DB" < combined_script.sql

# Verificar la creación exitosa
if [ -f "$SQLITE_DB" ]; then
  echo "Migración exitosa. Base de datos SQLite creada en: $OUTPUT_DIR/$SQLITE_DB"
  echo "Puedes explorarla con: sqlite3 $OUTPUT_DIR/$SQLITE_DB"
  
  # Lista de tablas migradas
  echo "Tablas migradas:"
  sqlite3 "$SQLITE_DB" ".tables"
  
  # Estadísticas
  echo "Estadísticas:"
  tables=$(sqlite3 "$SQLITE_DB" ".tables" | wc -w)
  echo "Total de tablas: $tables"
else
  echo "Error: La migración falló."
fi

echo "Migración completada."
