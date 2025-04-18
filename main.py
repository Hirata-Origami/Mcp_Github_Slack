import json
import os
from datetime import datetime, timezone, timedelta
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.shared.exceptions import McpError
from mcp.server.fastmcp import FastMCP

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_TEAM_ID = os.getenv("SLACK_TEAM_ID")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")

if not GITHUB_TOKEN or not SLACK_BOT_TOKEN or not SLACK_TEAM_ID or not SLACK_CHANNEL_ID:
    raise ValueError("Environment variables GITHUB_TOKEN, SLACK_BOT_TOKEN, SLACK_TEAM_ID, and SLACK_CHANNEL_ID must be set.")

github_server_params = StdioServerParameters(
    command="docker",
    args=["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server"],
    env={"GITHUB_PERSONAL_ACCESS_TOKEN": GITHUB_TOKEN}
)

slack_server_params = StdioServerParameters(
    command="docker",
    args=["run", "-i", "--rm", "-e", "SLACK_BOT_TOKEN", "-e", "SLACK_TEAM_ID", "-e", "SLACK_CHANNEL_IDS", "mcp/slack"],
    env={"SLACK_BOT_TOKEN": SLACK_BOT_TOKEN, "SLACK_TEAM_ID": SLACK_TEAM_ID, "SLACK_CHANNEL_IDS": SLACK_CHANNEL_ID}
)

def extract_json_from_tool_response(response):
    """Extract JSON data from an MCP tool response."""
    if hasattr(response, 'error') and response.error:
        print(f"Tool call error: {response.error}")
        return None
    text_content = next((c for c in response.content if c.type == "text"), None)
    if not text_content or not text_content.text:
        print("No text content in response")
        return None
    if text_content.text.startswith("Error:"):
        print(f"Tool error: {text_content.text}")
        return None
    try:
        return json.loads(text_content.text)
    except json.JSONDecodeError:
        print(f"Failed to parse JSON from tool response: {text_content.text}")
        return None

async def fetch_github_activities(user: str):
    """Fetch GitHub activities for the specified user for today."""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    async with stdio_client(github_server_params) as (github_read, github_write):
        async with ClientSession(github_read, github_write) as github_session:
            await github_session.initialize()
            repos_response = await github_session.call_tool("search_repositories", {"query": f"user:{user}"})
            repos_data = extract_json_from_tool_response(repos_response)
            repos = repos_data.get("items", []) if repos_data else []

            prs_created = []
            prs_merged = []
            issues_created = []
            issues_closed = []
            commits_by_repo = {}
            updated_branches_by_repo = {}

            prs_created_response = await github_session.call_tool("search_issues", {
                "q": f"author:{user} type:pr created:{today_start.strftime('%Y-%m-%d')}..{today_end.strftime('%Y-%m-%d')}"
            })
            prs_created_data = extract_json_from_tool_response(prs_created_response)
            if prs_created_data:
                for item in prs_created_data.get("items", []):
                    repo = f"{item['repository_url'].split('/')[-2]}/{item['repository_url'].split('/')[-1]}"
                    prs_created.append({
                        "repo": repo,
                        "number": item["number"],
                        "title": item["title"],
                        "url": item["html_url"]
                    })

            prs_merged_response = await github_session.call_tool("search_issues", {
                "q": f"author:{user} is:pr merged:{today_start.strftime('%Y-%m-%d')}..{today_end.strftime('%Y-%m-%d')}"
            })
            prs_merged_data = extract_json_from_tool_response(prs_merged_response)
            if prs_merged_data:
                for item in prs_merged_data.get("items", []):
                    repo = f"{item['repository_url'].split('/')[-2]}/{item['repository_url'].split('/')[-1]}"
                    prs_merged.append({
                        "repo": repo,
                        "number": item["number"],
                        "title": item["title"],
                        "url": item["html_url"]
                    })

            issues_created_response = await github_session.call_tool("search_issues", {
                "q": f"author:{user} type:issue created:{today_start.strftime('%Y-%m-%d')}..{today_end.strftime('%Y-%m-%d')}"
            })
            issues_created_data = extract_json_from_tool_response(issues_created_response)
            if issues_created_data:
                for item in issues_created_data.get("items", []):
                    repo = f"{item['repository_url'].split('/')[-2]}/{item['repository_url'].split('/')[-1]}"
                    issues_created.append({
                        "repo": repo,
                        "number": item["number"],
                        "title": item["title"],
                        "url": item["html_url"]
                    })

            issues_closed_response = await github_session.call_tool("search_issues", {
                "q": f"author:{user} type:issue closed:{today_start.strftime('%Y-%m-%d')}..{today_end.strftime('%Y-%m-%d')}"
            })
            issues_closed_data = extract_json_from_tool_response(issues_closed_response)
            if issues_closed_data:
                for item in issues_closed_data.get("items", []):
                    repo = f"{item['repository_url'].split('/')[-2]}/{item['repository_url'].split('/')[-1]}"
                    issues_closed.append({
                        "repo": repo,
                        "number": item["number"],
                        "title": item["title"],
                        "url": item["html_url"]
                    })

            for repo in repos:
                repo_name = f"{repo['owner']['login']}/{repo['name']}"
                try:
                    commit_response = await github_session.call_tool("list_commits", {
                        "owner": repo["owner"]["login"],
                        "repo": repo["name"],
                        "since": today_start.isoformat()
                    })
                    commit_list = extract_json_from_tool_response(commit_response)
                    if commit_list:
                        today_commits = []
                        for commit in commit_list:
                            commit_date = datetime.fromisoformat(commit["commit"]["author"]["date"].replace("Z", "+00:00"))
                            if commit_date >= today_start and commit["author"]["login"] == user:
                                today_commits.append({
                                    "message": commit["commit"]["message"].split("\n")[0],
                                    "sha": commit["sha"]
                                })
                        if today_commits:
                            commits_by_repo[repo_name] = today_commits[:1]
                except McpError as e:
                    if "Git Repository is empty" in str(e):
                        print(f"Skipping empty repository: {repo_name}")
                        continue
                    raise

                branch_response = await github_session.call_tool("list_branches", {
                    "owner": repo["owner"]["login"],
                    "repo": repo["name"]
                })
                branch_data = extract_json_from_tool_response(branch_response)
                if branch_data:
                    for branch in branch_data:
                        commit_response = await github_session.call_tool("get_commit", {
                            "owner": repo["owner"]["login"],
                            "repo": repo["name"],
                            "sha": branch["commit"]["sha"]
                        })
                        commit_data = extract_json_from_tool_response(commit_response)
                        if commit_data:
                            commit_date = datetime.fromisoformat(commit_data["commit"]["author"]["date"].replace("Z", "+00:00"))
                            if commit_date >= today_start and commit_data["author"]["login"] == user:
                                updated_branches_by_repo.setdefault(repo_name, []).append({
                                    "name": branch["name"],
                                    "commit_message": commit_data["commit"]["message"].split("\n")[0]
                                })

            return prs_created, prs_merged, issues_created, issues_closed, commits_by_repo, updated_branches_by_repo

def build_summary(user: str, prs_created, prs_merged, issues_created, issues_closed, commits_by_repo, updated_branches_by_repo):
    """Build a formatted summary string of GitHub activities."""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    summary = f"Daily GitHub Activity Summary for {user} on {today_start.strftime('%Y-%m-%d')}:\n\n"

    summary += "**Pull Requests Created Today:**\n"
    if prs_created:
        for pr in prs_created:
            summary += f"- PR #{pr['number']} in {pr['repo']}: \"{pr['title']}\" ({pr['url']})\n"
    else:
        summary += "- None\n"

    summary += "**Pull Requests Merged Today:**\n"
    if prs_merged:
        for pr in prs_merged:
            summary += f"- PR #{pr['number']} in {pr['repo']}: \"{pr['title']}\" ({pr['url']})\n"
    else:
        summary += "- None\n"

    summary += "**Issues Created Today:**\n"
    if issues_created:
        for issue in issues_created:
            summary += f"- Issue #{issue['number']} in {issue['repo']}: \"{issue['title']}\" ({issue['url']})\n"
    else:
        summary += "- None\n"

    summary += "**Issues Closed Today:**\n"
    if issues_closed:
        for issue in issues_closed:
            summary += f"- Issue #{issue['number']} in {issue['repo']}: \"{issue['title']}\" ({issue['url']})\n"
    else:
        summary += "- None\n"

    summary += "**Commits Made Today:**\n"
    if commits_by_repo:
        for repo, commits in commits_by_repo.items():
            summary += f"- {repo}:\n"
            for commit in commits:
                summary += f"  - \"{commit['message']}\" (SHA: {commit['sha'][:7]})\n"
    else:
        summary += "- None\n"

    summary += "**Branches Updated Today:**\n"
    if updated_branches_by_repo:
        for repo, branches in updated_branches_by_repo.items():
            summary += f"- {repo}:\n"
            for branch in branches:
                summary += f"  - {branch['name']}: \"{branch['commit_message']}\"\n"
    else:
        summary += "- None\n"

    summary += "**Branches Deleted Today:**\n- Not detectable with current API\n"
    summary += "**Repositories Deleted Today:**\n- Not detectable with current API\n"

    return summary

async def send_slack_summary(summary: str):
    """Send the summary to Slack via the MCP Slack server."""
    async with stdio_client(slack_server_params) as (slack_read, slack_write):
        async with ClientSession(slack_read, slack_write) as slack_session:
            await slack_session.initialize()
            response = await slack_session.call_tool("slack_post_message", {
                "channel_id": SLACK_CHANNEL_ID,
                "text": summary
            })
            if hasattr(response, 'error') and response.error:
                print(f"Failed to send Slack message: {response.error}")
            else:
                print("Summary sent successfully.")

mcp = FastMCP("GitHub Summary Tool")

@mcp.tool()
async def send_daily_github_summary(user: str) -> str:
    """Generate and send a daily GitHub activity summary for the specified user to Slack."""
    prs_created, prs_merged, issues_created, issues_closed, commits_by_repo, updated_branches_by_repo = await fetch_github_activities(user)
    summary = build_summary(user, prs_created, prs_merged, issues_created, issues_closed, commits_by_repo, updated_branches_by_repo)
    await send_slack_summary(summary)
    return "Summary sent successfully"

if __name__ == "__main__":
    mcp.run()