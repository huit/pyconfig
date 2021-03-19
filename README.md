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

## Project structure

the config files reside outside the src directory:

    project root
    +-- ansible_vars
    |   +-- dev_ansible_vars.yml
    |   +-- test_ansible_vars.yml
    |   +-- stage_ansible_vars.yml
    |   +-- prod_ansible_vars.yml
    |
    +-- src
    |   +-- somedirectory
    |   +-- app.py
    |
    +-- Dockerfile
    +-- LICENSE
    (etc.)

NOTE: if using within a locally-running Docker container, you will likely need to mount one of the config files, e.g.:

    docker run -v $(pwd)/ansible_vars/dev_ansible_vars.yml:/ansible_vars/dev_ansible_vars.yml your-docker-image-name

(the precise path for the mounted file may differ from above)

## YAML File organization

In order for the values to be read and processed properly, the YAML file must be organized appropriately.
Specifically, it needs to contain at least 2 sections of key/value pairs.

    target_app_secrets_ref:
    - SOME_SECRET_KEY:  some-identifier-for-aws
      SOME_OTHER_SECRET_KEY: some-other-identifier-for-aws
    target_app_env:
    - name: SOME_KEY
      value: some value
    - name: SOME_OTHER_KEY
      value: some other value

Note the difference in layout for the 2 sections: 

1. the first is a list of `key: value` pairs
1. the second is a 'list of 2-item lists of `key: value` pairs'
