from mcp.server.fastmcp import FastMCP
from connection import connect



mcp = FastMCP("PostgressManagement")

def execute(query: str):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    cursor.close()
    conn.close()
    return True
    

@mcp.tool()
async def query_db(query: str):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

@mcp.tool()
async def insert_db(query: str):
    return execute(query)

@mcp.tool()
async def update_db(query: str):
    return execute(query)
    

@mcp.tool()
async def delete_db(query: str):
    return execute(query)
    

@mcp.tool()
async def create_table(query: str):
    return execute(query)
    

@mcp.tool()
async def alter_table(query: str):
    return execute(query)
    

@mcp.tool()
async def drop_table(query: str):
    return execute(query)

@mcp.tool()
async def insert_db(query: str):
    return execute(query)
    




if __name__ == "__main__":
    print("Starting server...")
    conn = connect()
    mcp.run(transport="stdio")