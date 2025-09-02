import os
import json
import openai
from github import Github

# Validate environment variables
required_env_vars = ["GITHUB_TOKEN", "OPENAI_API_KEY", "GITHUB_REPOSITORY", "GITHUB_EVENT_PATH"]
for var in required_env_vars:
    if not os.getenv(var):
        raise EnvironmentError(f"Missing required environment variable: {var}")

# Load tokens
github_token = os.getenv("GITHUB_TOKEN")
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load GitHub event payload (contains PR number)
event_path = os.getenv("GITHUB_EVENT_PATH")
with open(event_path, "r") as f:
    event = json.load(f)

pr_number = event["pull_request"]["number"]
repo_name = os.getenv("GITHUB_REPOSITORY")

# Connect to GitHub
g = Github(github_token)
repo = g.get_repo(repo_name)

# Get PR details
pr = repo.get_pull(pr_number)
files = pr.get_files()

comments = []

# Analyze each file change
for file in files:
    if file.filename.endswith((".py", ".js", ".ts", ".java", ".cpp", ".vue")):  # Only suggest for code files
        prompt = f"""
        You are a code reviewer. Suggest improvements for the following code:

        Filename: {file.filename}
        Patch:
        {file.patch}
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a senior code reviewer."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=400,
            )

            suggestion = response["choices"][0]["message"]["content"]
            comments.append(f"### 💡 AI Suggestion for `{file.filename}`\n{suggestion}")

        except Exception as e:
            comments.append(f"⚠️ Error analyzing {file.filename}: {e}")

# Post a single comment on PR
if comments:
    body = "\n\n".join(comments)
    pr.create_issue_comment(body)
