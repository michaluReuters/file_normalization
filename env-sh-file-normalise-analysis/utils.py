import boto3
import os

appconfig = boto3.client('appconfigdata')


def get_latest_configuration(configuration):
    """
    This function gathers latest configuration in AWS App config

    :return:
        decoded configuration
    """

    token = appconfig.start_configuration_session(
        ApplicationIdentifier=os.environ.get('APP_CONFIG_APP_ID'),
        EnvironmentIdentifier=os.environ.get('APP_ENVIRONMENT'),
        ConfigurationProfileIdentifier=os.environ.get(configuration),
        RequiredMinimumPollIntervalInSeconds=20
    )['InitialConfigurationToken']

    response = appconfig.get_latest_configuration(
        ConfigurationToken=token
    )
    return response['Configuration'].read().decode('utf-8')
