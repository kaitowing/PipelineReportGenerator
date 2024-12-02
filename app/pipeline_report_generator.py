from calendar import c
import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = os.getenv("BITBUCKET_URL", "https://api.bitbucket.org/2.0")
WORKSPACE = os.getenv("BITBUCKET_WORKSPACE")
USERNAME = os.getenv("BITBUCKET_USERNAME")
APP_PASSWORD = os.getenv("BITBUCKET_APP_PASSWORD")
RAW_OUTPUT_FILE = os.getenv("OUTPUT_FILE", "report.json")
REPORT_OUTPUT_FILE = os.getenv("REPORT_OUTPUT_FILE", "report.md")
IGNORE_FORKS = os.getenv("IGNORE_FORKS", "").split(",")
IGNORE_PIPES = os.getenv("IGNORE_PIPES", "").split(",")

# Set the start of the week to the previous Monday
today = datetime.today()
start_of_week = today - timedelta(days=7)
START_OF_THE_WEEK = start_of_week


def fetch_repositories():
    """Fetch all repositories from the workspace updated since the start of the week."""
    url = f"{BASE_URL}/repositories/{WORKSPACE}"
    params = {
        "fields": "values.slug,values.uuid,values.updated_on,next,values.parent.name",
        "q": f"updated_on >= {START_OF_THE_WEEK.isoformat()}",
        "pagelen": 100,
    }
    repositories = []

    while url:
        response = requests.get(url, auth=(USERNAME, APP_PASSWORD), params=params)
        if response.status_code == 200:
            data = response.json()
            for repo in data.get("values", []):
                if repo["slug"] not in IGNORE_PIPES and (
                    not repo.get("parent") or repo["parent"]["name"] not in IGNORE_FORKS
                ):
                    repositories.append(repo)
            url = data.get("next")
            params = None
        else:
            print(
                f"Error fetching repositories: {response.status_code}\n{response.text}"
            )
            break

    return repositories


def fetch_pipeline_data(repo_slug):
    """Fetch pipelines created since the start of the week for a repository and return pipelines, number of pipelines,
       total time spent and users who started the pipeline.
    """
    url = f"{BASE_URL}/repositories/{WORKSPACE}/{repo_slug}/pipelines/"
    params = {
        "fields": "values.created_on,values.build_seconds_used,values.creator.nickname,next",
        "sort": "-created_on",
        "pagelen": 100,
    }
    pipelines = []
    total_pipelines = 0
    total_time_spent = 0
    users = []

    while url:
        response = requests.get(url, auth=(USERNAME, APP_PASSWORD), params=params)
        if response.status_code == 200:
            data = response.json()
            url = data.get("next")
            params = None

            if not data.get("values"):
                break

            for pipeline in data.get("values", []):
                created_on = datetime.fromisoformat(
                    pipeline["created_on"].split("Z")[0]
                )
                if created_on > START_OF_THE_WEEK:
                    pipelines.append(pipeline)
                    total_pipelines += 1
                    total_time_spent += pipeline.get("build_seconds_used", 0)
                    if pipeline.get("creator"):
                        users.append(pipeline["creator"].get("nickname"))
                else:
                    url = None
                    break
        else:
            print(
                f"Error fetching pipelines for {repo_slug}: {response.status_code}\n{response.text}"
            )
            break

    return pipelines, total_pipelines, total_time_spent / 60, list(set(users))


def save_to_file(data, file_path, mode="w", formatted=True):
    """Save data to a file."""
    try:
        delete_file(file_path)
        with open(file_path, mode) as file:
            content = json.dumps(data, indent=4) if formatted else data
            file.write(content)
        print(f"Data saved to {file_path}")
    except IOError as e:
        print(f"Error saving file: {e}")


def delete_file(file_path):
    """Delete a file."""
    try:
        os.remove(file_path)
        print(f"File {file_path} deleted.")
    except FileNotFoundError:
        print(f"File {file_path} not found.")


def save_report(repositories, file_path):
    """Save a report with repository and pipeline data."""
    try:
        delete_file(file_path)
        with open(file_path, "w") as file:
            file.write("# Repository and Pipeline Report\n\n")
            for repo in repositories:
                file.write(f"## Repository: {repo['slug']}\n")
                file.write(f"- **Number of Pipelines**: {repo['pipelines_count']}\n")
                file.write(
                    f"- **Total Time Spent**: {repo['pipelines_time_spent']:.2f} minutes\n"
                )
                file.write("- **Users who Created Pipelines**:\n")
                for user in repo["users"]:
                    file.write(f"  - {user}\n")
                file.write(
                    f"- **User with Most Pipelines**: {max(set(repo['users']), key=repo['users'].count) if repo['users'] else 'N/A'}\n\n"
                )
        print(f"Report saved to {file_path}")
    except IOError as e:
        print(f"Error saving file: {e}")


def print_execution_completion(total, current):
    """Print the current execution completion."""
    percentage = (current / total) * 100
    print(f"Loading data... {current}/{total}  {percentage:.2f}%")


def main():
    """Main script flow."""
    repositories = fetch_repositories()
    number_of_repositories = len(repositories)
    index = 0

    for repo in repositories:
        print_execution_completion(number_of_repositories, index)
        pipelines, count, time_spent, users = fetch_pipeline_data(repo["slug"])
        repo.update(
            {
                "pipelines_count": count,
                "pipelines_time_spent": time_spent,
                "users": users,
                "pipelines": pipelines,
            }
        )
        index += 1

    if repositories:
        save_to_file(repositories, RAW_OUTPUT_FILE)
        save_report(repositories, REPORT_OUTPUT_FILE)


if __name__ == "__main__":
    main()
