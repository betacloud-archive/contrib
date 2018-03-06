#!/usr/bin/env python

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os
import sys

import keystoneauth1
import os_client_config
import shade
import yaml

CLOUDNAME = 'service'

cloud = shade.operator_cloud(cloud=CLOUDNAME)
keystone = os_client_config.make_client('identity', cloud=CLOUDNAME)

try:
    keystone.endpoint_filter.add_endpoint_group_to_project(
        endpoint_group=os.environ.get("ENDPOINT_GROUP"),
        project=os.environ.get("PROJECT")
    )
except keystoneauth1.exceptions.http.Conflict:
    pass
