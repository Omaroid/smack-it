#! /usr/bin/env python3

"""
author : ygouzerh
date: 26/11/2018

API to manage roles
"""
from boto3 import client, resource
import boto3
import json
from .tagger import Tagger
from ...utils.python.config_parser import Parser

class Role:
    """
        Manage roles
    """

    @staticmethod
    def get_role(name):
        """
            Retrieve a role
        """
        for role in client('iam').list_roles()['Roles']:
            if role['RoleName'] == name:
                return resource('iam').Role(name)
        return None

    @staticmethod
    def get_default_role():
        """
            Retrieve the default role
        """
        config = Parser.parse('instances.ini')
        return Role.get_role(config["INSTANCES"]["role_name"])

    @staticmethod
    def create_default_role():
        """
            Create default role
        """
        config = Parser.parse('instances.ini')
        if Role.get_default_role() is None :
            response = client('iam').create_role(
                RoleName=config["INSTANCES"]["role_name"],
                Description='Give all access to all',
                AssumeRolePolicyDocument='{"Version": "2012-10-17","Statement": {"Effect": "Allow","Principal": { "Service" : "ec2.amazonaws.com" },"Action": "sts:AssumeRole"}}'
            )
            print("We have created the default role")
            default_role_name = response['Role']['RoleName']
            client_iam = boto3.client('iam')
            client_iam.tag_role(
                RoleName=default_role_name,
                Tags=[Tagger.k8s_get_tag(), Tagger.project_get_tag()]
            )
            print("We have attached the role to the project")
            client('iam').attach_role_policy(
                RoleName=Role.get_default_role().role_name,
                PolicyArn="arn:aws:iam::aws:policy/AdministratorAccess"
            )
            print("We have attached the default role to the AdministratorAccess policy")
        else:
            print("The default role was already created")

    @staticmethod
    def create_instance_profile():
        """
            Create instance profile
        """
        config = Parser.parse('instances.ini')
        client('iam').create_instance_profile(
            InstanceProfileName=config["INSTANCES"]["profile_name"]
        )
        print("We have created the default instance profile")
        #print("We have tag the instance profile")
        # instance_profile = Role.get_instance_profile()
        # print(instance_profile)
        # instance_profile_id = instance_profile.id
        # Tagger.attach_on_project(instance_profile_id)
        # Tagger.k8s_attach(instance_profile_id)
        Role.get_instance_profile().add_role(RoleName=config["INSTANCES"]["role_name"])
        print("We have added the default role to the defaut instance profile")

    @staticmethod
    def delete_instance_profile():
        """
            Delete the default instance profile.
            Check if exists
        """
        config = Parser.parse('instances.ini')
        instance_profile = Role.get_instance_profile()
        if instance_profile is not None:
            print("A default instance profile was already created, we need delete it...")
            if Role.get_default_role() is not None :
                for role in instance_profile.roles:
                    print(".....Detach role : ", role.name)
                    client('iam').remove_role_from_instance_profile(InstanceProfileName=config["INSTANCES"]["profile_name"],
                        RoleName=role.name)
                    print(".....Delete role : ", role.name)
                    print("Attached policies")
                    for policy in role.attached_policies.all():
                        print("Detach policy : ", policy)
                        role.detach_policy(
                            PolicyArn=policy.arn
                        )
                    client('iam').delete_role(RoleName=role.name)
                    print("...Role deleted")
            print("...Remove instance profile")
            client('iam').delete_instance_profile(InstanceProfileName=config["INSTANCES"]["profile_name"])
            print("...Default instance deleted")

    @staticmethod
    def get_instance_profile():
        """
            Retrieve the instance profile
            TODO : passes a name in parameter
        """
        config = Parser.parse('instances.ini')
        name = config["INSTANCES"]["profile_name"]
        for instance in client('iam').list_instance_profiles()['InstanceProfiles']:
            if instance['InstanceProfileName'] == name:
                return resource('iam').InstanceProfile(config["INSTANCES"]["profile_name"])
        return None

    @staticmethod
    def init():
        """
            Link a role and an instance profile
        """
        print("Start the creation of the default role")
        Role.create_default_role()
        print("Start the creation of the default instance profile")
        Role.create_instance_profile()

    @staticmethod
    def reset():
        """
            TODO
            Reset all the configuration.
        """
        print("Delete the instance profile and the associated roles")
        Role.delete_instance_profile()
