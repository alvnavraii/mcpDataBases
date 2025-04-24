from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession
from mcp import StdioServerParameters
import asyncio

async def main():
    server_params = StdioServerParameters(
        command = "python",
        args = ["main.py"]
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            print("Connected to server")
            tools_result = await session.list_tools()
            print("Available tools:")
            add_tool_found = False
            for key, value in tools_result:
                if key == "tools" and value:
                    for tool in value:
                        print(f" - {tool.name}: {tool.description}")
                        if tool.name == "query_db":
                            add_tool_found = True
                            result = await session.call_tool("query_db", {"query": "SELECT * FROM users"})
                            print(f"Result: {result.content}")
            if not add_tool_found:
                print("Tool 'query_db' not found")

                

if __name__ == "__main__":
    asyncio.run(main())