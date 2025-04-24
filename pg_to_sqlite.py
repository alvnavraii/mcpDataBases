#!/usr/bin/env python3
"""
Script para migrar una base de datos PostgreSQL a SQLite

Este script extrae:
- Estructura de tablas
- Datos
- Índices
- Restricciones

Y genera una base de datos SQLite compatible.
"""

import os
import sys
import argparse
import sqlite3
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

def parse_args():
    """Configurar argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(description='Migrar base de datos PostgreSQL a SQLite')
    
    parser.add_argument('--pg-host', default=os.getenv('PG_HOST', 'localhost'),
                        help='Host PostgreSQL (predeterminado: localhost)')
    parser.add_argument('--pg-port', default=os.getenv('PG_PORT', '5433'),
                        help='Puerto PostgreSQL (predeterminado: 5433)')
    parser.add_argument('--pg-user', default=os.getenv('PG_USER', 'postgres'),
                        help='Usuario PostgreSQL (predeterminado: postgres)')
    parser.add_argument('--pg-password', default=os.getenv('PG_PASSWORD', 'postgres'),
                        help='Contraseña PostgreSQL (predeterminado: postgres)')
    parser.add_argument('--pg-db', default=os.getenv('PG_DATABASE', 'ecommerce'),
                        help='Nombre de la base de datos PostgreSQL (predeterminado: ecommerce)')
    parser.add_argument('--sqlite-file', default='ecommerce.sqlite',
                        help='Archivo de base de datos SQLite de salida (predeterminado: ecommerce.sqlite)')
    
    return parser.parse_args()

def pg_connect(host, port, user, password, dbname):
    """Conectar a PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=dbname
        )
        return conn
    except Exception as e:
        print(f"Error al conectar a PostgreSQL: {e}")
        sys.exit(1)

def sqlite_connect(db_file):
    """Conectar a SQLite"""
    try:
        # Eliminar el archivo si ya existe
        if os.path.exists(db_file):
            os.remove(db_file)
        
        conn = sqlite3.connect(db_file)
        conn.execute("PRAGMA foreign_keys = OFF;")
        return conn
    except Exception as e:
        print(f"Error al conectar a SQLite: {e}")
        sys.exit(1)

def get_tables(pg_conn):
    """Obtener lista de tablas en PostgreSQL"""
    cursor = pg_conn.cursor()
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return tables

def get_columns(pg_conn, table):
    """Obtener estructura de columnas de una tabla"""
    cursor = pg_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("""
        SELECT 
            column_name, 
            data_type, 
            is_nullable, 
            column_default
        FROM 
            information_schema.columns
        WHERE 
            table_schema = 'public'
            AND table_name = %s
        ORDER BY 
            ordinal_position;
    """, (table,))
    columns = cursor.fetchall()
    cursor.close()
    return columns

def get_primary_keys(pg_conn, table):
    """Obtener claves primarias de una tabla"""
    cursor = pg_conn.cursor()
    cursor.execute("""
        SELECT
            a.attname as column_name
        FROM
            pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
        WHERE
            i.indrelid = %s::regclass
            AND i.indisprimary;
    """, (table,))
    pks = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return pks

def get_foreign_keys(pg_conn, table):
    """Obtener claves foráneas de una tabla"""
    cursor = pg_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("""
        SELECT
            kcu.column_name,
            ccu.table_name AS referenced_table,
            ccu.column_name AS referenced_column
        FROM
            information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
        WHERE
            tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name = %s
            AND tc.table_schema = 'public';
    """, (table,))
    fks = cursor.fetchall()
    cursor.close()
    return fks

def get_indexes(pg_conn, table):
    """Obtener índices de una tabla (excluyendo PK)"""
    cursor = pg_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("""
        SELECT
            i.relname AS index_name,
            array_agg(a.attname) AS column_names,
            ix.indisunique AS is_unique
        FROM
            pg_index ix
            JOIN pg_class i ON i.oid = ix.indexrelid
            JOIN pg_class t ON t.oid = ix.indrelid
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
        WHERE
            t.relkind = 'r'
            AND t.relname = %s
            AND NOT ix.indisprimary
        GROUP BY
            i.relname,
            ix.indisunique;
    """, (table,))
    indexes = cursor.fetchall()
    cursor.close()
    return indexes

def pg_to_sqlite_type(pg_type):
    """Convertir tipo de dato PostgreSQL a SQLite"""
    type_mapping = {
        'bigint': 'INTEGER',
        'bigserial': 'INTEGER',
        'boolean': 'INTEGER',
        'character varying': 'TEXT',
        'character': 'TEXT',
        'date': 'TEXT',
        'double precision': 'REAL',
        'integer': 'INTEGER',
        'numeric': 'REAL',
        'real': 'REAL',
        'smallint': 'INTEGER',
        'serial': 'INTEGER',
        'text': 'TEXT',
        'timestamp with time zone': 'TIMESTAMP',
        'timestamp without time zone': 'TIMESTAMP',
        'uuid': 'TEXT',
        'jsonb': 'TEXT',
        'json': 'TEXT'
    }
    
    for pg, sqlite in type_mapping.items():
        if pg_type.startswith(pg):
            return sqlite
    
    return 'TEXT'  # Tipo por defecto

def format_value(value, data_type):
    """Formatear valor para SQLite"""
    if value is None:
        return None
    
    # Convertir booleanos
    if data_type == 'boolean':
        return 1 if value in ('t', True) else 0
    
    # Para tipos de texto, devolver tal cual
    return value

def create_table(sqlite_conn, table, columns, pks, fks):
    """Crear tabla en SQLite"""
    column_defs = []
    
    for col in columns:
        sql_type = pg_to_sqlite_type(col['data_type'])
        nullable = "" if col['is_nullable'] == 'YES' else " NOT NULL"
        
        # Comprobar si tiene un valor por defecto
        default = ""
        if col['column_default'] is not None and not col['column_default'].startswith('nextval'):
            if col['data_type'] == 'boolean':
                # Convertir booleanos
                if col['column_default'] == 'true':
                    default = " DEFAULT 1"
                elif col['column_default'] == 'false':
                    default = " DEFAULT 0"
            else:
                default = f" DEFAULT {col['column_default']}"
        
        column_defs.append(f"{col['column_name']} {sql_type}{nullable}{default}")
    
    # Agregar clave primaria
    if pks:
        column_defs.append(f"PRIMARY KEY ({', '.join(pks)})")
    
    # Agregar claves foráneas
    for fk in fks:
        column_defs.append(
            f"FOREIGN KEY ({fk['column_name']}) REFERENCES {fk['referenced_table']}({fk['referenced_column']})"
        )
    
    # Crear la tabla
    sql = f"CREATE TABLE {table} (\n  " + ",\n  ".join(column_defs) + "\n);"
    sqlite_conn.execute(sql)

def create_indexes(sqlite_conn, table, indexes):
    """Crear índices en SQLite"""
    for idx in indexes:
        unique = "UNIQUE " if idx['is_unique'] else ""
        columns = ", ".join(idx['column_names'])
        sql = f"CREATE {unique}INDEX idx_{table}_{('_'.join(idx['column_names']))} ON {table} ({columns});"
        sqlite_conn.execute(sql)

def copy_data(pg_conn, sqlite_conn, table, columns):
    """Copiar datos de PostgreSQL a SQLite"""
    # Obtener nombres de columnas
    column_names = [col['column_name'] for col in columns]
    
    # Consulta para obtener datos
    pg_cursor = pg_conn.cursor()
    pg_cursor.execute(f"SELECT {', '.join(column_names)} FROM {table};")
    
    # Preparar inserción en SQLite
    placeholders = ", ".join(["?"] * len(column_names))
    insert_sql = f"INSERT INTO {table} ({', '.join(column_names)}) VALUES ({placeholders});"
    
    # Procesar lotes de datos
    batch_size = 1000
    batch = []
    
    # Para cada fila de datos
    for row in pg_cursor:
        # Formatear los valores según el tipo de dato
        formatted_row = []
        for i, value in enumerate(row):
            formatted_row.append(format_value(value, columns[i]['data_type']))
        
        batch.append(formatted_row)
        
        # Insertar en lotes para mayor eficiencia
        if len(batch) >= batch_size:
            sqlite_conn.executemany(insert_sql, batch)
            batch = []
    
    # Insertar cualquier lote restante
    if batch:
        sqlite_conn.executemany(insert_sql, batch)
    
    pg_cursor.close()

def main():
    """Función principal"""
    # Cargar variables de entorno
    load_dotenv()
    
    # Obtener argumentos
    args = parse_args()
    
    print(f"Migrando base de datos PostgreSQL '{args.pg_db}' a SQLite '{args.sqlite_file}'...")
    
    # Conectar a PostgreSQL
    pg_conn = pg_connect(args.pg_host, args.pg_port, args.pg_user, args.pg_password, args.pg_db)
    
    # Conectar a SQLite
    sqlite_conn = sqlite_connect(args.sqlite_file)
    
    # Iniciar transacción en SQLite
    sqlite_conn.execute("BEGIN TRANSACTION;")
    
    try:
        # Obtener lista de tablas
        tables = get_tables(pg_conn)
        print(f"Encontradas {len(tables)} tablas para migrar")
        
        # Procesar cada tabla
        for table in tables:
            print(f"Procesando tabla: {table}")
            
            # Obtener estructura
            columns = get_columns(pg_conn, table)
            pks = get_primary_keys(pg_conn, table)
            fks = get_foreign_keys(pg_conn, table)
            indexes = get_indexes(pg_conn, table)
            
            # Crear tabla en SQLite
            create_table(sqlite_conn, table, columns, pks, fks)
            
            # Copiar datos
            print(f"  Copiando datos...")
            copy_data(pg_conn, sqlite_conn, table, columns)
            
            # Crear índices
            for idx in indexes:
                print(f"  Creando índice: {idx['index_name']}")
                create_indexes(sqlite_conn, table, [idx])
        
        # Confirmar transacción
        sqlite_conn.execute("COMMIT;")
        sqlite_conn.execute("PRAGMA foreign_keys = ON;")
        print(f"Migración completada correctamente")
        
        # Verificación final
        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"La base de datos SQLite contiene {len(tables)} tablas:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]};")
            count = cursor.fetchone()[0]
            print(f"  - {table[0]}: {count} registros")
    
    except Exception as e:
        # Revertir en caso de error
        sqlite_conn.execute("ROLLBACK;")
        print(f"Error durante la migración: {e}")
        sys.exit(1)
    
    finally:
        # Cerrar conexiones
        pg_conn.close()
        sqlite_conn.close()

if __name__ == "__main__":
    main()
