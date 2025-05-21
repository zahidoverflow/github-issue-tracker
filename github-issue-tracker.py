#!/usr/bin/env python3
"""
GitHub Issue Tracker - Monitors repositories for new issues and sends notifications to Telegram.
Required dependency: requests
"""
import sys
import subprocess
import importlib.util

# Check if requests is installed, install if not
if importlib.util.find_spec("requests") is None:
    print("Installing required dependency 'requests'...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])

# Now import the required modules
import requests
import time
import os
import re
import json

# -----------------------Configuration-----------------------
# Telegram Bot Token (get from BotFather)
TELEGRAM_BOT_TOKEN = ""
# Telegram Chat ID (ID of the chat to send messages to)
TELEGRAM_CHAT_ID = ""
# GitHub Personal Access Token (optional, for higher rate limits)
GITHUB_TOKEN = ""
# Path to the file containing the list of GitHub repositories
GITHUB_REPOS_FILE = "github_repo_links.txt"
# Path to the file for storing last known issue IDs
LAST_ISSUE_FILE = "last_known_issues.json"
# Seconds to wait between each API request (1 request per second)
REQUEST_DELAY = 1

# -----------------------Functions-----------------------
def read_repositories_from_file(file_path):
    """Reads repository URLs from the specified file."""
    try:
        with open(file_path, 'r') as file:
            repos = [line.strip() for line in file if line.strip()]
        return repos
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return []
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

def load_last_issues(file_path):
    """Loads last known issue IDs from a JSON file."""
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Last issues file ({file_path}) not found. Starting fresh.")
        return {}
    except json.JSONDecodeError:
        print(f"Error decoding JSON from {file_path}. Starting fresh.")
        return {}
    except Exception as e:
        print(f"Error loading last issues from {file_path}: {e}. Starting fresh.")
        return {}

def save_last_issues(file_path, last_issues):
    """Saves last known issue IDs to a JSON file."""
    try:
        with open(file_path, 'w') as file:
            json.dump(last_issues, file, indent=4)
    except Exception as e:
        print(f"Error saving last issues to {file_path}: {e}")

def fetch_issues(repo_url):
    """Fetches open issues from the GitHub repository."""
    # Extract owner and repo name from the URL
    match = re.search(r"github.com/([^/]+)/([^/]+)", repo_url)
    if not match:
        print(f"Invalid GitHub repository URL: {repo_url}")
        return None
    owner, repo = match.groups()

    # Use the search API to specifically find open issues (not PRs)
    api_url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    try:
        # Add headers for API version and token
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {GITHUB_TOKEN}",
        }
        # Parameters to get only open issues, not PRs
        params = {
            "state": "open",
            "sort": "created",
            "direction": "desc",
            "per_page": 30
        }
        response = requests.get(api_url, headers=headers, params=params)
        response.raise_for_status()
        
        # Filter out pull requests (PRs have a 'pull_request' key)
        issues = [issue for issue in response.json() if 'pull_request' not in issue]
        return issues
    except requests.exceptions.RequestException as e:
        print(f"Error fetching issues from {api_url}: {e}")
        if 'response' in locals() and response is not None and hasattr(response, 'text'):
            print(f"Response content: {response.text}")
        return None

def send_telegram_message(token, chat_id, message):
    """Sends a message to the Telegram chat using direct HTTP API call."""
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": message,
            "disable_web_page_preview": True,  # Prevent link previews
            "parse_mode": "HTML"  # Using HTML format instead of Markdown - more reliable
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        print(f"✅ Found new issue(s): Notification sent")
    except Exception as e:
        print(f"Error sending message: {e}")
        # Try again without parse_mode if there was an error
        try:
            data["parse_mode"] = ""
            # Strip any HTML tags for plain text
            plain_text = message.replace("<b>", "").replace("</b>", "")
            plain_text = plain_text.replace("<i>", "").replace("</i>", "")
            plain_text = plain_text.replace("<code>", "").replace("</code>", "")
            plain_text = plain_text.replace("<pre>", "").replace("</pre>", "")
            data["text"] = plain_text
            response = requests.post(url, data=data)
            response.raise_for_status()
            print("Notification sent successfully with plain text.")
        except Exception as e2:
            print(f"Error sending plain text message: {e2}")

def main():
    """Main function to monitor GitHub repositories and send notifications."""
    # Read repositories from the file
    repositories = read_repositories_from_file(GITHUB_REPOS_FILE)
    if not repositories:
        print("No repositories to monitor. Exiting.")
        return

    # Load last known issue IDs from file, or initialize if not found/invalid
    last_known_issues = load_last_issues(LAST_ISSUE_FILE)
    # Ensure all current repositories have an entry
    for repo_url in repositories:
        if repo_url not in last_known_issues:
            last_known_issues[repo_url] = None

    # Main loop to check repositories for new issues continuously
    repo_index = 0
    while True:
        # Record the start time of this iteration
        start_time = time.time()
        
        # Get next repository in the list (cycle through them)
        repo_url = repositories[repo_index]
        repo_index = (repo_index + 1) % len(repositories)
        
        # Make the request
        issues = fetch_issues(repo_url)
        
        # Process the results
        if issues is not None and len(issues) > 0:
            # Get the highest issue number (most recent)
            latest_issue_number = max(issue['number'] for issue in issues)
            
            # Check if this is the first run for this repository
            if last_known_issues[repo_url] is None:
                # First run - just record the latest issue number
                last_known_issues[repo_url] = latest_issue_number
                print(f"Monitoring: {repo_url} | Latest issue: #{latest_issue_number}")
            elif latest_issue_number > last_known_issues[repo_url]:
                # New issues found since last check
                new_issues = [issue for issue in issues if issue['number'] > last_known_issues[repo_url]]
                
                # Sort new issues by issue number (ascending)
                new_issues.sort(key=lambda x: x['number'])
                
                if new_issues:
                    # Prepare and send notification
                    message_lines = [f"<b>✅ Found new issue(s): {repo_url}/issues</b>"]
                    for issue in new_issues:
                        message_lines.append(f"- {issue['title']}")
                    
                    message = "\n".join(message_lines)
                    send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message)
                
                # Update last known issue number
                last_known_issues[repo_url] = latest_issue_number
                print(f"Updated latest issue number for {repo_url} to #{latest_issue_number}")
            else:
                print(f"No new issues: {repo_url}/issues > latest is still #{last_known_issues[repo_url]}")
        elif issues is not None:
            print(f"No open issues: {repo_url}/issues")
        else:
            print(f"Could not fetch issues: {repo_url}/issues")

        # Save last known issue IDs after each repository check
        save_last_issues(LAST_ISSUE_FILE, last_known_issues)
        
        # Calculate how much time elapsed during this iteration
        elapsed_time = time.time() - start_time
        
        # If processing took less than 1 second, wait just enough to maintain 1 req/sec
        if elapsed_time < REQUEST_DELAY:
            time.sleep(REQUEST_DELAY - elapsed_time)
        # If processing took more than 1 second, don't wait at all
        # This ensures we never exceed 1 request per second, but also don't add unnecessary delay

if __name__ == "__main__":
    main()
