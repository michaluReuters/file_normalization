import json

from aws_lambda_powertools import Logger

from utils import get_latest_configuration

workflow = 'APP_DEFAULT_WORKFLOW_ID'
template = 'APP_DEFAULT_TEMPLATE_ID'
configuration_profile_identifier = json.loads(get_latest_configuration(workflow))
default_template = json.loads(get_latest_configuration(template))
logger = Logger()


class TemplateDTO:

    def __init__(self):
        self.configuration_profile_identifier = configuration_profile_identifier
        self.default_template = default_template
        self.correct_container = True
        self.correct_codec = True
        self.correct_resolution = True
        self.correct_audio_codec = True
        self.correct_sample_rate = True
        self.correct_framerate = False

    def update_default_template(self, variable):
        self.default_template['Settings']['OutputGroups'] = {'Outputs': {}}
        if variable == 'x-amz-meta-container-format':
            self.update_container()
        elif variable == 'x-amz-meta-video-codec':
            self.update_codec()
        elif variable == "x-amz-meta-video-resolution":
            self.update_resolution()
        elif variable == "x-amz-meta-audio-codec":
            self.update_audio_codec()
        elif variable == "x-amz-meta-audio-sample_rate":
            self.update_sample_rate()
        elif variable == 'x-amz-meta-video-min_framerate':
            self.correct_framerate = True

    def update_container(self):
        logger.info(f'File extension does not match allowed extensions. Assigning extension as MP4.')
        self.default_template['Settings']['OutputGroups']['Outputs']['ContainerSettings'] = {'Container': 'MP4'}
        self.correct_container = False

    def update_codec(self):
        logger.info(f'Codec does not match allowed codecs. Assigning default codec data.')
        with open('./json_files/video_description.json') as file:
            self.default_template['Settings']['OutputGroups']['Outputs']['VideoDescription'] = json.load(file)
            self.correct_codec = False

    def update_resolution(self):
        logger.info(f'Resolution does not match allowed resolutions. Assigning default resolution value.')
        with open('./json_files/resolution.json') as file:
            if 'VideoDescription' in self.default_template['Settings']['OutputGroups']['Outputs']:
                self.default_template['Settings']['OutputGroups']['Outputs']['VideoDescription'].update(json.load(file))
                self.correct_resolution = False
            else:
                self.default_template['Settings']['OutputGroups']['Outputs']['VideoDescription'] = json.load(file)
                self.correct_resolution = False

    def update_audio_codec(self):
        logger.info(f'Audio codec does not match allowed codecs. Assigning default audio codec.')
        with open('./json_files/audio.json') as file:
            self.default_template['Settings']['OutputGroups']['Outputs']['AudioDescription'] = json.load(file)
            self.correct_audio_codec = False

    def update_sample_rate(self):
        logger.info(f'Sample Rate does not match allowed values. Assigning default Sample Rate')
        self.default_template['Settings']['OutputGroups']['Outputs']['AudioDescription']['CodecSettings'][
            'ACCSettings'][
            'SampleRate'] = 48000
        self.correct_sample_rate = False
