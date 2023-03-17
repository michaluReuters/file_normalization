from aws_lambda_powertools import Logger
from model import FFProbe, FFprobeDTO

import json
import os
import boto3

logger = Logger()
s3client = boto3.resource("s3")


@logger.inject_lambda_context(log_event=True)
def handler(event, context):
    event_object = event["Records"][0]["s3"]["object"]["key"]
    event_bucket = event["Records"][0]["s3"]["bucket"]["name"]

    try:
        local_file_name = '/tmp/' + event_object
        s3client.Bucket(event_bucket).download_file(event_object, local_file_name)
        metadata = FFProbe(video_file=local_file_name)

        result = FFprobeDTO()
        result.gather_required_data(metadata)
        result.assign_data_to_proper_destinations()

        cleared = {k: v for k, v in result.data.items() if bool(v)}
        logger.info(f"Cleared fields: {json.dumps(cleared, indent=4)}")
        os.system(f"rm /tmp/{event_object}")
        logger.info(f"Result Data: {result.data}")
        return result.destination_data
    # TODO Also we would need to modify the s3 object metadata with one gathered from this step 17/03/2023
    except Exception as exc:
        logger.info(f"There has been exception. Exception is: {exc}")
