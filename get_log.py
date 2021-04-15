#!/usr/bin/env python
# coding: utf-8

import os
import json
import subprocess
import requests
import argparse
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


def main(path_secret, workflow_id, task_name):

    # get metadata via Swagger
    metadata = get_metadata(get_secrets(path_secret), workflow_id)

    print(json.dumps(metadata, indent=2))

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

    print(job_id)

    # run aws CLI to extract log stream name
    proc = subprocess.Popen(
        ["aws", "batch", "describe-jobs", "--jobs", job_id], stdout=subprocess.PIPE
    )

    stdout, stderr = proc.communicate()

    data = json.loads(stdout.decode())
    log_stream_name = data["jobs"][0]["container"]["logStreamName"]

    print(log_stream_name)

    # run AWS CLI to extract the actual log
    proc = subprocess.Popen(
        "aws logs get-log-events --log-group-name {} --log-stream-name {} | jq .events[].message".format(
            "/aws/batch/job", log_stream_name
        ),
        stdout=subprocess.PIPE,
        shell=True,
    )

    stdout, stderr = proc.communicate()

    print(stdout.decode())


def parse_arguments():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-k",
        action="store",
        dest="path_secret",
        help="path to secret file",
        required=True,
    )

    parser.add_argument(
        "--workflow-id",
        "-w",
        action="store",
        dest="workflow_id",
        help="Workflow ID",
        required=True,
    )

    parser.add_argument(
        "--task-name",
        "-t",
        action="store",
        dest="task_name",
        help="the name of the task",
        required=True,
    )

    # parse arguments
    params = parser.parse_args()

    return params


if __name__ == "__main__":

    params = parse_arguments()

    # workflow_id = "66431c43-af28-4df3-a678-7990db3c8a73"
    # task_name = "SCATA.Count"
    # path_secrets_file = "/Users/chunj/Documents/keys/secrets-aws.json"

    main(params.path_secret, params.workflow_id, params.task_name)
