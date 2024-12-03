from calendar import c
import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from collections import Counter

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
MAX_DISPLAY_REPOSITORIES = 5

users_map = {}


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
            print(
                f"Error fetching repositories: {response.status_code}\n{response.text}"
            )
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
    repository_users = []
    total_pipelines_count = 0
    total_time_spent = 0

    while url:
        print(f"Fetching pipelines for {repository_slug}")
        response = requests.get(url, auth=(USERNAME, APP_PASSWORD), params=params)
        if response.status_code == 200:
            data = response.json()
            url = data.get("next")

            if not data.get("values"):
                break

            for pipeline in data.get("values", []):
                created_on = datetime.fromisoformat(
                    pipeline["created_on"].split("Z")[0]
                )
                if created_on > START_OF_THE_WEEK:
                    pipelines.append(pipeline)
                    total_pipelines_count += 1
                    total_time_spent += pipeline.get("duration_in_seconds", 0)
                    if pipeline.get("creator"):
                        repository_users.append(pipeline["creator"].get("nickname"))
                        if pipeline["creator"].get("nickname") not in users_map:
                            users_map[pipeline["creator"].get("nickname")] = {
                                "count": 0,
                                "time_spent": 0,
                            }
                        users_map[pipeline["creator"].get("nickname")]["count"] += 1
                        users_map[pipeline["creator"].get("nickname")][
                            "time_spent"
                        ] += pipeline.get("duration_in_seconds", 0) / 60
                else:
                    url = None
                    break
        else:
            print(
                f"Error fetching pipelines for {repository_slug}: {response.status_code}\n{response.text}"
            )
            break

    return (
        pipelines,
        total_pipelines_count,
        total_time_spent / 60,
        repository_users,
    )


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


def save_report(repositories, users, file_path):
    """Save a report with repository and pipeline data formatted as a table for Slack."""
    try:
        delete_existing_report(file_path)
        longest_repository_slug = get_longest_repository_slug(repositories)

        with open(file_path, "w") as file:
            write_report_header(file, longest_repository_slug)
            write_repository_data(file, repositories, longest_repository_slug)
            write_users_summary(file, repositories, users)

        print(f"Report saved to {file_path}")
    except IOError as error:
        print(f"Error saving file: {error}")


def write_users_summary(file, repositories, users):
    user_with_most_pipelines = max(users.items(), key=lambda x: x[1]["count"])
    print(user_with_most_pipelines[0])
    file.write(
        f"\nUser with the most pipelines: {user_with_most_pipelines[0]} {user_with_most_pipelines[1]["count"]} pipelines\n"
    )

    for repository in repositories:
        user_with_most_time_spent = max(users.items(), key=lambda x: x[1]["time_spent"])

    file.write(
        f"User with the most time spent: {user_with_most_time_spent[0]} {user_with_most_time_spent[1]['time_spent']:.2f} minutes\n"
    )


def delete_existing_report(file_path):
    """Delete the report file if it exists."""
    import os

    if os.path.exists(file_path):
        os.remove(file_path)


def get_longest_repository_slug(repositories):
    """Get the longest repository slug length."""
    return max(
        repositories[0:MAX_DISPLAY_REPOSITORIES], key=lambda repo: len(repo["slug"])
    )["slug"]


def write_report_header(file, longest_repository_slug):
    """Write the report header to the file."""
    file.write("# Pipeline Report\n")
    file.write(
        f"Time period: {START_OF_THE_WEEK.isoformat().split("T")[0]} - {datetime.today().isoformat().split("T")[0]}\n"
    )
    file.write(
        f"| {'Project'.ljust(len(longest_repository_slug))} | Total Minutes | Number of Pipelines | Average Minutes per Pipeline |\n"
    )


def write_repository_data(file, repositories, longest_repository_slug):
    """Write repository data to the report file."""
    for index, repository in enumerate(repositories, start=1):
        write_single_repository_row(file, repository, longest_repository_slug)
        if index == MAX_DISPLAY_REPOSITORIES:
            write_other_repositories_summary(
                file, repositories[index:], longest_repository_slug
            )
            break


def write_single_repository_row(file, repository, longest_repository_slug):
    """Write a single repository row to the report."""
    slug = repository["slug"].ljust(len(longest_repository_slug))
    total_minutes = f"{repository['pipelines_time_spent']:.2f}".ljust(
        len("Total Minutes")
    )
    pipelines_count = str(repository["pipelines_count"]).ljust(
        len("Number of Pipelines")
    )
    average_minutes = (
        f"{repository['pipelines_time_spent'] / repository['pipelines_count']:.2f}"
        if repository["pipelines_count"]
        else "0.00"
    ).ljust(len("Average Minutes per Pipeline"))
    file.write(
        f"| {slug} | {total_minutes} | {pipelines_count} | {average_minutes} |\n"
    )


def write_other_repositories_summary(file, other_repositories, longest_repository_slug):
    """Write summary row for remaining repositories."""
    other_count = len(other_repositories)
    other_repositories_name = f"Other ({other_count} repositories)".ljust(
        len(longest_repository_slug)
    )
    total_minutes = sum(repo["pipelines_time_spent"] for repo in other_repositories)
    total_pipelines = sum(repo["pipelines_count"] for repo in other_repositories)
    average_minutes = (
        f"{total_minutes / total_pipelines:.2f}" if total_pipelines else "0.00"
    )

    total_minutes = f"{total_minutes:.2f}".ljust(len("Total Minutes"))
    total_pipelines = str(total_pipelines).ljust(len("Number of Pipelines"))
    average_minutes = average_minutes.ljust(len("Average Minutes per Pipeline"))
    file.write(
        f"| {other_repositories_name} | {total_minutes} | {total_pipelines} | {average_minutes} |\n"
    )


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
        pipelines, count, time_spent, repository_users = fetch_pipeline_data(
            repository["slug"]
        )
        repository.update(
            {
                "pipelines_count": count,
                "pipelines_time_spent": time_spent,
                "pipelines": pipelines,
                "users": repository_users,
            }
        )
    repositories.sort(key=lambda repo: repo["pipelines_time_spent"], reverse=True)

    if repositories:
        save_to_file(repositories, RAW_OUTPUT_FILE)
        save_report(repositories, users_map, REPORT_OUTPUT_FILE)


if __name__ == "__main__":
    main()
