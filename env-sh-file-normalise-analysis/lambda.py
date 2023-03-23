import json
import boto3 as boto3
from aws_lambda_powertools import Logger
from utils import get_latest_configuration

logger = Logger()
client = boto3.client('events')
workflow = 'APP_DEFAULT_WORKFLOW_ID'
template = 'APP_DEFAULT_TEMPLATE_ID'
configuration_profile_identifier = json.loads(get_latest_configuration(workflow))
default_template = json.loads(get_latest_configuration(template))


@logger.inject_lambda_context(log_event=True)
def handler(event, context):
    input_dict = event['detail']
    dict_event = combine_resolution(input_dict)

    logger.info(f'DICT = {dict_event}')

    for i in configuration_profile_identifier['encode_logic']:
        value_to_compare = dict_event.get(i['input_parameter'])
        if value_to_compare is None:
            continue
        rule_type = i['rule_type']

        if rule_type == 'not_equal':
            # if value_to_compare not in i['input_values']:
            if not any(value_to_compare.casefold() == item.casefold() for item in i['input_values']):
                update_default_template(i['input_parameter'])
        else:
            # if value_to_compare in i['input_values']:
            if any(value_to_compare.casefold() == item.casefold() for item in i['input_values']):
                update_default_template(i['input_parameter'])
    logger.info(f"MODIFIED TEMPLATE = {default_template}")


def combine_resolution(metadata):
    if "x-amz-meta-video-Resolution-Width" in metadata and "x-amz-meta-video-Resolution-Height" in metadata:
        width = metadata["x-amz-meta-video-Resolution-Width"]
        height = metadata["x-amz-meta-video-Resolution-Height"]
        metadata["x-amz-meta-video-resolution"] = f"{width}x{height}"
        del metadata["x-amz-meta-video-Resolution-Width"]
        del metadata["x-amz-meta-video-Resolution-Height"]
    return metadata


def update_default_template(variable):
    default_template['Settings']['OutputGroups'] = {'Outputs': {}}
    if variable == 'x-amz-meta-container-format':
        __update_container()
    elif variable == 'x-amz-meta-video-codec':
        __update_codec()
    elif variable == "x-amz-meta-video-resolution":
        __update_resolution()
    elif variable == "x-amz-meta-audio-codec":
        __update_audio_codec()
    elif variable == "x-amz-meta-audio-sample_rate":
        __update_sample_rate()
    pass


def __update_container():
    logger.info(f'File extension does not match allowed extensions. Assigning extension as MP4.')
    default_template['Settings']['OutputGroups']['Outputs']['ContainerSettings'] = {'Container': 'MP4'}


def __update_codec():
    logger.info(f'Codec does not match allowed codecs. Assigning default codec data.')
    with open('./json_files/video_description.json') as file:
        default_template['Settings']['OutputGroups']['Outputs']['VideoDescription'] = json.load(file)


def __update_resolution():
    logger.info(f'Resolution does not match allowed resolutions. Assigning default resolution value.')
    with open('./json_files/resolution.json') as file:
        if bool(default_template['Settings']['OutputGroups']['Outputs']['VideoDescription']):
            default_template['Settings']['OutputGroups']['Outputs']['VideoDescription'].update(json.load(file))
        else:
            default_template['Settings']['OutputGroups']['Outputs']['VideoDescription'] = json.load(file)


def __update_audio_codec():
    logger.info(f'Audio codec does not match allowed codecs. Assigning default audio codec.')
    with open('./json_files/audio.json') as file:
        default_template['Settings']['OutputGroups']['Outputs']['AudioDescription'] = json.load(file)


def __update_sample_rate():
    logger.info(f'Sample Rate does not match allowed values. Assigning default Sample Rate')
    default_template['Settings']['OutputGroups']['Outputs']['AudioDescription']['CodecSettings']['ACCSettings'][
        'SampleRate'] = 48000
