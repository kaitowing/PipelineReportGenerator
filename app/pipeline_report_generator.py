from calendar import c
import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from collections import Counter

# Load environment variables
load_dotenv()

BASE_URL = os.getenv("BITBUCKET_URL", "https://api.bitbucket.org/2.0")
WORKSPACE = os.getenv("BITBUCKET_WORKSPACE")
USERNAME = os.getenv("BITBUCKET_USERNAME")
APP_PASSWORD = os.getenv("BITBUCKET_APP_PASSWORD")
RAW_OUTPUT_FILE = os.getenv("OUTPUT_FILE", "report.json")
REPORT_OUTPUT_FILE = os.getenv("REPORT_OUTPUT_FILE", "report.md")
IGNORE_FORKS = os.getenv("IGNORE_FORKS", "").split(",")
IGNORE_REPOSITORIES = os.getenv("IGNORE_REPO", "").split(",")
START_OF_THE_WEEK = datetime.today() - timedelta(days=7)

total_users_list = []

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
                if repo["slug"] not in IGNORE_REPOSITORIES and (
                    not repo.get("parent") or repo["parent"]["name"] not in IGNORE_FORKS
                ):
                    repositories.append(repo)
            url = data.get("next")
            params = None
        else:
            print(f"Error fetching repositories: {response.status_code}\n{response.text}")
            break

    return repositories

def fetch_pipeline_data(repository_slug):
    """Fetch pipelines created since the start of the week for a repository.
    Return pipelines, number of pipelines, total time spent and users who started the pipeline.
    """
    url = f"{BASE_URL}/repositories/{WORKSPACE}/{repository_slug}/pipelines/"
    params = {
        "fields": "values.created_on,values.duration_in_seconds,values.creator.nickname,next",
        "sort": "-created_on",
        "pagelen": 100,
    }
    pipelines = []
    total_pipelines_count = 0
    total_time_spent = 0
    users_list = []

    while url:
        print(f"Fetching pipelines for {repository_slug}")
        response = requests.get(url, auth=(USERNAME, APP_PASSWORD), params=params)
        if response.status_code == 200:
            data = response.json()
            url = data.get("next")
            params = None

            if not data.get("values"):
                break

            for pipeline in data.get("values", []):
                created_on = datetime.fromisoformat(pipeline["created_on"].split("Z")[0])
                if created_on > START_OF_THE_WEEK:
                    pipelines.append(pipeline)
                    total_pipelines_count += 1
                    total_time_spent += pipeline.get("duration_in_seconds", 0)
                    if pipeline.get("creator"):
                        users_list.append(pipeline["creator"].get("nickname"))
                        total_users_list.append(pipeline["creator"].get("nickname"))
                else:
                    url = None
                    break
        else:
            print(f"Error fetching pipelines for {repository_slug}: {response.status_code}\n{response.text}")
            break

    return pipelines, total_pipelines_count, total_time_spent / 60, list(set(users_list))

def save_to_file(data, file_path, mode="w", formatted=True):
    """Save data to a file."""
    try:
        delete_file(file_path)
        with open(file_path, mode) as file:
            content = json.dumps(data, indent=4) if formatted else data
            file.write(content)
        print(f"Data saved to {file_path}")
    except IOError as error:
        print(f"Error saving file: {error}")

def delete_file(file_path):
    """Delete a file."""
    try:
        os.remove(file_path)
        print(f"File {file_path} deleted.")
    except FileNotFoundError:
        print(f"File {file_path} not found.")

def save_report(repositories, file_path, longest_repository_slug=""):
    """Save a report with repository and pipeline data formatted as a table for Slack."""
    try:
        delete_file(file_path)
        TOTAL_MINUTES_HEADER = "Total Minutes"
        TOTAL_PIPELINES_HEADER = "Number of Pipelines"
        AVERAGE_MINUTES_HEADER = "Average Minutes per Pipeline"

        with open(file_path, "w") as file:
            file.write(f"| {'Project'.ljust(len(longest_repository_slug))} | {TOTAL_MINUTES_HEADER} | {TOTAL_PIPELINES_HEADER} | {AVERAGE_MINUTES_HEADER} |\n")

            for repository in repositories:
                slug = repository["slug"]
                pipelines_time_spent = f"{repository['pipelines_time_spent']:.2f}"
                pipelines_count = str(repository["pipelines_count"])
                average_time_spent = (
                    f"{repository['pipelines_time_spent']/repository['pipelines_count']:.2f}"
                    if repository["pipelines_count"]
                    else "0.00"
                )
                if repository["slug"] == longest_repository_slug:
                    file.write(f"| {slug} | {pipelines_time_spent.ljust(len(TOTAL_MINUTES_HEADER))} | {pipelines_count.ljust(len(TOTAL_PIPELINES_HEADER))} | {average_time_spent.ljust(len(AVERAGE_MINUTES_HEADER))} |\n")
                else:
                    file.write(f"| {slug.ljust(len(longest_repository_slug))} | {pipelines_time_spent.ljust(len(TOTAL_MINUTES_HEADER))} | {pipelines_count.ljust(len(TOTAL_PIPELINES_HEADER))} | {average_time_spent.ljust(len(AVERAGE_MINUTES_HEADER))} |\n")

            if total_users_list:
                user_with_most_pipelines = Counter(total_users_list).most_common(1)[0]
                file.write("\n")
                file.write(f"User with the most pipelines: {user_with_most_pipelines[0]} {user_with_most_pipelines[1]} pipelines\n")

            user_time_spent = {}
            for repository in repositories:
                for user in repository["users"]:
                    user_time_spent[user] = user_time_spent.get(user, 0) + repository["pipelines_time_spent"]
            if user_time_spent:
                user_with_most_time = max(user_time_spent.items(), key=lambda x: x[1])
                file.write(f"User with the most time spent: {user_with_most_time[0]} {user_with_most_time[1]:.2f} minutes\n")

        print(f"Report saved to {file_path}")
    except IOError as error:
        print(f"Error saving file: {error}")

def print_execution_completion(total, current):
    """Print the current execution completion."""
    percentage = (current / total) * 100
    print(f"Loading data... {current}/{total}  {percentage:.2f}%")

def main():
    """Main script flow."""
    repositories = fetch_repositories()
    number_of_repositories = len(repositories)

    for index, repository in enumerate(repositories):
        print_execution_completion(number_of_repositories, index)
        pipelines, count, time_spent, users = fetch_pipeline_data(repository["slug"])
        repository.update(
            {
                "pipelines_count": count,
                "pipelines_time_spent": time_spent,
                "users": users,
                "pipelines": pipelines,
            }
        )

    repositories.sort(key=lambda repo: repo["pipelines_time_spent"], reverse=True)
    longest_repository_slug = max(repositories, key=lambda repo: len(repo["slug"]))["slug"]

    if repositories:
        save_to_file(repositories, RAW_OUTPUT_FILE)
        save_report(repositories, REPORT_OUTPUT_FILE, longest_repository_slug)

if __name__ == "__main__":
    main()
