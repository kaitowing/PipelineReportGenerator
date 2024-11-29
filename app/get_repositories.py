import requests
import json
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

load_dotenv()

BASE_URL = os.getenv("BITBUCKET_URL", "https://api.bitbucket.org/2.0")
WORKSPACE = os.getenv("BITBUCKET_WORKSPACE")
USERNAME = os.getenv("BITBUCKET_USERNAME")
APP_PASSWORD = os.getenv("BITBUCKET_APP_PASSWORD")
OUTPUT_FILE = "repositories.json"

today = datetime.today()
start_of_week = today - timedelta(days=today.weekday())
START_OF_THE_WEEK = start_of_week.strftime("%Y-%m-%dT%H:%M:%S%z")

def fetch_repositories():
    url = f"{BASE_URL}/repositories/{WORKSPACE}"
    params = {
        "fields": "values.slug,values.uuid,values.updated_on,next",
        "q": f"updated_on > {START_OF_THE_WEEK}",
        "pagelen": 100
    }
    repositories = []

    while url:
        print(f"Buscando repositórios de: {url}")
        response = requests.get(url, auth=(USERNAME, APP_PASSWORD), params=params)
        if response.status_code == 200:
            response_data = response.json()
            repositories.extend(response_data.get("values", []))
            url = response_data.get("next")
            params = None
        else:
            print(f"Erro ao buscar repositórios: {response.status_code}")
            print(response.text)
            break

    return repositories

def save_repositories_to_file(repositories, file_path=OUTPUT_FILE):
    try:
        with open(file_path, "w") as file:
            formatted_data = json.dumps(repositories, indent=4)
            file.write(formatted_data)
        print(f"Repositórios salvos em {file_path}")
    except IOError as e:
        print(f"Erro ao salvar o arquivo: {e}")

def main():
    repositories = fetch_repositories()
    if repositories:
        save_repositories_to_file(repositories)

if __name__ == "__main__":
    main()
