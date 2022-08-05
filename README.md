# pyconfig

Essentials for integrating python application running locally and/or in a docker container config with ansible script

## Purpose and intended audience 

When using ansible to build and deploy docker containers, for security purposes we would like to populate config values, 
especially secrets, into the operating system so that they are accessible in only that way. Using ansible scripts written
for the purpose will read from a properly formatted _ansible_vars.yml file and populate the created task definition with 
appropriate values in both the 'environment' and 'secrets' sections.

For the 'environment' section, there will be a list of 'name': name / 'value': value pairs.

For the 'secrets' section, there will be a list of 'name': name /'valueFrom': valueFrom pairs, where valueFrom is a 
properly constructed arn for a secret in the secrets manager.

This script will create an appropriately formatted file that can be used to populate the required OS environment 
variables for the application to be run locally (e.g., with `Docker run --env-file .env`)). A user that is logged into
their AWS account with a still-valid token can use this script to pull current values from AWS secrets manager for
appropriately-named secrets; the script is idempotent and can thus be run and re-run as often as required.

## Requirements

    python >=3.7

## Installation and usage

First, create and/or activate a suitable python3 virtual env, then:
```
pip install https://github.com/huit/pyconfig/archive/v2.0.0.tar.gz

from pyconfig.pyconfig import Config, Stack, SecretService
```
to instantiate a Config object, running locally, reading from the default location and using the AWS SecretsManager:
```
Config()
```    
to instantiate a Config object, using 'dev', the AWS Parameter Store, and a custom location for config:    
```
    Config(stack=Stack.DEV, secret_service=SecretService.SSM, ansible_vars_path="./some/valid/path/to/some_yaml_file.yml")
    
    class Stack(Enum):
        SAND = "sand"
        DEV = "dev"
        TEST = "test"
        STAGE = "stage"
        PROD = "prod"

    # currently these are the only options for aws secrets management
    class SecretService(Enum):
        SSM = "ssm"
        SECRETS_MANAGER = "secretsmanager"
```
alternately, to pick up the stack from the environment: (must be from list above)
```    
(in shell: % export STACK="dev")
import os
Config(stack=Stack(stack=os.environ['STACK']))
```

The default file name for storing the vars/values is `.env`

It is also possible to customize the name of the `.env` file as desired:
```
Config(env_file_name=".docker-env")
```

## Project structure

the config files usually reside outside the src directory:
```
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
```

(the precise path for the mounted file may differ from above)

For Stack.DEV, the path to the file used for populating the .env will be `./ansible_vars/dev_ansible_vars.yml`

It is possible to override the ansible_vars_path by supplying the appropriate relative or absolute path to the desired file

## YAML File organization

In order for the values to be read and processed properly, the YAML file must be organized appropriately.
Specifically, it needs to contain at least 2 sections of key/value pairs.
```
    # this will populate the 'secrets' section of the task definition
    target_app_secrets_ref:
    - SOME_SECRET_KEY:  some-identifier-for-aws
      SOME_OTHER_SECRET_KEY: some-other-identifier-for-aws
    
    # this will populate the 'environment' section of the task definition  
    target_app_env:
    - name: SOME_KEY
      value: some value
    - name: SOME_OTHER_KEY
      value: some other value
     
    # additional 'root' key/value pairs may also be used by the ansible script
    successful_response_codes: 200-499
    target_port: 9103
    target_memory_mb: 256  
```

Note the difference in layout for the 3 sections: 

1. the first is a list of `key: value` pairs
2. the second is a 'list of 2-item lists of `key: value` pairs'
3. the third is simply `key: value` pairs at the root level - not in a list

Note also that the script will prepend the stack + "/" to all AWS identifiers. In the example above, for the dev environment,
that would result in looking up `dev/some-identifier-for-aws` and populating that value in the OS with the key `SOME_SECRET_KEY`