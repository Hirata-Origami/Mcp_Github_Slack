GitHub Summary Tool
Author: Hirata-OrigamiDate: April 18, 2025License: MIT
Overview
The GitHub Summary Tool is a Python-based application built using the Model Context Protocol (MCP) Python SDK. It fetches a user's daily GitHub activities—such as pull requests, issues, commits, and branch updates—and sends a formatted summary to a specified Slack channel. The tool is designed to integrate seamlessly with LLMs and MCP-compatible clients, exposing its functionality as an MCP tool.
Features

Daily Activity Summary: Retrieves a user's GitHub activities for the current day, including:
Pull requests created and merged
Issues created and closed
Commits made
Branches updated

Slack Integration: Sends the summary to a Slack channel via an MCP Slack server.
MCP Compatibility: Exposes functionality as an MCP tool (send_daily_github_summary) for use with LLMs or MCP clients.
Configurable: Uses environment variables for GitHub and Slack authentication.

Installation
Prerequisites

Python 3.8+
MCP Python SDK (pip install "mcp[cli]" or uv add "mcp[cli]")
Docker (for running GitHub and Slack MCP servers)
Access to GitHub and Slack MCP servers (images: ghcr.io/github/github-mcp-server and mcp/slack)

Setup

Clone the Repository:
git clone https://github.com/Hirata-Origami/github-summary-tool.git
cd github-summary-tool

Install Dependencies:Using uv (recommended):
uv init github-summary-tool
uv add "mcp[cli]"

Or with pip:
pip install "mcp[cli]"

Set Environment Variables:Create a .env file or set the following variables:
export GITHUB_TOKEN="your_github_personal_access_token"
export SLACK_BOT_TOKEN="your_slack_bot_token"
export SLACK_TEAM_ID="your_slack_team_id"
export SLACK_CHANNEL_ID="your_slack_channel_id"

Replace placeholders with actual values. Default values are provided for testing but should be replaced for production use.

Verify Docker Access:Ensure Docker is running and you have access to the required images:

ghcr.io/github/github-mcp-server
mcp/slack

Usage
Running the Server

Development Mode (with MCP Inspector):
uv run mcp dev server.py

This starts the server and opens the MCP Inspector for testing.

Claude Desktop Integration:
uv run mcp install server.py

Installs the tool in Claude Desktop for LLM interaction.

Direct Execution:
uv run python server.py

Runs the server directly, exposing the MCP tool.

Invoking the Tool
The tool exposes a single MCP tool, send_daily_github_summary, which takes a GitHub username as input:
await session.call_tool("send_daily_github_summary", {"user": "Hirata-Origami"})

This fetches the user's daily activities and sends a summary to the configured Slack channel, returning "Summary sent successfully".
Example Output
The Slack message will look like:
Daily GitHub Activity Summary for Hirata-Origami on 2025-04-18:

**Pull Requests Created Today:**

- None

**Pull Requests Merged Today:**

- None

**Issues Created Today:**

- None

**Issues Closed Today:**

- None

**Commits Made Today:**

- None

**Branches Updated Today:**

- None

**Branches Deleted Today:**

- Not detectable with current API

**Repositories Deleted Today:**

- Not detectable with current API

Future Implementation Plans
To enhance the tool's capabilities, the following features are planned:

Repository Management:

Create Repository: Add a tool to create a new GitHub repository with specified parameters (e.g., name, description, visibility).
Update Repository: Enable updating repository metadata (e.g., description, default branch).
Delete Repository: Allow deletion of a repository, with appropriate safeguards.

Branch Management:

Create Branch: Add a tool to create a new branch in a specified repository from a given commit or branch.
Delete Branch: Enable deletion of a branch, ensuring it’s not the default branch or protected.

Implementation Notes

GitHub API Integration: These features will leverage additional GitHub MCP server tools (e.g., create_repository, create_branch, delete_branch) if available, or direct API calls if necessary.
Error Handling: Robust error handling for permissions, rate limits, and invalid inputs.
MCP Tools: Each feature will be exposed as a separate MCP tool (e.g., create_repository, delete_branch) with clear argument schemas.
Slack Notifications: Extend the summary to include repository and branch actions performed via the tool.

Contributing
Contributions are welcome! Please:

Fork the repository.
Create a feature branch (git checkout -b feature/your-feature).
Commit changes (git commit -m "Add your feature").
Push to the branch (git push origin feature/your-feature).
Open a pull request.

See the MCP Python SDK Contributing Guide for additional guidelines.
License
This project is licensed under the MIT License. See the LICENSE file for details.
Contact
For questions or suggestions, contact Hirata-Origami via GitHub.
