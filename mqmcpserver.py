#!/usr/bin/env python3
"""
IBM MQ MCP Server

Model Context Protocol server for IBM MQ integration.
Provides tools to interact with IBM MQ via REST API.

Copyright (c) 2025 IBM Corp.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import json
import os

import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("mqmcpserver")

# Change this to point to your mqweb server
# URL_BASE = "https://localhost:9443/ibmmq/rest/v3/admin/"

# Change these to a suitable user in your mqweb server
# SER_NAME = "mqreader"
# PASSWORD = "mqreader"

# mqmcpserver.py

# URL base do seu mqweb server
URL_BASE = os.getenv("URL_BASE", "https://localhost:9443/ibmmq/rest/v2/admin")

# Usuário e senha que você usou no teste via REST
USER_NAME = os.getenv("USER_NAME", "admin")
PASSWORD = os.getenv("PASSWORD", "admin")

MCP_HOST = os.getenv("MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.getenv("MCP_PORT", "8414"))


@mcp.tool()
async def dspmq() -> str:
    """List available queue managers and whether they are running or not"""
    headers = {"Content-Type": "application/json", "ibm-mq-rest-csrf-token": "token"}

    url = URL_BASE + "qmgr/"

    auth = httpx.BasicAuth(username=USER_NAME, password=PASSWORD)
    async with httpx.AsyncClient(verify=False, auth=auth) as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return prettify_dspmq(response.content.decode("utf-8"))
        except (httpx.RequestError, httpx.HTTPStatusError) as err:
            print(err)
            return "Something went wrong!"


def prettify_dspmq(payload: str) -> str:
    """
    Format the output of dspmq command for better readability.

    Args:
        payload: Raw JSON response from IBM MQ REST API as string

    Returns:
        Formatted string with queue manager information
    """
    json_output = json.loads(payload)
    prettified_output = "\n---\n"
    for queue_manager in json_output["qmgr"]:
        prettified_output += (
            f"name = {queue_manager['name']}, "
            f"running = {queue_manager['state']}\n---\n"
        )

    return prettified_output


@mcp.tool()
async def runmqsc(qmgr_name: str, mqsc_command: str) -> str:
    """Run an MQSC command against a specific queue manager

    Args:
        qmgr_name: A queue manager name
        mqsc_command: An MQSC command to run on the queue manager
    """
    headers = {"Content-Type": "application/json", "ibm-mq-rest-csrf-token": "a"}

    data = '{"type":"runCommand","parameters":{"command":"' + mqsc_command + '"}}'

    url = URL_BASE + "action/qmgr/" + qmgr_name + "/mqsc"

    auth = httpx.BasicAuth(username=USER_NAME, password=PASSWORD)
    async with httpx.AsyncClient(verify=False, auth=auth) as client:
        try:
            response = await client.post(
                url, content=data, headers=headers, timeout=30.0
            )
            response.raise_for_status()
            return prettify_runmqsc(response.content.decode("utf-8"))
        except (httpx.RequestError, httpx.HTTPStatusError) as err:
            print(err)
            return "Something went wrong!"


def prettify_runmqsc(payload: str) -> str:
    """
    Format the output of MQSC commands for better readability.

    Note: This will not work against z/OS queue managers which use
    a slightly different format.

    Args:
        payload: Raw JSON response from IBM MQ REST API as string

    Returns:
        Formatted string with MQSC command results
    """
    json_output = json.loads(payload)
    prettified_output = "\n---\n"
    for command_response in json_output["commandResponse"]:
        prettified_output += command_response["text"][0] + "\n---\n"

    return prettified_output


if __name__ == "__main__":
    # Configure host and port via environment variables
    os.environ["HOST"] = MCP_HOST
    os.environ["PORT"] = str(MCP_PORT)

    # Run the MCP server
    mcp.run(transport="streamable-http")
