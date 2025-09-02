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
quota_exceeded = False

# Analyze each file change
for file in files:
    print(f"Processing file: {file.filename}")
    patch = file.patch if len(file.patch) <= 3000 else file.patch[:3000] + "\n... [truncated]"
    print(f"Patch for {file.filename}:\n{patch}")

    prompt = f"""
    You are a code reviewer. Suggest improvements for the following code:

    Filename: {file.filename}
    Patch:
    {patch}
    """

    try:
        # Updated API call for openai>=1.0.0
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a senior code reviewer."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=400,
        )
        suggestion = response.choices[0].message.content
        print(f"Suggestion for {file.filename}:\n{suggestion}")
        comments.append((file.filename, suggestion))

    except openai.APIError as e:
        if "insufficient_quota" in str(e):
            print(f"⚠️ OpenAI quota exceeded while analyzing `{file.filename}`")
            quota_exceeded = True
        else:
            print(f"⚠️ OpenAI API error analyzing `{file.filename}`: {e}")
    except Exception as e:
        print(f"⚠️ Unexpected error analyzing `{file.filename}`: {e}")

# Show results in GitHub Checks output
if comments:
    for filename, suggestion in comments:
        # ✅ GitHub annotation (appears in Checks tab)
        print(f"::notice file={filename}::💡 AI Suggestion: {suggestion}")
elif quota_exceeded:
    # ✅ Warning annotation if quota is exceeded
    print("::warning::⚠️ AI suggestions skipped because the OpenAI API quota has been exceeded.")
else:
    print("::notice::No AI suggestions for this PR.")
