# DataBase Project (PostgreSQL & SQLite Management)

Este proyecto está diseñado para gestionar y migrar datos entre bases de datos PostgreSQL y SQLite, facilitando la administración y operaciones CRUD para aplicaciones que requieran flexibilidad entre motores de base de datos.

## Estructura principal
- **main.py**: Servidor MCP con herramientas para consultar, insertar, actualizar, eliminar y modificar tablas en la base de datos PostgreSQL.
- **connection.py**: Gestiona la conexión a la base de datos PostgreSQL.
- **migrate_postgres_to_sqlite.py**: Script para migrar todas las tablas y sus datos de PostgreSQL a SQLite.
- **ecommerce.db**: Base de datos SQLite generada a partir de la migración (opcional).

## Funcionalidad
- **Operaciones CRUD**: Crea, lee, actualiza y elimina registros en las tablas de la base de datos PostgreSQL.
- **Gestión de tablas**: Permite crear, alterar y eliminar tablas fácilmente.
- **Migración de datos**: Transfiere la estructura y los datos entre PostgreSQL y SQLite de forma automática.
- **Consultas avanzadas**: Ejecuta consultas SQL personalizadas para análisis o mantenimiento.

## Ejemplos de uso

### 1. Servidor MCP (`main.py`)
- Ejecuta el servidor MCP para exponer herramientas de gestión de la base de datos:
  ```bash
  python3 main.py
  ```
- Herramientas disponibles:
  - `query_db(query)`: Ejecuta consultas SELECT y devuelve resultados.
  - `insert_db(query)`: Ejecuta INSERTS.
  - `update_db(query)`: Ejecuta UPDATES.
  - `delete_db(query)`: Ejecuta DELETES.
  - `create_table(query)`: Ejecuta CREATE TABLE.
  - `alter_table(query)`: Ejecuta ALTER TABLE.
  - `drop_table(query)`: Ejecuta DROP TABLE.

### 2. Migración de datos entre bases de datos
- Ejecuta el script de migración para copiar todas las tablas y datos de PostgreSQL a SQLite:
  ```bash
  python3 migrate_postgres_to_sqlite.py
  ```
- Puedes adaptar el script para migrar datos en ambos sentidos o entre diferentes esquemas.

### 3. Ejemplos de operaciones CRUD
- **Crear un registro:**
  ```sql
  INSERT INTO users (email, password) VALUES ('usuario@dominio.com', 'secreto');
  ```
- **Leer registros:**
  ```sql
  SELECT * FROM products WHERE is_active = TRUE;
  ```
- **Actualizar registros:**
  ```sql
  UPDATE categories SET name = 'Nuevas Tecnologías' WHERE id = 1;
  ```
- **Eliminar registros:**
  ```sql
  DELETE FROM carts WHERE created_at < '2024-01-01';
  ```

## Configuración de MCP (mcp_config.json o claude_desktop_config.json)

Para que las herramientas MCP funcionen correctamente, debes definir cada servicio en tu archivo de configuración (por ejemplo, `~/.codeium/windsurf/mcp_config.json` o `~/.config/Claude/claude_desktop_config.json`). Ejemplo:

```json
{
  "SqliteManagement": {
    "command": "/home/slendy/MCPProjects/DataBase/.venv/bin/python",
    "args": [
      "/home/slendy/MCPProjects/DataBase/main.py",
      "--engine", "sqlite",
      "--url", "sqlite:////home/slendy/MCPProjects/DataBase/ecommerce.db"
    ]
  },
  "PostgressManagement": {
    "command": "/home/slendy/MCPProjects/DataBase/.venv/bin/python",
    "args": [
      "/home/slendy/MCPProjects/DataBase/main.py",
      "--engine", "postgresql",
      "--url", "postgresql://usuario:contraseña@localhost:5432/ecommerce"
    ]
  }
}
```

- Cambia las rutas, credenciales y puertos según tu entorno.
- Por defecto, PostgreSQL utiliza el puerto 5432. Si ya tienes una base de datos en ese puerto, puedes especificar otro (por ejemplo, 5433).
- No incluyas contraseñas reales en el archivo de configuración; reemplaza `usuario` y `contraseña` por los valores adecuados.
- Puedes añadir más servicios para otros motores o bases de datos.
- El nombre del bloque (ej: `SqliteManagement`) será el identificador de la herramienta MCP.

## Dependencias
- Python 3.8+ 
- psycopg2-binary
- sqlite3
- PostgreSQL (servidor y base de datos configurada)

## Notas
- Asegúrate de configurar correctamente los servicios MCP en tu archivo `mcp_config.json` (o `claude_desktop_config.json`) siguiendo el ejemplo anterior.
- Configura también las credenciales de conexión en `connection.py` según tu entorno y base de datos.
- Tras cambios en la estructura de la base de datos, reinicia el servidor MCP para evitar problemas de conexión.
- Puedes adaptar los scripts para migrar o gestionar otros catálogos según tus necesidades.

---

¿Dudas o sugerencias? ¡No dudes en consultar o proponer mejoras! 