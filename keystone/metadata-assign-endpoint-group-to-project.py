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

CLOUDNAME = 'service'

# openstack --os-cloud service project set --property has_cinder=True testbed
# openstack --os-cloud service project set --property has_glance=True testbed
# openstack --os-cloud service project set --property has_heat=True testbed
# openstack --os-cloud service project set --property has_keystone=True testbed
# openstack --os-cloud service project set --property has_mistral=True testbed
# openstack --os-cloud service project set --property has_neutron=True testbed
# openstack --os-cloud service project set --property has_nova=True testbed

BASE_ENDPOINT_GROUPS = {
    "has_cinder": ["cinder-public", "cinderv2-public", "cinderv3-public"],
    "has_glance": ["glance-public"],
    "has_heat": ["heat-public", "heat-cfn-public"],
    "has_keystone": ["keystone-public"],
    "has_mistral": ["mistral-public"],
    "has_neutron": ["neutron-public"],
    "has_nova": ["nova-public", "nova_legacy-public"],
}

cloud = shade.operator_cloud(cloud=CLOUDNAME)
keystone = os_client_config.make_client('identity', cloud=CLOUDNAME)

try:
    project = keystone.projects.get(project=os.environ.get("PROJECT"))
except keystoneauth1.exceptions.http.NotFound:
    print("project %s not found" % os.environ.get("PROJECT"))
    sys.exit(1)

existing_endpoint_groups = {x.name: x for x in keystone.endpoint_groups.list()}

for group in [x for x in project.to_dict() if x.startswith("has_") and x in BASE_ENDPOINT_GROUPS]:
    if project.to_dict()[group] in ["True", "true", "Yes", "yes"]:
        for endpoint in BASE_ENDPOINT_GROUPS[group]:
            print("assign endpoint group %s to project %s" % (endpoint, os.environ.get("PROJECT")))
            try:
                keystone.endpoint_filter.add_endpoint_group_to_project(
                    endpoint_group=existing_endpoint_groups[endpoint].id,
                    project=os.environ.get("PROJECT")
                )
            except keystoneauth1.exceptions.http.Conflict:
                pass
    elif project.to_dict()[group] in ["False", "false", "No", "no"]:
        for endpoint in BASE_ENDPOINT_GROUPS[group]:
            print("unassign endpoint group %s from project %s" % (endpoint, os.environ.get("PROJECT")))
            try:
                keystone.endpoint_filter.delete_endpoint_group_from_project(
                    endpoint_group=existing_endpoint_groups[endpoint].id,
                    project=os.environ.get("PROJECT")
                )
            except keystoneauth1.exceptions.http.NotFound:
                pass
    else:
        print("project %s has wrong value %s for %s" % (os.environ.get("PROJECT"), project.to_dict()[group], group))
