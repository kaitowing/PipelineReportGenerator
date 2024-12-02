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
IGNORE_REPO = os.getenv("IGNORE_REPO", "").split(",")
START_OF_THE_WEEK = datetime.today() - timedelta(days=7)

total_users = []


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
                if repo["slug"] not in IGNORE_REPO and (
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
        "fields": "values.created_on,values.duration_in_seconds,values.creator.nickname,next",
        "sort": "-created_on",
        "pagelen": 100,
    }
    pipelines = []
    total_pipelines = 0
    total_time_spent = 0
    users = []

    while url:
        print(f"Fetching pipelines for {repo_slug}")
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
                    total_time_spent += pipeline.get("duration_in_seconds", 0)
                    if pipeline.get("creator"):
                        users.append(pipeline["creator"].get("nickname"))
                        total_users.append(pipeline["creator"].get("nickname"))
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


def save_report(repositories, file_path, longest_slug=""):
    """Save a report with repository and pipeline data formatted as a table for Slack."""
    try:
        delete_file(file_path)
        TOTAL_MINUTES = "Total de minutos"
        TOTAL_PIPES = "Quantidade de pipes"
        AVERAGE_MINUTES = "Média de minutos"

        with open(file_path, "w") as file:
            # Cabeçalho da tabela
            file.write(
                f"| {'Projeto'.ljust(len(longest_slug))} | {TOTAL_MINUTES} | {TOTAL_PIPES} | {AVERAGE_MINUTES} |\n"
            )

            for repo in repositories:
                # Escreve os dados de cada repositório
                slug = repo["slug"]
                pipelines_time_spent = f"{repo['pipelines_time_spent']:.2f}"
                pipelines_count = str(repo["pipelines_count"])
                average_time_spent = (
                    f"{repo['pipelines_time_spent']/repo['pipelines_count']:.2f}"
                    if repo["pipelines_count"]
                    else "0.00"
                )
                if repo["slug"] == longest_slug:
                    file.write(
                        f"| {slug} | {pipelines_time_spent.ljust(len(TOTAL_MINUTES))} | {pipelines_count.ljust(len(TOTAL_PIPES))} | {average_time_spent.ljust(len(AVERAGE_MINUTES))} |\n"
                    )
                else:
                    file.write(
                        f"| {slug.ljust(len(longest_slug))} | {pipelines_time_spent.ljust(len(TOTAL_MINUTES))} | {pipelines_count.ljust(len(TOTAL_PIPES))} | {average_time_spent.ljust(len(AVERAGE_MINUTES))} |\n"
                    )

            if total_users:
                user_with_most_pipelines = Counter(total_users).most_common(1)[0]
                file.write("\n")
                file.write(
                    f"Usuário com maior número de pipes: {user_with_most_pipelines[0]} {user_with_most_pipelines[1]} pipelines\n"
                )

            user_time_spent = {}
            for repo in repositories:
                for user in repo["users"]:
                    user_time_spent[user] = (
                        user_time_spent.get(user, 0) + repo["pipelines_time_spent"]
                    )
            if user_time_spent:
                user_with_most_time = max(user_time_spent.items(), key=lambda x: x[1])
                file.write(
                    f"Usuário com maior número de minutos: {user_with_most_time[0]} {user_with_most_time[1]:.2f} minutos\n"
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

    repositories.sort(key=lambda repo: repo["pipelines_time_spent"], reverse=True)
    longest_slug = max(repositories, key=lambda repo: len(repo["slug"]))["slug"]

    if repositories:
        save_to_file(repositories, RAW_OUTPUT_FILE)
        save_report(repositories, REPORT_OUTPUT_FILE, longest_slug)


if __name__ == "__main__":
    main()
