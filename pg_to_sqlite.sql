-- Script para extraer estructura y datos de PostgreSQL para SQLite
-- Generado: 2025-04-23

-- Obtener lista de tablas
\echo 'Extrayendo estructura de tablas...'
\o table_list.txt
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' ORDER BY table_name;
\o

-- Función para generar scripts de creación de tablas en formato SQLite
CREATE OR REPLACE FUNCTION generate_sqlite_schema() RETURNS TEXT AS $$
DECLARE
    tabla RECORD;
    columna RECORD;
    fk RECORD;
    pk RECORD;
    resultado TEXT := '';
    campos TEXT;
    tabla_name TEXT;
    primary_keys TEXT;
    foreign_keys TEXT;
BEGIN
    FOR tabla IN SELECT table_name FROM information_schema.tables 
                 WHERE table_schema = 'public' AND table_type = 'BASE TABLE' 
                 ORDER BY table_name
    LOOP
        tabla_name := tabla.table_name;
        resultado := resultado || '-- Tabla: ' || tabla_name || E'\n';
        resultado := resultado || 'CREATE TABLE ' || tabla_name || ' (' || E'\n';
        
        -- Obtener definición de columnas
        campos := '';
        FOR columna IN SELECT column_name, data_type, is_nullable, column_default
                       FROM information_schema.columns
                       WHERE table_schema = 'public' AND table_name = tabla_name
                       ORDER BY ordinal_position
        LOOP
            campos := campos || '  ' || columna.column_name || ' ';
            
            -- Convertir tipo de dato PostgreSQL a SQLite
            CASE
                WHEN columna.data_type LIKE 'character%' OR columna.data_type = 'text' THEN
                    campos := campos || 'TEXT';
                WHEN columna.data_type IN ('integer', 'smallint', 'bigint') THEN
                    campos := campos || 'INTEGER';
                WHEN columna.data_type IN ('numeric', 'real', 'double precision') THEN
                    campos := campos || 'REAL';
                WHEN columna.data_type = 'boolean' THEN
                    campos := campos || 'INTEGER'; -- 0 o 1 en SQLite
                WHEN columna.data_type LIKE 'timestamp%' OR columna.data_type = 'date' THEN
                    campos := campos || 'TIMESTAMP';
                ELSE
                    campos := campos || 'TEXT'; -- Tipo por defecto
            END CASE;
            
            -- NULL o NOT NULL
            IF columna.is_nullable = 'NO' THEN
                campos := campos || ' NOT NULL';
            END IF;
            
            -- Valores por defecto (excepto secuencias/autoincrement)
            IF columna.column_default IS NOT NULL AND columna.column_default NOT LIKE 'nextval%' THEN
                -- Convertir valores booleanos
                IF columna.column_default = 'true' THEN
                    campos := campos || ' DEFAULT 1';
                ELSIF columna.column_default = 'false' THEN
                    campos := campos || ' DEFAULT 0';
                ELSE
                    campos := campos || ' DEFAULT ' || columna.column_default;
                END IF;
            END IF;
            
            campos := campos || ',' || E'\n';
        END LOOP;
        
        -- Agregar claves primarias
        primary_keys := '';
        FOR pk IN SELECT a.attname as column_name
                  FROM pg_index i
                  JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                  WHERE i.indrelid = (SELECT oid FROM pg_class WHERE relname = tabla_name)
                  AND i.indisprimary
        LOOP
            IF primary_keys = '' THEN
                primary_keys := pk.column_name;
            ELSE
                primary_keys := primary_keys || ', ' || pk.column_name;
            END IF;
        END LOOP;
        
        IF primary_keys <> '' THEN
            campos := campos || '  PRIMARY KEY (' || primary_keys || '),' || E'\n';
        END IF;
        
        -- Agregar foreign keys
        foreign_keys := '';
        FOR fk IN SELECT
                     kcu.column_name,
                     ccu.table_name AS referenced_table,
                     ccu.column_name AS referenced_column
                  FROM information_schema.table_constraints tc
                  JOIN information_schema.key_column_usage kcu
                     ON tc.constraint_name = kcu.constraint_name
                  JOIN information_schema.constraint_column_usage ccu
                     ON ccu.constraint_name = tc.constraint_name
                  WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_name = tabla_name
                  AND tc.table_schema = 'public'
        LOOP
            foreign_keys := foreign_keys || '  FOREIGN KEY (' || fk.column_name || ') REFERENCES ';
            foreign_keys := foreign_keys || fk.referenced_table || '(' || fk.referenced_column || '),' || E'\n';
        END LOOP;
        
        -- Agregar foreign keys si existen
        IF foreign_keys <> '' THEN
            campos := campos || foreign_keys;
        END IF;
        
        -- Eliminar la última coma
        campos := rtrim(campos, E',\n');
        
        resultado := resultado || campos || E'\n' || ');' || E'\n\n';
    END LOOP;
    
    RETURN resultado;
END;
$$ LANGUAGE plpgsql;

-- Generar script para extraer datos
CREATE OR REPLACE FUNCTION generate_sqlite_data() RETURNS TEXT AS $$
DECLARE
    tabla RECORD;
    resultado TEXT := '';
    sql TEXT;
    datos TEXT;
BEGIN
    FOR tabla IN SELECT table_name FROM information_schema.tables 
                 WHERE table_schema = 'public' AND table_type = 'BASE TABLE' 
                 ORDER BY table_name
    LOOP
        resultado := resultado || '-- Datos para tabla: ' || tabla.table_name || E'\n';
        resultado := resultado || '\echo ''Extrayendo datos de ' || tabla.table_name || '...''' || E'\n';
        resultado := resultado || '\o ' || tabla.table_name || '_data.sql' || E'\n';
        
        -- Crear sentencia para obtener datos en formato de inserts SQLite
        sql := 'SELECT ''INSERT INTO ' || tabla.table_name || ' ('' || ';
        
        -- Obtener nombres de columnas
        sql := sql || 'string_agg(column_name, '', '') || ';
        
        -- Cerrar paréntesis y agregar VALUES
        sql := sql || ''') VALUES ('' || ';
        
        -- Construir la lista de valores
        sql := sql || 'string_agg(';
        sql := sql || '  CASE ';
        sql := sql || '    WHEN column_default LIKE ''%::boolean'' OR data_type = ''boolean'' THEN ';
        sql := sql || '      CASE WHEN is_nullable = ''YES'' AND column_name IS NULL THEN ''NULL'' ';
        sql := sql || '           WHEN column_name::text = ''t'' THEN ''1'' ';
        sql := sql || '           WHEN column_name::text = ''f'' THEN ''0'' ';
        sql := sql || '           ELSE column_name::text END ';
        sql := sql || '    ELSE ';
        sql := sql || '      CASE WHEN is_nullable = ''YES'' AND column_name IS NULL THEN ''NULL'' ';
        sql := sql || '           WHEN data_type IN (''character varying'', ''text'', ''date'', ''timestamp without time zone'') ';
        sql := sql || '               THEN '''''''' || replace(column_name::text, '''''''', '''''''''''') || '''''''' ';
        sql := sql || '           ELSE column_name::text END ';
        sql := sql || '  END, '', '') || ';
        
        -- Cerrar paréntesis y terminar sentencia
        sql := sql || ''');'' ';
        
        -- FROM y GROUP BY
        sql := sql || 'FROM (';
        sql := sql || '  SELECT c.column_name, c.data_type, c.is_nullable, c.column_default, ';
        sql := sql || '         row_number() OVER() as rn ';
        sql := sql || '  FROM information_schema.columns c ';
        sql := sql || '  WHERE c.table_schema = ''public'' AND c.table_name = ''' || tabla.table_name || ''' ';
        sql := sql || '  ORDER BY c.ordinal_position';
        sql := sql || ') cols ';
        sql := sql || 'GROUP BY rn;';
        
        -- Ejecutar la consulta y almacenar el resultado
        EXECUTE sql INTO datos;
        
        -- Agregar el resultado al script final
        resultado := resultado || datos || E'\n\o\n\n';
    END LOOP;
    
    RETURN resultado;
END;
$$ LANGUAGE plpgsql;

-- Exportar esquema y datos
\echo 'Generando script para estructura SQLite...'
\o sqlite_schema.sql
SELECT generate_sqlite_schema();
\o

\echo 'Generando script para extracción de datos...'
\o extract_data.sql
SELECT generate_sqlite_data();
\o

-- Ejecutar el script de extracción de datos
\echo 'Extrayendo datos...'
\i extract_data.sql

-- Generar script para creación de índices
\echo 'Generando script para índices...'
\o sqlite_indexes.sql
SELECT 
  'CREATE ' || 
  CASE WHEN i.indisunique THEN 'UNIQUE ' ELSE '' END ||
  'INDEX idx_' || t.relname || '_' || string_agg(a.attname, '_') || 
  ' ON ' || t.relname || 
  ' (' || string_agg(a.attname, ', ') || ');'
FROM 
  pg_index i
JOIN 
  pg_class t ON t.oid = i.indrelid
JOIN 
  pg_class ix ON ix.oid = i.indexrelid
JOIN 
  pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(i.indkey)
JOIN 
  pg_namespace n ON n.oid = t.relnamespace
WHERE 
  t.relkind = 'r' AND 
  n.nspname = 'public' AND
  NOT i.indisprimary  -- Excluir claves primarias que ya están en el schema
GROUP BY 
  i.indisunique, t.relname, i.indexrelid
ORDER BY 
  t.relname, i.indexrelid;
\o

-- Instrucciones para combinar los archivos
\echo 'INSTRUCCIONES PARA CREAR LA BASE DE DATOS SQLITE:'
\echo '1. Combine los archivos en este orden:'
\echo '   - sqlite_schema.sql (estructura de tablas)'
\echo '   - *_data.sql (archivos de datos)'
\echo '   - sqlite_indexes.sql (índices)'
\echo '2. Use este comando para crear la base de datos SQLite:'
\echo '   sqlite3 ecommerce.sqlite < combined_script.sql'
