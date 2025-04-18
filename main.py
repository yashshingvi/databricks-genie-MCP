import os
import time
import requests
from dotenv import load_dotenv
from typing import Dict, List
from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv(override=True)

# Global Config
DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")

# Headers
HEADERS = {
    "Authorization": f"Bearer {DATABRICKS_TOKEN}",
    "Content-Type": "application/json"
}

# MCP Server
mcp = FastMCP(
    name="Genie MCP Server",
    description=(
        "This MCP server interfaces with the Databricks Genie API. "
        "Genie is a conversational assistant that allows users to query data within defined spaces "
        "using natural language. This server provides tools to list Genie spaces, get metadata about a space, "
        "start new conversations, and ask follow-up questions."
        "Follow up question is invoked when user askes follow up question to the previous question, else we can call ask_genie."
        "Space ID can be internal, you do not need to show it to users."
    )
)

@mcp.resource("genie://about")
def about_genie() -> str:
    return (
        "📊 Genie is a natural language interface to Databricks data. "
        "You ask questions like 'What are top 5 products sold last month?' and Genie returns SQL + data. "
        "Spaces represent data domains."
    )

@mcp.resource("genie-space://details")
def get_genie_space_id()  -> List[Dict[str, str]]:
    """
    Returns Databricks Genie space IDs and thier names, Genie spaces hav.
    """
    # At this time I could not find api to get all space ids and names.
    # At that time you can create a service principal and assign it to a spaces you want to give it access to.
    # So I am hardcoding the space ids and names.
    # This is a temporary solution and should be replaced with a proper API call in the future.
    return [
        {"space_id": "01f01a54963a1c94b80020c9048124", "title": "Bakehouse Sales Space"},
        {"space_id": "a9bc12345d29169db030324fd0aaaaaa", "title": "Customer Insights"},
        {"space_id": "b7de67890f29169db030324fd0bbbbbb", "title": "Test Space"}
    ]

@mcp.resource("genie-space-details://{space_id}")
def get_genie_space_metadata(space_id: str) -> str:
    """
    Returns metadata about a Databricks Genie Space.
    """
    try:
        url = f"https://{DATABRICKS_HOST}/api/2.0/genie/spaces/{space_id}"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()

        data = resp.json()

        # Validate response content
        if not all(key in data for key in ("space_id", "title", "description")):
            return "⚠️ Incomplete space metadata received from Genie API."

        return (
            f" Genie Space Metadata\n\n"
            f"- `space_id`: `{data['space_id']}`\n"
            f"- `title`: `{data['title']}`\n"
            f"- `description`: {data['description']}"
        )

    except requests.exceptions.HTTPError as http_err:
        return f"HTTP error occurred while fetching Genie space: {http_err}"
    except requests.exceptions.Timeout:
        return "Request to Genie API timed out."
    except requests.exceptions.RequestException as req_err:
        return f"Request error occurred: {req_err}"
    except ValueError:
        return "Failed to parse JSON response from Genie API."
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

@mcp.tool()
def get_space_info(space_id: str) -> str:
    """
    Returns metadata about a Databricks Genie Space.
    """
    return get_genie_space_metadata(space_id)

@mcp.tool()
def ask_genie(space_id: str, question: str) -> str:
    """
    Start a new Databricks Genie conversation, ask a question, and return the SQL + query result from the database.
    Args:
        space_id: Genie space ID
        question: Question to be asked to Databricks Genie
    """
    try:
        base_url = f"https://{DATABRICKS_HOST}/api/2.0/genie/spaces/{space_id}"

        # Step 1: Start conversation
        resp = requests.post(
            f"{base_url}/start-conversation",
            headers=HEADERS,
            json={"content": question}
        )
        resp.raise_for_status()
        data = resp.json()
        conversation_id = data["conversation"]["id"]
        message_id = data["message"]["id"]

        # Step 2: Poll until COMPLETED
        for _ in range(60):
            msg_resp = requests.get(
                f"{base_url}/conversations/{conversation_id}/messages/{message_id}",
                headers=HEADERS
            )
            msg_resp.raise_for_status()
            msg_data = msg_resp.json()
            status = msg_data["status"]

            if status == "COMPLETED":
                attachments = msg_data.get("attachments", [])
                if not attachments:
                    return f" Query completed but no result data."

                attachment = attachments[0]
                attachment_id = attachment.get("attachment_id")
                query_text = attachment.get("text", "No text.")
                sql = attachment.get("query", "No SQL.")

                # Step 3: Retrieve query result
                query_result_url = (
                    f"{base_url}/conversations/{conversation_id}/messages/{message_id}/query-result/{attachment_id}"
                )
                result_resp = requests.get(query_result_url, headers=HEADERS)
                result_resp.raise_for_status()
                result_json = result_resp.json()

                statement = result_json.get("statement_response", {})
                schema = statement.get("manifest", {}).get("schema", {}).get("columns", [])
                rows = statement.get("result", {}).get("data_array", [])

                if not schema or not rows:
                    return f" SQL:\n```sql\n{sql}\n```\n\n🔎 Genie:\n{query_text}\n\n No data returned."

                # Format  table
                headers_row = [col["name"] for col in schema]

                structured_rows = [
                    {
                        headers_row[i]: (str(cell) if cell is not None else "NULL")
                        for i, cell in enumerate(row)
                    }
                    for row in rows
                ]

                table = {
                    "headers": headers_row,
                    "rows": structured_rows
                }

                return (
                    f" Genie:\n{query_text}\n\n"
                    f" SQL:\n```sql\n{sql}\n```\n\n"
                    f" Query Result:\n\n{table}"
                    f" Conversation ID:\n\n{conversation_id}"
                )

            elif status in {"FAILED", "CANCELLED"}:
                return f" Genie returned status: {status}"

            time.sleep(5)

        return f"Timeout waiting for Genie response. conversation_id: `{conversation_id}`"

    except Exception as e:
        return f" Error: {str(e)}"



@mcp.tool()
def follow_up(space_id: str, conversation_id: str, question: str) -> str:
    """
    Ask a follow-up question in an existing Genie conversation and return SQL + query result.
    """
    try:
        base_url = f"https://{DATABRICKS_HOST}/api/2.0/genie/spaces/{space_id}"

        # Step 1: Post follow-up message
        resp = requests.post(
            f"{base_url}/conversations/{conversation_id}/messages",
            headers=HEADERS,
            json={"content": question}
        )
        resp.raise_for_status()
        message_id = resp.json()["id"]

        # Step 2: Poll until COMPLETED
        for _ in range(60):
            msg_resp = requests.get(
                f"{base_url}/conversations/{conversation_id}/messages/{message_id}",
                headers=HEADERS
            )
            msg_resp.raise_for_status()
            msg_data = msg_resp.json()
            status = msg_data["status"]

            if status == "COMPLETED":
                attachments = msg_data.get("attachments", [])
                if not attachments:
                    return f" Follow-up completed but no result data."

                attachment = attachments[0]
                attachment_id = attachment.get("attachment_id")
                query_text = attachment.get("text", "No text.")
                sql = attachment.get("query", "No SQL.")

                # Step 3: Fetch result
                query_result_url = (
                    f"{base_url}/conversations/{conversation_id}/messages/{message_id}/query-result/{attachment_id}"
                )
                result_resp = requests.get(query_result_url, headers=HEADERS)
                result_resp.raise_for_status()
                result_json = result_resp.json()

                statement = result_json.get("statement_response", {})
                schema = statement.get("manifest", {}).get("schema", {}).get("columns", [])
                rows = statement.get("result", {}).get("data_array", [])

                if not schema or not rows:
                    return f"SQL:\n```sql\n{sql}\n```\n\nGenie:\n{query_text}\n\nNo data returned."

                headers_row = [col["name"] for col in schema]

                structured_rows = [
                    {
                        headers_row[i]: (str(cell) if cell is not None else "NULL")
                        for i, cell in enumerate(row)
                    }
                    for row in rows
                ]

                table = {
                    "headers": headers_row,
                    "rows": structured_rows
                }

                return (
                    f"Genie (Follow-up):\n{query_text}\n\n"
                    f"SQL:\n```sql\n{sql}\n```\n\n"
                    f"Query Result:\n\n{table}"
                    f" Conversation ID:\n\n{conversation_id}"
                )

            elif status in {"FAILED", "CANCELLED"}:
                return f"Follow-up failed. Status: {status}"

            time.sleep(5)

        return f"Timeout waiting for follow-up result. conversation_id: `{conversation_id}`"

    except Exception as e:
        return f"Follow-up error: {str(e)}"



if __name__ == "__main__":
    mcp.run(transport="stdio")
