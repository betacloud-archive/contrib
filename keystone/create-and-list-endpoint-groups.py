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
from tabulate import tabulate
import yaml

CLOUDNAME = os.environ.get("CLOUD", "service")

cloud = shade.operator_cloud(cloud=CLOUDNAME)
keystone = os_client_config.make_client("identity", cloud=CLOUDNAME)

existing_endpoint_groups = {x.name: x for x in keystone.endpoint_groups.list()}

changed = False
for service in [x for x in keystone.services.list() if x.name not in existing_endpoint_groups.keys()]:
    for interface in ["public", "admin", "internal"]:
        changed = True
        print("create endpoint %s for service %s (%s)" % (interface, service.name, service.id))
        payload = {
            "name": "%s-%s" % (service.name, interface),
            "filters": {
                "interface": interface,
                "service_id": service.id
            }
        }
        keystone.endpoint_groups.create(**payload)

if changed:
    existing_endpoint_groups = {x.name: x for x in keystone.endpoint_groups.list()}

result = []
for endpoint_group in existing_endpoint_groups:
    result.append([endpoint_group, existing_endpoint_groups[endpoint_group].id])
print(tabulate(result, headers=["endpoint group name", "endpoint group id"], tablefmt="psql"))
