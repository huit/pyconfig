#!/usr/bin/env python3

import yaml
import os
import boto3
import base64
import json
import logging

from enum import Enum
from os import linesep
from os.path import exists

from botocore.exceptions import ClientError


#============================================================================================
# Globals
#============================================================================================
NO_VALUE_FOUND = "NO VALUE FOUND"


class Stack(Enum):
    LOCAL = "local"
    SAND = "sand"
    DEV = "dev"
    TEST = "test"
    STAGE = "stage"
    PROD = "prod"


class SecretService(Enum):
    SSM = "ssm"
    SECRETS_MANAGER = "secretsmanager"


class Config:
    """
    All pyconfig values pulled from the OS environment
    For local deployment, will populate OS environ with variables/values pulled from dev_ansible_vars.yml,
    adding secrets pulled from parameter store or secretsmanager, depending on self.SecretService
    For other environments, variables and values are pumped into the OS environ by the AWS task definition
    """

    APP_ENV_KEY = 'target_app_env'
    SECRETS_REF_KEY = 'target_app_secrets_ref'

    def __init__(self, stack: Stack = Stack.LOCAL,
                 secret_service: SecretService = SecretService.SECRETS_MANAGER,
                 ansible_vars_path: str = "./ansible_vars/dev_ansible_vars.yml"):
        """
                 Retrieve values from OS environment or read from pyconfig files
        :param stack: defaults to Stack.LOCAL
        :param secret_service: defaults to SecretService.SECRETS_MANAGER
        :param ansible_vars_dir_path: defaults to './ansible_vars'
        :param logging_level: defaults to logging.CRITICAL
        :param logging_format: defaults to None
        """
        self.stack = stack
        self.config_stack = Stack.DEV if stack == Stack.LOCAL else stack
        self.ansible_vars_path = ansible_vars_path
        self.secret_service = secret_service
        self.value_store = {}
        self.env_file_name = ".env"
        open(self.env_file_name, 'w').close()  # empty the .env file
        self.populate_os_env()
        self.git_ignore_path = "./.gitignore"
        self.update_git_ignore()

    def update_git_ignore(self):
        """
        adds env file (containing secrets) to .gitignore if necessary
        :return:
        """
        if exists(self.git_ignore_path):
            with open(self.git_ignore_path, 'r') as f:
                lines = f.readlines()
                f.close()
        else:
            lines = []
        if f"{self.env_file_name}\n" not in lines:
            with open(self.git_ignore_path, "a") as git_ignore:
                git_ignore.write(f"\n# pyconfig added generated {self.env_file_name} file \n{self.env_file_name} to protect secrets \n")
                git_ignore.close()

    def populate_os_env(self):
        app_dict = self.populate_app_dict()
        self.populate_secrets(app_dict)
        self.populate_vars(app_dict)
        self.populate_plain_vars(app_dict)

    def populate_app_dict(self):
        yaml_file_name = self.ansible_vars_path
        with open(yaml_file_name) as yaml_file_obj:
            app_dict = yaml.load(yaml_file_obj, Loader=yaml.FullLoader)
        return app_dict

    def populate_secrets(self, app_dict):
        """
        Reads key/value pairs from app_dict
        target_app_secrets_ref:
          - SOME_SECRET_KEY:  <identifier for a valid aws secret stored in either parameter store or secrets manager>
            SOME_OTHER_SECRET_KEY: <identifier for a valid aws secret stored in either parameter store or secrets manager>
            STILL_OTHER_SECRET_KEY: <identifier for a valid aws secret stored in either parameter store or secrets manager>

        this will populate the OS environ with variables names for the keys, with values looked up from the selected SecretService
        :param app_dict:
        :return:
        """
        print(f"======= populating secrets from AWS {self.secret_service.value} =======")
        try:
            with open(self.env_file_name, 'a') as env_file:
                var_dict = app_dict.get(self.SECRETS_REF_KEY)[0]
                if var_dict is None or len(var_dict.keys()) == 0:
                    print("Secrets section of config appears to be missing")
                else:
                    for k, v in var_dict.items():
                        secret_value = f"{self.get_secret_value(v)}"
                        env_file.write(f"{k}={secret_value.replace(linesep, '').replace('  ','')}\n")

        except yaml.YAMLError as exc:
            print.exception(f"ERROR: {exc}")

    def populate_vars(self, app_dict):
        """
        reads key value pairs from 'target_app_env' in app_dict, and populates those pairs in the OS environ
        for example:
        target_app_env:
          - name: SOME_KEY
            value: <some value>
          - name: SOME_OTHER_KEY
            value: <some other value>
          - name: STILL_ANOTHER_KEY
            value: <still another value>

        :param app_dict:
        :return:
        """
        print(f"======= parsing pyconfig vars and values =======")
        try:
            with open(self.env_file_name, 'a') as env_file:
                values_list = app_dict.get(self.APP_ENV_KEY)
                if values_list is None or len(values_list) == 0:
                    print("Secrets section of config appears to be missing")
                else:
                    for item in values_list:
                        for key, value in item.items():
                            if key == "name":
                                var_name = value
                            if key == "value":
                                var_value = f"{value}"
                        env_file.write(f"{var_name}={var_value.replace(linesep, '')}\n")
        except yaml.YAMLError as exc:
            print.exception(f"ERROR: {exc}")

    def populate_plain_vars(self, app_dict):
        print(f"======= parsing OTHER pyconfig vars and values =======")
        try:
            with open(self.env_file_name, 'a') as env_file:
                for k, v in app_dict.items():
                    if k not in [self.APP_ENV_KEY, self.SECRETS_REF_KEY] and v is not None:
                        env_file.write(f"{k}={v}\n")

        except Exception as err:
            print.exception(f"ERROR: {exc}")

    def get_secret(self, name):
        secret_name = name
        session = boto3.session.Session()
        region_name = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        client = session.client(service_name="secretsmanager", region_name=region_name)
        try:
            get_secret_value_response = client.get_secret_value(SecretId=secret_name)
            if "SecretString" in get_secret_value_response:
                secret = get_secret_value_response["SecretString"]
            else:
                secret = base64.b64decode(get_secret_value_response["SecretBinary"])
        except ClientError as error:
            print("ERROR: Lookup " + secret_name + ": " + str(error))
            secret = error
        return secret

    def get_ssm_param(self, name):
        """
         Retrieve a parameter from SSM
         """
        ssm_client = boto3.client('ssm')
        print(f"param name = {name}")
        parameter = ssm_client.get_parameter(
            Name=name,
            WithDecryption=True)
        return parameter['Parameter']['Value']

    def get_secret_value(self, name):
        """
        get the value from env if not in the env get the value from secret manager and add it to the dictionary
        :param name:
        :return:
        """
        if self.secret_service == SecretService.SECRETS_MANAGER:
            l_secret = os.environ.get(name, self.get_secret(self.config_stack.value + "/" + name))
        elif self.secret_service == SecretService.SSM:
            l_secret = os.environ.get(name, self.get_ssm_param(name))

        if l_secret is not None:
            return l_secret
        else:
            return NO_VALUE_FOUND


Config()