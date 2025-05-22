# GitHub Issue Tracker

A small Python tool that monitors one or more GitHub repositories for new issues and sends notifications to a Telegram bot.

## Features

- Polls GitHub's REST API at a controlled rate (1 request/sec)
- Filters out pull requests and only alerts on issues
- Sends formatted HTML notifications to Telegram (with a plain-text fallback)
- Keeps track of the last seen issue per repo to avoid duplicate alerts
- Reads repositories from a simple text file (`github_repo_links.txt`)
- Stores last seen issue numbers in `last_known_issues.json`

## Requirements

- Python 3.6 or newer
- <code>requests</code> library (auto-installed if missing)

## Setup

1. **Clone the repo**
   ```bash
   git clone <your-repo-url>
   cd github-issue-tracker
   ```

2. **Create a `.env` file** in the project root and add your secrets:
   ```dotenv
   # Telegram bot token (from BotFather)
   TELEGRAM_BOT_TOKEN=your_bot_token_here

   # Telegram chat ID (where notifications should go)
   TELEGRAM_CHAT_ID=your_chat_id_here

   # GitHub personal access token (with `repo` scope)
   GITHUB_TOKEN=your_github_token_here
   ```

3. **Populate the list of repositories** in `github_repo_links.txt`, one URL per line, e.g.:
   ```text
   https://github.com/owner1/repo1
   https://github.com/owner2/repo2
   ```

4. **Run the script**:
   ```bash
   python github-issue-tracker.py
   ```

Notifications will appear in your specified Telegram chat whenever a new issue is created.

## Git Ignored Files

- `.env` (your local secrets)
- `last_known_issues.json` (tracking state)

---

Feel free to open an issue or submit a PR if you find bugs or want to add features! 

## Disclaimer

This tool is intended for ethical use only, such as authorized testing. Unauthorized scanning or misuse of this tool may violate laws or terms of service. Always obtain permission before scanning any website or application, and report findings responsibly through proper channels.

## Vibecoding Note

This project was generated with the assistance AI. As an independent security researcher, I used AI to accelerate development and learn best practices, but I have reviewed and understood the code to ensure it aligns with my skills and goals. This demonstrates my ability to leverage modern tools while building practical cybersecurity solutions.
