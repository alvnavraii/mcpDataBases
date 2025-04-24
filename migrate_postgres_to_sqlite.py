import psycopg2
import sqlite3
from psycopg2 import sql

# Configuración de conexión PostgreSQL
db_pg = {
    'dbname': 'ecommerce',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': 5433
}

# Ruta de la base de datos SQLite
db_sqlite = '/home/slendy/MCPProjects/DataBase/ecommerce.db'

def get_pg_tables(cur):
    cur.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type='BASE TABLE';
    """)
    return [row[0] for row in cur.fetchall()]

def get_pg_columns(cur, table):
    cur.execute(sql.SQL("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns WHERE table_name = %s
        ORDER BY ordinal_position;
    """), [table])
    return cur.fetchall()

def pg_type_to_sqlite(pg_type):
    mapping = {
        'integer': 'INTEGER',
        'bigint': 'INTEGER',
        'smallint': 'INTEGER',
        'boolean': 'BOOLEAN',
        'character varying': 'TEXT',
        'text': 'TEXT',
        'timestamp without time zone': 'TEXT',
        'timestamp with time zone': 'TEXT',
        'date': 'TEXT',
        'numeric': 'REAL',
        'double precision': 'REAL',
        'real': 'REAL',
        'bytea': 'BLOB',
    }
    return mapping.get(pg_type, 'TEXT')

def create_sqlite_table(sqlite_cur, table, columns):
    col_defs = []
    for col_name, col_type, is_nullable, col_default in columns:
        col_def = f'"{col_name}" {pg_type_to_sqlite(col_type)}'
        if is_nullable == 'NO':
            col_def += ' NOT NULL'
        # No se añaden defaults ni autoincrement aquí por compatibilidad
        col_defs.append(col_def)
    stmt = f'CREATE TABLE IF NOT EXISTS "{table}" ({", ".join(col_defs)});'
    sqlite_cur.execute(stmt)

def copy_table_data(pg_cur, sqlite_cur, table, columns):
    col_names = [col[0] for col in columns]
    pg_cur.execute(sql.SQL('SELECT * FROM {}').format(sql.Identifier(table)))
    rows = pg_cur.fetchall()
    if not rows:
        return
    placeholders = ','.join(['?'] * len(col_names))
    insert_stmt = f'INSERT INTO "{table}" ({", ".join(col_names)}) VALUES ({placeholders})'
    sqlite_cur.executemany(insert_stmt, rows)

def main():
    pg_conn = psycopg2.connect(**db_pg)
    sqlite_conn = sqlite3.connect(db_sqlite)
    pg_cur = pg_conn.cursor()
    sqlite_cur = sqlite_conn.cursor()

    tables = get_pg_tables(pg_cur)
    for table in tables:
        print(f'Migrando tabla: {table}')
        columns = get_pg_columns(pg_cur, table)
        create_sqlite_table(sqlite_cur, table, columns)
        copy_table_data(pg_cur, sqlite_cur, table, columns)
        sqlite_conn.commit()

    pg_cur.close()
    pg_conn.close()
    sqlite_cur.close()
    sqlite_conn.close()
    print('Migración completada.')

if __name__ == '__main__':
    main()
