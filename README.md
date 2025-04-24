# DataBase Project (PostgreSQL & SQLite Management)

This project is designed to manage and migrate data between PostgreSQL and SQLite databases, making it easier to perform CRUD operations and administration for applications that require flexibility between database engines.

## Main Structure
- **main.py**: MCP server with tools to query, insert, update, delete, and modify tables in the PostgreSQL database.
- **connection.py**: Manages the connection to the PostgreSQL database.
- **migrate_postgres_to_sqlite.py**: Script to migrate all tables and their data from PostgreSQL to SQLite.
- **ecommerce.db**: SQLite database generated from the migration (optional).

## Features
- **CRUD operations**: Create, read, update, and delete records in PostgreSQL database tables.
- **Table management**: Easily create, alter, and drop tables.
- **Data migration**: Automatically transfer structure and data between PostgreSQL and SQLite.
- **Advanced queries**: Run custom SQL queries for analysis or maintenance.

## Usage Examples

### 1. MCP Server (`main.py`)
- Run the MCP server to expose database management tools:
  ```bash
  python3 main.py
  ```
- Available tools:
  - `query_db(query)`: Executes SELECT queries and returns results.
  - `insert_db(query)`: Executes INSERT statements.
  - `update_db(query)`: Executes UPDATE statements.
  - `delete_db(query)`: Executes DELETE statements.
  - `create_table(query)`: Executes CREATE TABLE statements.
  - `alter_table(query)`: Executes ALTER TABLE statements.
  - `drop_table(query)`: Executes DROP TABLE statements.

### 2. Data migration between databases
- Run the migration script to copy all tables and data from PostgreSQL to SQLite:
  ```bash
  python3 migrate_postgres_to_sqlite.py
  ```
- You can adapt the script to migrate data in both directions or between different schemas.

### 3. CRUD operation examples
- **Create a record:**
  ```sql
  INSERT INTO users (email, password) VALUES ('user@domain.com', 'secret');
  ```
- **Read records:**
  ```sql
  SELECT * FROM products WHERE is_active = TRUE;
  ```
- **Update records:**
  ```sql
  UPDATE categories SET name = 'New Technologies' WHERE id = 1;
  ```
- **Delete records:**
  ```sql
  DELETE FROM carts WHERE created_at < '2024-01-01';
  ```

## MCP Configuration (`mcp_config.json` or `claude_desktop_config.json`)

To ensure MCP tools work properly, define each service in your configuration file (e.g., `~/.codeium/windsurf/mcp_config.json` or `~/.config/Claude/claude_desktop_config.json`). Example:

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
      "--url", "postgresql://user:password@localhost:5432/ecommerce"
    ]
  }
}
```

- Change the paths, credentials, and ports according to your environment.
- By default, PostgreSQL uses port 5432. If you already have a database on that port, you can specify another (e.g., 5433).
- Do not include real passwords in the configuration file; replace `user` and `password` with the appropriate values.
- You can add more services for other engines or databases.
- The block name (e.g., `SqliteManagement`) will be the MCP tool identifier.

## Dependencies
- Python 3.8+
- psycopg2-binary
- sqlite3
- PostgreSQL (server and configured database)

## Notes
- Make sure to properly configure the MCP services in your `mcp_config.json` (or `claude_desktop_config.json`) file following the example above.
- Also configure the connection credentials in `connection.py` according to your environment and database.
- After changes to the database structure, restart the MCP server to avoid connection issues.
- You can adapt the scripts to migrate or manage other catalogs as needed.

---
