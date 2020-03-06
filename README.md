# cromwell-aws-log

For a given task of your WDL/Cromwell workflow, get the job ID from AWS Batch, then print out the log via AWS CloudWatch.

```bash
python get_log.py \
    -k ~/Documents/keys/secrets-aws.json \
    -w 66431c43-af28-4df3-a678-7990db3c8a73 \
    -t SCATA.Count
```
