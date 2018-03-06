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
import time

import os_client_config
import shade
import yaml

CLOUDNAME = 'service'


def check_quota(project, cloud):

    if "quotamultiplier" in project:
        multiplier = int(project.quotamultiplier)
    else:
        multiplier = 1

    print "check network quota for %s" % project.name
    quotanetwork = cloud.get_network_quotas(project.id)
    quotaupdate = False
    for key in quotaclasses[project.quotaclass]["network"]:
        if key in ["security_group_rule"]:
            tmultiplier = 1
        else:
            tmultiplier = multiplier
        if quotaclasses[project.quotaclass]["network"][key] != quotanetwork[key] * multiplier:
            print "%s [ network / %s ] %d != %d" % (project.name, key, quotaclasses[project.quotaclass]["network"][key], quotanetwork[key] * tmultiplier)
            cloud.set_network_quotas(project.id, **{key: quotaclasses[project.quotaclass]["network"][key] * tmultiplier})

    print "check compute quota for %s" % project.name
    quotacompute = cloud.get_compute_quotas(project.id)
    for key in quotaclasses[project.quotaclass]["compute"]:
        if key in ["injected_file_content_bytes", "metadata_items", "injected_file_path_bytes"]:
            tmultiplier = 1
        else:
            tmultiplier = multiplier
        if quotaclasses[project.quotaclass]["compute"][key] != quotacompute[key] * tmultiplier:
            print "%s [ compute / %s ] %d != %d" % (project.name, key, quotaclasses[project.quotaclass]["compute"][key], quotacompute[key] * tmultiplier)
            cloud.set_compute_quotas(project.id, **{key: quotaclasses[project.quotaclass]["compute"][key] * tmultiplier})

    print "check volume quota for %s" % project.name
    quotavolume = cloud.get_volume_quotas(project.id)
    for key in quotaclasses[project.quotaclass]["volume"]:
        if key in ["per_volume_gigabytes"]:
            tmultiplier = 1
        else:
            tmultiplier = multiplier
        if quotaclasses[project.quotaclass]["volume"][key] != quotavolume[key] * tmultiplier:
            print "%s [ volume %s ] %d != %d" % (project.name, key, quotaclasses[project.quotaclass]["volume"][key], quotavolume[key] * tmultiplier)
            cloud.set_volume_quotas(project.id, **{key: quotaclasses[project.quotaclass]["volume"][key] * multiplier})


def create_network_resources(project, domain):

    domain_name = domain.name.lower()
    project_name = project.name.lower()
    router_name = "router-to-%s-public-%s" % (domain_name, project_name)
    net_name = "net-to-%s-public-%s" % (domain_name, project_name)
    subnet_name = "subnet-to-%s-public-%s" % (domain_name, project_name)

    if domain_name == "default":
        public_net_name = "public"
    else:
        public_net_name = "%s-public" % domain_name

    router = cloud.get_router(router_name)
    attach = False

    if not router:
        public_network_id = cloud.get_network(public_net_name).id
        print "create router for %s" % project.name
        router = cloud.create_router(
            name=router_name,
            ext_gateway_net_id=public_network_id,
            enable_snat=True,
            project_id=project.id,
            availability_zone_hints=["north-1"]
        )
        attach = True

    net = cloud.get_network(net_name)
    if not net:
        print "create network for %s" % project.name
        net = cloud.create_network(net_name, project_id=project.id, availability_zone_hints=["south-1"])

    subnet = cloud.get_subnet(subnet_name)
    if not subnet:
        print "create subnetwork for %s" % project.name
        subnet = cloud.create_subnet(
            net.id,
            tenant_id=project.id,
            subnet_name=subnet_name,
            use_default_subnetpool=True,
            enable_dhcp=True
        )
        attach = True

    if attach:
        cloud.add_router_interface(router, subnet_id=subnet.id)


cloud = shade.operator_cloud(cloud=CLOUDNAME)
with open("etc/quotaclasses.yml", "r") as fp:
    quotaclasses = yaml.load(fp)

project = cloud.get_project(os.environ.get("PROJECT"))
if not project:
    print("project %s does not exist" % os.environ.get("PROJECT"))
    sys.exit(1)

print("prepare project %s" % os.environ.get("PROJECT"))

if "quotaclass" not in project:
    print("quotaclass for project %s not set" % project.name)
else:
    if project.quotaclass not in quotaclasses:
        print("quotaclass %s for project %s not defined" % (project.quotaclass, project.name))
    else:
        check_quota(project, cloud)

domain = cloud.get_domain(project.domain_id)
create_network_resources(project, domain)
