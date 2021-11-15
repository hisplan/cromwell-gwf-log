import json
import subprocess
import requests
from requests.exceptions import HTTPError
from requests.auth import HTTPBasicAuth


def get_secrets(path_secrets_file):

    with open(path_secrets_file, "rt") as fin:
        data = json.loads(fin.read())

    return data


def prep_api_call(secrets):

    api_version = "v1"
    url = secrets["url"]

    # remove a trailing slash
    url = url[:-1] if url.endswith("/") else url
    url = f"{url}/api/workflows/{api_version}"

    auth = HTTPBasicAuth(secrets["username"], secrets["password"])

    return url, auth


def get_metadata(secrets, workflow_id):

    base_url, auth = prep_api_call(secrets)

    try:
        response = requests.get(
            url=f"{base_url}/{workflow_id}/metadata?expandSubWorkflows=true",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            auth=auth,
        )

        # deprecated
        # response = requests.patch(
        #     url=f"{base_url}/{workflow_id}/metadata?expandSubWorkflows=true",
        #     headers={"Content-Type": "application/json", "Accept": "application/json"},
        #     auth=auth,
        # )

        # if response.status_code == 200:
        data = response.json()

        return data

    except HTTPError as err:
        print(err)


def get_job_id(metadata, task_name):

    # extract job ID
    keys = task_name.split(".")
    if len(keys) == 2:
        # e.g. Sharp.CiteSeqCount
        job_id = metadata["calls"][task_name][0]["jobId"]
    elif len(keys) == 3:
        # has one subworkflow
        # e.g. Sharp.Preprocess.CiteSeqCount
        key1 = keys[0] + "." + keys[1]
        key2 = keys[1] + "." + keys[2]
        job_id = metadata["calls"][key1][0]["subWorkflowMetadata"]["calls"][key2][0][
            "jobId"
        ]

    return job_id


def get_describe_job(job_id: str, region: str):

    # run aws CLI to extract log stream name
    proc = subprocess.Popen(
        [
            "aws",
            "batch",
            "describe-jobs",
            "--jobs",
            job_id,
            "--region",
            region,
            "--output",
            "json",
        ],
        stdout=subprocess.PIPE,
    )

    stdout, stderr = proc.communicate()

    data = json.loads(stdout.decode())

    if len(data["jobs"]) == 0:
        print(
            f"AWS Batch Job ID {job_id} returned nothing. Maybe the job data has been erased?"
        )
        exit(1)

    job = data["jobs"][0]

    return job


def get_log_stream_name(job):

    if not "logStreamName" in job["container"]:
        return None

    log_stream_name = job["container"]["logStreamName"]

    return log_stream_name


def get_job_status(job):

    status = job["status"]

    # might not be available
    status_reason = job["statusReason"] if "statusReason" in job else "n/a"
    container_reason = (
        job["container"]["reason"] if "reason" in job["container"] else ""
    )

    return status, status_reason, container_reason


def get_log_contents(log_stream_name: str, region: str):

    # run AWS CLI to extract the actual log
    proc = subprocess.Popen(
        "aws logs get-log-events --log-group-name {} --log-stream-name {} --region {} --output json | jq .events[].message".format(
            "/aws/batch/job", log_stream_name, region
        ),
        stdout=subprocess.PIPE,
        shell=True,
    )

    stdout, stderr = proc.communicate()

    stdout = stdout.decode()

    if stderr:
        stderr = stderr.decode()

    return proc.returncode, stdout, stderr
