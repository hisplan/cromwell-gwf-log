#!/usr/bin/env python
# coding: utf-8

import argparse
import json
import api


#   "calls": {
#     "Sharp.Preprocess": [
#       {
#         "retryableFailure": false,
#         "executionStatus": "Failed",
#         "subWorkflowMetadata": {
#           "workflowName": "Preprocess",
#           "rootWorkflowId": "36d9d431-02c7-4f2a-99f1-8fb14d412cf1",
#           "calls": {
#             "Preprocess.WhitelistFromSeqcDenseMatrix": [
#               {
#                 "retryableFailure": false,
def handle_call(task: str, call: str, region: str):

    for k, v in call.items():
        for attempt in v:
            if "subWorkflowMetadata" in attempt:
                handle_call(
                    task=k, call=attempt["subWorkflowMetadata"]["calls"], region=region
                )
            else:
                if attempt["executionStatus"] == "Failed":

                    job_id = attempt["jobId"]

                    job = api.get_describe_job(job_id=job_id, region=region)
                    job_name = job["jobName"]
                    print(f"Job Name: {job_name}")

                    log_stream_name = api.get_log_stream_name(job=job)
                    print(f"AWS Batch Log Stream Name: {log_stream_name}")

                    # print("executionStatus", attempt["executionStatus"])
                    # print("failures", attempt["failures"])

                    status, status_reason, container_reason = api.get_job_status(
                        job=job
                    )
                    print(f"Container Status: {status} - {status_reason}")
                    print(container_reason)

                    with open(f"errors/{job_id}-{job_name}.json", "wt") as fout:
                        json.dump(job, fout, indent=4)
                    print()


def main(path_secret, workflow_id, region):

    # get metadata via Swagger
    metadata = api.get_metadata(api.get_secrets(path_secret), workflow_id)

    # print(json.dumps(metadata, indent=2))

    if metadata["status"] != "Failed":
        print("There is no error.")
        exit(0)

    handle_call(task="root", call=metadata["calls"], region=region)


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
        "--region",
        "-r",
        action="store",
        dest="region",
        help="AWS region",
        required=True,
    )

    # parse arguments
    params = parser.parse_args()

    params.workflow_id = params.workflow_id.replace("cromwell-", "")

    return params


if __name__ == "__main__":

    params = parse_arguments()

    # workflow_id = "66431c43-af28-4df3-a678-7990db3c8a73"
    # path_secrets_file = "/Users/chunj/Documents/keys/secrets-aws.json"

    main(params.path_secret, params.workflow_id, params.region)
