# pyconfig

Essentials for integrating python application config with ansible script

## Installation and usage

First, create and/or activate a suitable python3 virtual env: python >=3.7 required

    pip install https://github.com/huit/pyconfig/archive/v1.0.0.tar.gz

    from pyconfig.pyconfig import Config, Stack, SecretService, get_config

to instantiate a Config object, running locally, reading from the default location and using the AWS SecretsManager:

    Config()
    
to instantiate a Config object, using 'dev', the AWS Parameter Store, and a custom location for config:    

    Config(stack=Stack.DEV, secret_service=SecretService.SSM, ansible_vars_dir_path="/some/valid/path")
    
    class Stack(Enum):
        LOCAL = "local"
        SAND = "sand"
        DEV = "dev"
        TEST = "test"
        STAGE = "stage"
        PROD = "prod"

    # currently these are the only options for aws secrets management
    class SecretService(Enum):
        SSM = "ssm"
        SECRETS_MANAGER = "secretsmanager"

alternately, to pick up the stack from the environment: (must be from list above)
    
    (in shell: % export STACK="dev")
    import os
    Config(stack=Stack(os.environ['STACK']))

to retrieve values:

    get_config().get_value('SOME_KEY')

