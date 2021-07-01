# cromwell-gwf-log

## Prerequisites

- AWS CLI
- Python `requests` library

## How to Use

For a given task of your WDL/Cromwell workflow, this gets the job ID from AWS Batch, then prints out the log via AWS CloudWatch.

```bash
python get_log.py \
    -k ~/keys/secrets-aws.json \
    -w 66431c43-af28-4df3-a678-7990db3c8a73 \
    -t SCATA.Count
```

In a normal case, a task name consists of three names:

```
Workflow Name + Subworkflow Name + Task Name
```

e.g. `Sharp.Preprocess.CiteSeqCount`

```bash
python get_log.py \
    -k ~/keys/secrets-aws.json \
    -w dc41ed29-0e92-415f-ba6e-d574c80d9960 \
    -t Sharp.Preprocess.CiteSeqCount
```

In the case where a job was restarted and already completed tasks were picked up from the cache, do not specify a workflow name in the task name. For example:

```
Subworkflow Name + Task Name
```

e.g. `Preprocess.CiteSeqCount`

```bash
python get_log.py \
    -k ~/keys/secrets-aws.json \
    -w dc41ed29-0e92-415f-ba6e-d574c80d9960 \
    -t Preprocess.CiteSeqCount
```
