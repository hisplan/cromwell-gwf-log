#!/usr/bin/env python
# coding: utf-8

import argparse
import json
import api


def main(path_secret, workflow_id, task_name, region):

    # get metadata via Swagger
    metadata = api.get_metadata(api.get_secrets(path_secret), workflow_id)

    print(json.dumps(metadata, indent=2))

    job_id = api.get_job_id(metadata=metadata, task_name=task_name)

    print(f"AWS Batch Job ID: {job_id}")

    job = api.get_describe_job(job_id=job_id, region=region)

    log_stream_name = api.get_log_stream_name(job=job)

    print(
        "AWS Batch Log Stream Name: {}".format(
            log_stream_name if log_stream_name else "N/A"
        )
    )

    status, status_reason, container_reason = api.get_job_status(job=job)

    print(f"Container Status: {status} - {status_reason}")
    print(container_reason)

    if log_stream_name:
        exit_code, stdout, stderr = api.get_log_contents(
            log_stream_name=log_stream_name, region=region
        )

        print(stdout)


def parse_arguments():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--key",
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

    parser.add_argument(
        "--region",
        "-r",
        action="store",
        dest="region",
        help="AWS region",
        required=True,
    )

    # parse arguments
    params = parser.parse_args()

    return params


if __name__ == "__main__":

    params = parse_arguments()

    main(params.path_secret, params.workflow_id, params.task_name, params.region)
