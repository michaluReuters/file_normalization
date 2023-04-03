import boto3 as boto3
from aws_lambda_powertools import Logger
from model import TemplateDTO

logger = Logger()
client = boto3.client('events')


@logger.inject_lambda_context(log_event=True)
def handler(event, context):
    input_dict = event['detail']
    source_prefix = input_dict.pop('source_prefix')
    dict_event = combine_resolution(input_dict)

    logger.info(f'DICT = {dict_event}')
    template = TemplateDTO()

    check_required_values(dict_event, template, 'encode_logic', source_prefix)
    check_required_values(dict_event, template, 'output_logic', source_prefix)

    if template.correct_framerate and evaluate_template(template):
        logger.info(f'FRAMERATE CORRECT, ALL OTHER FALSE -> {template.default_template}')
    #     TODO SEND DATA TO OUTPUT 03.04.2023

    elif template.correct_framerate and not evaluate_template(template):
        logger.info(f'FRAMERATE CORRECT, AT LEAST ONE FALSE -> {template.default_template}')
    #     TODO SEND DATA TO OUTPUT 03.04.2023

    elif not template.correct_framerate:
        logger.info(f'FRAMERATE INCORECT -> {template.default_template}')
    #   TODO SEND DATA TO OUTPUT 03.04.2023
    else:
        logger.info(f'LOOKS OK? -> {template.default_template}')


def evaluate_template(template) -> bool:
    if all([not getattr(template, f) for f in dir(template) if
            not callable(getattr(template, f)) and not f.startswith("__")]):
        return True
    else:
        return False


def check_required_values(dict_event, template, logic_input: str, source: {}):
    for i in template.configuration_profile_identifier[logic_input]:

        if i['input_parameter'] == 'x-amz-meta-container-format':
            container_rule = i['rule_type']
            container_format = source.get('prefix').split('.')[1]
            logger.info(f'Container format to be checked is: {container_format}')
            check_value_for_rule(i, container_rule, template, container_format)
            continue

        value_to_compare = dict_event.get(i['input_parameter'])
        if value_to_compare is None:
            continue
        rule_type = i['rule_type']
        check_value_for_rule(i, rule_type, template, value_to_compare)


def check_value_for_rule(i, rule_type, template, value_to_compare):
    if rule_type == 'not_equal':
        logger.info(f'Comparing {value_to_compare.casefold()} for not_equal')
        if not value_to_compare.lower() in [x.lower() for x in i['input_values']]:
            logger.info(f'COMPARED {value_to_compare}')
            logger.info(f'LIST = {[x.lower() for x in i["input_values"]]}')
            template.update_default_template(i['input_parameter'])

    else:
        logger.info(f'Comparing {value_to_compare.casefold()} for equal')
        if value_to_compare.lower() in [x.lower() for x in i['input_values']]:
            template.update_default_template(i['input_parameter'])


def combine_resolution(metadata):
    if "x-amz-meta-video-Resolution-Width" in metadata and "x-amz-meta-video-Resolution-Height" in metadata:
        width = metadata["x-amz-meta-video-Resolution-Width"]
        height = metadata["x-amz-meta-video-Resolution-Height"]
        metadata["x-amz-meta-video-resolution"] = f"{width}x{height}"
        del metadata["x-amz-meta-video-Resolution-Width"]
        del metadata["x-amz-meta-video-Resolution-Height"]
    return metadata
