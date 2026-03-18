import argparse
import asyncio
from .server import run_server

def main():
    parser = argparse.ArgumentParser(description="Social Search MCP Server")
    parser.parse_args()
    asyncio.run(run_server())

if __name__ == "__main__":
    main()
