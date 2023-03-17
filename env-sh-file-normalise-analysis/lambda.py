from aws_lambda_powertools import Logger

logger = Logger()


def handler(event, context):
    dict_event = event['detail']
