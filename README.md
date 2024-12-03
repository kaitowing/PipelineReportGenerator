# Pipeline Report Generator

This project is a Python script designed to generate a report on repositories and their pipelines within a Bitbucket workspace. The report provides key metrics, including the number of pipelines, total time spent, and information about the users who created the pipelines. It also highlights the user with the most pipelines and the user who spent the most time on pipelines across all repositories.

## Features
- Retrieves all repositories from a Bitbucket workspace that have been updated since the start of the week.
- Collects pipeline data for each repository, including creation date, time spent, and user information.
- Identifies the user who created the most pipelines and the user who spent the most time running pipelines.
- Generates a detailed report in Markdown format.

## Requirements
- Python 3.7+
- Bitbucket account credentials
- The following Python packages:
  - `requests`
  - `python-dotenv`

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
   IGNORE_FORKS=<comma-separated list of forks to ignore>
   IGNORE_REPO=<comma-separated list of repositories to ignore>
   ```

## Usage
To run the script, use the following command:
```sh
python pipeline_report_generator.py
```
The script will generate two output files:
- `report.json`: Contains all the raw data collected about the repositories and their pipelines.
- `report.md`: A human-readable report in Markdown format with details about each repository and its pipelines.

## Report Structure
The generated Markdown report (`report.md`) includes the following information for each repository:
- **Repository**: The name of the repository.
- **Total Minutes Spent**: The total amount of time spent on running pipelines, measured in minutes.
- **Number of Pipelines**: The number of pipelines executed for the repository.
- **Average Minutes per Pipeline**: The average time spent per pipeline.

Additionally, the report includes:
- **User with Most Pipelines**: The user who triggered the most pipelines across all repositories.
- **User with Most Minutes Spent**: The user who spent the most time on pipelines across all repositories.

## Environment Variables
The script uses the following environment variables, which should be configured in a `.env` file:
- `BITBUCKET_URL`: The base URL of the Bitbucket API (default: `https://api.bitbucket.org/2.0`).
- `BITBUCKET_WORKSPACE`: The workspace from which to retrieve repositories.
- `BITBUCKET_USERNAME`: Your Bitbucket username.
- `BITBUCKET_APP_PASSWORD`: Your Bitbucket app password.
- `RAW_OUTPUT_FILE`: The output file for storing raw repository data (`report.json` by default).
- `REPORT_OUTPUT_FILE`: The output file for the Markdown report (`report.md` by default).
- `IGNORE_FORKS`: Comma-separated list of fork repository names to ignore.
- `IGNORE_REPO`: Comma-separated list of repository names to ignore during pipeline analysis.

## Example Output
An example of a generated report:

```markdown
| Project                | Total Minutes | Number of Pipelines | Average Minutes per Pipeline |
| project1               | 1098.55       | 100                 | 10.99                        |
| project2               | 522.43        | 67                  | 7.80                         |
| project3               | 346.38        | 20                  | 17.32                        |
| project4               | 194.77        | 14                  | 13.91                        |
| project5               | 166.27        | 32                  | 5.20                         |
| Other (5 repositories) | 145.50        | 21                  | 6.93                         |

User with the most pipelines: user1 104 pipelines
User with the most time spent: user2 1073.00 minutes
```

## Contributing
If you would like to contribute to this project, please fork the repository and create a feature branch. Pull requests are always welcome.

## License
This project is open source and available under the [MIT License](LICENSE).

## Author
Developed by Arthur Igansi.
