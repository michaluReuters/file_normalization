from aws_lambda_powertools import Logger
from model import FFProbe, FFprobeDTO

import json
import os
import boto3
import subprocess

logger = Logger()
s3client = boto3.resource("s3")


@logger.inject_lambda_context(log_event=True)
def handler(event, context):
    event_object = event["Records"][0]["s3"]["object"]["key"]
    event_bucket = event["Records"][0]["s3"]["bucket"]["name"]

    file_path = 'ffprobe'
    dir_path = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(dir_path, file_path)

    logger.info(f"Wywołanie: {os.system(full_path)}")

    try:
        local_file_name = '/tmp/' + event_object
        s3client.Bucket(event_bucket).download_file(event_object, local_file_name)
        metadata = FFProbe(video_file=local_file_name)
        result = FFprobeDTO()
        result.gather_required_data(metadata)

        cleared = {k: v for k, v in result.data.items() if bool(v)}
        logger.info(f"Cleared fields: {json.dumps(cleared, indent=4)}")
        # add_metadata_to_s3_object(event_object, cleared, event_bucket)
        os.system(f"rm /tmp/{event_object}")
        logger.info(f"Result Data: {result.data}")
        return result.data
    except Exception as exc:
        logger.info(f"There has been exception. Exception is: {exc}")
