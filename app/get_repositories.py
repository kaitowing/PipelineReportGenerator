from token import STAR
import requests
import json
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

# Carrega variáveis do .env
load_dotenv()

BASE_URL = os.getenv("BITBUCKET_URL", "https://api.bitbucket.org/2.0")
WORKSPACE = os.getenv("BITBUCKET_WORKSPACE")
USERNAME = os.getenv("BITBUCKET_USERNAME")
APP_PASSWORD = os.getenv("BITBUCKET_APP_PASSWORD")
OUTPUT_FILE = "repositories.json"
IGNORE_FORK = "ubots-default-bot"

# Define o início da semana atual
today = datetime.today()
start_of_week = today - timedelta(days=7)
START_OF_THE_WEEK = start_of_week


def fetch_repositories():
    """Busca todos os repositórios do workspace atualizados a partir do início da semana."""
    url = f"{BASE_URL}/repositories/{WORKSPACE}"
    print(START_OF_THE_WEEK.isoformat())
    params = {
        "fields": "values.slug,values.uuid,values.updated_on,next,values.parent.name",
        "q": f"updated_on >= {START_OF_THE_WEEK.isoformat()}",
        "pagelen": 100,
    }
    repositories = []

    while url:
        print(f"Buscando repositórios de: {url}")
        response = requests.get(url, auth=(USERNAME, APP_PASSWORD), params=params)
        if response.status_code == 200:
            data = response.json()
            for repo in data.get("values", []):
                if not repo["parent"] or repo["parent"]["name"] != IGNORE_FORK:
                    repositories.append(repo)
            url = data.get("next")
            params = None
        else:
            print(f"Erro ao buscar repositórios: {response.status_code}")
            print(response.text)
            break

    return repositories


def fetch_pipelines_count(repo_slug):
    """Busca e conta pipelines criadas a partir do início da semana para um repositório."""
    url = f"{BASE_URL}/repositories/{WORKSPACE}/{repo_slug}/pipelines/"
    params = {
        "fields": "values.created_on,values.completed_on,values.creator.display_name,values.creator.nickname,values.build_seconds_used,next",
        "sort": f"-created_on",
        "pagelen": 100,
    }
    pipelines = []
    count = 0

    while url:
        print(f"Buscando pipelines de: {repo_slug}")
        response = requests.get(url, auth=(USERNAME, APP_PASSWORD), params=params)
        if response.status_code == 200:
            data = response.json()
            if not data.get("values"):
                break

            for pipeline in data.get("values"):
                timestamp = pipeline["created_on"].split("Z")[0][:26]

                if datetime.fromisoformat(timestamp) > START_OF_THE_WEEK:
                    #print(f"Data: {timestamp}")
                    pipelines.append(pipeline)
                    count += 1
                    url = data.get("next")
                    params = None
                else:
                    print(f"Data: {timestamp}")
                    url = None
                    break
        else:
            print(f"Erro ao buscar pipelines para {repo_slug}: {response.status_code}")
            print(response.text)
            break

    return pipelines, count


def save_repositories_to_file(repositories, file_path=OUTPUT_FILE):
    """Salva os dados de repositórios e pipelines em um arquivo JSON."""
    try:
        with open(file_path, "w") as file:
            formatted_data = json.dumps(repositories, indent=4)
            file.write(formatted_data)
        print(f"Repositórios salvos em {file_path}")
    except IOError as e:
        print(f"Erro ao salvar o arquivo: {e}")


def main():
    """Fluxo principal do script."""
    repositories = fetch_repositories()

    # repo = repositories[2]

    # pipelines, count = fetch_pipelines_count(repo["slug"])
    # repo["pipelines"] = pipelines
    # repo["pipelines_count"] = count

    for repo in repositories:
        pipelines, count = fetch_pipelines_count(repo["slug"])
        repo["pipelines"] = pipelines
        repo["pipelines_count"] = count

    if repositories:
        save_repositories_to_file(repositories)


if __name__ == "__main__":
    main()
