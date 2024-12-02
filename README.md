# Pipeline Report Generator

This project is a Python script that generates a report on repositories and their respective pipelines in a Bitbucket workspace. The report includes the number of pipelines, total time spent, and information about users who created the pipelines. Additionally, it identifies the user with the most pipelines across all repositories.

## Features
- Fetches all repositories from a Bitbucket workspace that have been updated since the start of the week.
- Collects pipeline data for each repository, including creation date, time spent, and user information.
- Identifies the user with the most pipelines across all repositories.
- Generates a detailed report in Markdown format.

## Requirements
- Python 3.7+
- Bitbucket account credentials
- The following Python packages:
  - `requests`
  - `python-dotenv`
  - `collections`

## Installation
1. Clone this repository:
   ```sh
   git clone git@github.com:kaitowing/PipelineReportGenerator.git
   ```
2. Navigate to the project directory:
   ```sh
   cd PipelineReportGenerator
   ```
3. Install the required Python packages:
   ```sh
   pip install -r requirements.txt
   ```
4. Create a `.env` file to set your environment variables:
   ```sh
   BITBUCKET_URL=https://api.bitbucket.org/2.0
   BITBUCKET_WORKSPACE=<your_workspace>
   BITBUCKET_USERNAME=<your_username>
   BITBUCKET_APP_PASSWORD=<your_app_password>
   RAW_OUTPUT_FILE=report.json
   REPORT_OUTPUT_FILE=report.md
   IGNORE_FORKS=<this is a list if you want to ignore any repo coming from a specific fork>
   IGNORE_REPO=<this is a list if you want to ignore any repo from your workspace>
   ```

## Usage
Run the script using Python:
```sh
python pipeline_report_generator.py
```
The script will generate two output files:
- `report.json`: Contains all fetched data about the repositories and their pipelines.
- `report.md`: Contains a readable report in Markdown format with details about each repository and its pipelines.

## Report Structure
The generated Markdown report (`report.md`) includes the following information for each repository:
- **Repository**: The name of the repository.
- **Number of Pipelines**: The number of pipelines run for the repository.
- **Total Time Spent**: The total time spent on pipelines, in minutes.
- **Users who Created Pipelines**: A list of users who triggered the pipelines.

In addition, the report includes:
- **User with Most Pipelines Overall**: The user who triggered the most pipelines across all repositories.

## Environment Variables
The script uses the following environment variables, which should be set in a `.env` file:
- `BITBUCKET_URL`: The base URL of the Bitbucket API (default: `https://api.bitbucket.org/2.0`).
- `BITBUCKET_WORKSPACE`: The workspace from which to fetch repositories.
- `BITBUCKET_USERNAME`: Your Bitbucket username.
- `BITBUCKET_APP_PASSWORD`: Your Bitbucket app password.
- `RAW_OUTPUT_FILE`: The output file for storing raw repository data (`report.json` by default).
- `REPORT_OUTPUT_FILE`: The output file for the Markdown report (`report.md` by default).
- `IGNORE_FORKS`: Comma-separated list of fork repository names to ignore.
- `IGNORE_REPO`: Comma-separated list of repository names to ignore during pipeline analysis.

## Example Output
An example of a generated report in Markdown format:

```markdown
# Repository and Pipeline Report
- **User with Most Pipelines Overall**: user1 (15 pipelines)

## Repository: example-repo
- **Number of Pipelines**: 10
- **Total Time Spent**: 150.25 minutes
- **Users who Created Pipelines**:
  - user1
  - user2

```

## Contributing
If you'd like to contribute to this project, please fork the repository and use a feature branch. Pull requests are welcome.

## License
This project is open source and available under the [MIT License](LICENSE).

## Author
Developed by Arthur Igansi.
