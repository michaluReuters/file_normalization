import json

from aws_lambda_powertools import Logger
from model import FFProbe, FFprobeDTO

import os
import boto3

logger = Logger()
s3client = boto3.resource("s3")
client = boto3.client('events')
LAMBDA_NAME = os.environ["AWS_LAMBDA_FUNCTION_NAME"]

@logger.inject_lambda_context(log_event=True)
def handler(event, context):
    event_object = event["Records"][0]["s3"]["object"]["key"]
    event_bucket = event["Records"][0]["s3"]["bucket"]["name"]

    try:
        local_file_name = '/tmp/' + event_object

        logger.info(f"Looking for S3 object: {event_object} in S3 bucket; {event_bucket}")
        try:
            s3client.Bucket(event_bucket).download_file(event_object, local_file_name)
        except Exception as exc:
            logger.error(f"There was an error while fetching {event_object}. Exception is: {exc}")

        try:
            # Extracting Metadata
            metadata = FFProbe(video_file=local_file_name)
            logger.info(f'METADATA STREAM = {metadata.show_json_format()}')
            result = FFprobeDTO()
            result.gather_required_data(metadata)
            logger.info(f'DATA SEPARATED = {result.data}')
            result.assign_data_to_proper_destinations()

            os.system(f"rm /tmp/{event_object}")
            logger.info(f"Result Data: {result.destination_data}")

            #TODO FOR TEST PURPOSES METHOD BELLOW IS COMMENTED

            # # Replacing Object Metadata
            # s3client.copy_object(
            #     Bucket=event_bucket,
            #     CopySource={'Bucket': event_bucket, 'Key': event_object},
            #     Key=event_object,
            #     Metadata=result.destination_data,
            #     MetadaDirective='REPLACE'
            # )

            # Sending to EventBridge
            data_to_send = json.dumps(result.destination_data)
            response = client.put_events(
                Entries=[
                    {
                        'Source': f"{LAMBDA_NAME}-complete",
                        'Resources': [LAMBDA_NAME],
                        'DetailType': "file-normalise-metadata-extraction-complete",
                        'Detail': data_to_send
                    },
                ]
            )

            logger.info(response)

            return result.destination_data
        except Exception as exc:
            logger.error(f"There was an error while gathering metadata from ffprobe. Exception is: {exc}")
    except Exception as exc:
        logger.info(f"There has been exception. Exception is: {exc}")
