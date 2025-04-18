
# Databricks Genie MCP Server

A Model Context Protocol (MCP) server that connects to the Databricks Genie API, allowing LLMs to ask natural language questions, run SQL queries, and interact with Databricks conversational agents.


## ✨ Features

- List Genie spaces available in your Databricks workspace (Currently Manual/Using Resource)
- Fetch metadata (title, description) of a specific Genie space
- Start new Genie conversations with natural language questions
- Ask follow-up questions in ongoing Genie conversations
- Retrieve SQL and result tables in structured format

## 🧱 Prerequisites

- Python 3.7+
- Databricks workspace with:
  - Personal access token
  - Genie API enabled
  - Permissions to access Genie spaces and run queries


## ⚙️ Setup

1. **Clone this repository**

2. **Create and activate a virtual environment** (recommended):
  

```
 python -m venv .venv
 source .venv/bin/activate
 ```

   
**Install dependencies:**

```
pip install -r requirements.txt
```

Create a **.env** file in the root directory with the following variables:

```
DATABRICKS_HOST=your-databricks-instance.cloud.databricks.com # Don't add https
DATABRICKS_TOKEN=your-personal-access-token
```


📌 **Manually Adding Genie Space IDs**

**Note:**  
 At this time, the Databricks Genie API **does not provide a public endpoint to list all available space IDs and titles**.  (afaik)
As a workaround, you need to **manually add the Genie space IDs and their titles** in the `get_genie_space_id()` function in `main.py`.





## 🧪 Test the Server
You can test the MCP server using the inspector (optional but recommended):

```
npx @modelcontextprotocol/inspector python main.py
```
OR

**You can directly build and run docker to test the server**

## 💬 Use with Claude Desktop

Download Claude Desktop

**Install Your MCP Server:**
From your project directory, run:

```
mcp install main.py
```
**Once Server Installed**
  1. Connect in Claude
   
   2. Open Claude Desktop
   
   3. Click Resources → Add Resource
   
   4. Select your Genie MCP Server
   
   5. Start chatting with your data using natural language! 🎯




## 🧾 Obtaining Databricks Credentials
**Host**
Your Databricks instance URL (e.g., your-instance.cloud.databricks.com) — do not include https://

**Token**

 1. Go to your Databricks workspace
    
 2. Click your username (top right) → User Settings
 3. Under the Developer tab, click Manage under "Access tokens"
 4. Generate a new token and copy it




## 🚀 Running the Server

```
python main.py
```
This will start the Genie MCP server over the stdio transport for LLM interaction.

## 🧰 Available MCP Tools
The following MCP tools are available:


**Tool	Description**
1. get_genie_space_id()	List available Genie space IDs and titles
2. get_space_info(space_id: str)	Retrieve title and description of a Genie space
3. ask_genie(space_id: str, question: str)	Start a new Genie conversation and get results
4. follow_up(space_id: str, conversation_id: str, question: str)	Continue an existing Genie conversation

## 🛠️ Troubleshooting
Common Issues
- Invalid host: Ensure the host does not include https://

- Token error: Make sure your personal access token is valid and has access to Genie

- Timeout: Check if the Genie space is accessible and not idle/expired

- No data returned: Ensure your query is valid for the selected space

## 🔐 Security Considerations

 - Keep your .env file secure and never commit it to version control

 - Use minimal scope tokens with expiration whenever possible

- Avoid exposing this server in public-facing environments unless authenticated

## Claude Desktop Screenshots

![image](https://github.com/user-attachments/assets/42b391d3-0ae8-48bd-8665-a1560437b8ef)

![image](https://github.com/user-attachments/assets/eb80c99f-e854-4d55-bb0e-8a447c29ee51)
