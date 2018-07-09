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

import neutronclient
import os_client_config
import shade
import yaml

CLOUDNAME = os.environ.get("CLOUDNAME", "service")

PROJECT = os.environ.get("PROJECT", None)
if not PROJECT:
    print("PROJECT not specified")
PROJECT = PROJECT.rstrip()

def check_quota(project, cloud):

    if "quotamultiplier" in project:
        multiplier = int(project.quotamultiplier)
    else:
        multiplier = 1

    if "quotamultiplier_storage" in project:
        multiplier_storage = int(project.quotamultiplier_storage)
    else:
        multiplier_storage = multiplier

    if "quotamultiplier_compute" in project:
        multiplier_compute = int(project.quotamultiplier_compute)
    else:
        multiplier_compute = multiplier

    if "quotamultiplier_network" in project:
        multiplier_network = int(project.quotamultiplier_network)
    else:
        multiplier_network = multiplier

    print("check network quota for %s" % project.name)
    quotanetwork = cloud.get_network_quotas(project.id)
    for key in quotaclasses[project.quotaclass]["network"]:
        if quotaclasses[project.quotaclass]["network"][key] * multiplier_network != quotanetwork[key]:
            print("%s [ network / %s ] %d != %d" % (project.name, key, quotaclasses[project.quotaclass]["network"][key] * multiplier_network, quotanetwork[key]))
            cloud.set_network_quotas(project.id, **{key: quotaclasses[project.quotaclass]["network"][key] * multiplier_network})

    print("check compute quota for %s" % project.name)
    quotacompute = cloud.get_compute_quotas(project.id)
    for key in quotaclasses[project.quotaclass]["compute"]:
        if key in ["injected_file_content_bytes", "metadata_items", "injected_file_path_bytes"]:
            tmultiplier = 1
        else:
            tmultiplier = multiplier_compute
        if quotaclasses[project.quotaclass]["compute"][key] * tmultiplier != quotacompute[key]:
            print("%s [ compute / %s ] %d != %d" % (project.name, key, quotaclasses[project.quotaclass]["compute"][key] * tmultiplier, quotacompute[key]))
            cloud.set_compute_quotas(project.id, **{key: quotaclasses[project.quotaclass]["compute"][key] * tmultiplier})

    print("check volume quota for %s" % project.name)
    quotavolume = cloud.get_volume_quotas(project.id)
    for key in quotaclasses[project.quotaclass]["volume"]:
        if key in ["per_volume_gigabytes"]:
            tmultiplier = 1
        else:
            tmultiplier = multiplier_storage
        if quotaclasses[project.quotaclass]["volume"][key] * tmultiplier != quotavolume[key]:
            print("%s [ volume %s ] %d != %d" % (project.name, key, quotaclasses[project.quotaclass]["volume"][key] * tmultiplier, quotavolume[key]))
            cloud.set_volume_quotas(project.id, **{key: quotaclasses[project.quotaclass]["volume"][key] * tmultiplier})


def create_network_resources(project, domain):

    if "quotamultiplier" in project:
        multiplier = int(project.quotamultiplier)
    else:
        multiplier = 1

    if "quotamultiplier_network" in project:
        multiplier_network = int(project.quotamultiplier_network)
    else:
        multiplier_network = multiplier

    if not multiplier_network:
        return

    domain_name = domain.name.lower()
    project_name = project.name.lower()

    if "has_public_network" in project and project.has_public_network.lower() in ["true", "yes"]:
        net_name = "net-to-public-%s" % project_name
        router_name = "router-to-public-%s" % project_name
        subnet_name = "subnet-to-public-%s" % project_name
        create_network_with_router(project, net_name, subnet_name, router_name, "public")

    if "domain_name" != "default" and "has_domain_network" in project and project.has_domain_network.lower() in ["true", "yes"]:
        net_name = "net-to-%s-public-%s" % (domain_name, project_name)
        router_name = "router-to-%s-public-%s" % (domain_name, project_name)
        subnet_name = "subnet-to-%s-public-%s" % (domain_name, project_name)
        create_network_with_router(project, net_name, subnet_name, router_name, "%s-public" % domain_name)


def create_network_with_router(project, net_name, subnet_name, router_name, public_net_name):
    try:
        public_net = cloud.get_network(public_net_name)
        neutron.create_rbac_policy({'rbac_policy': {
            'target_tenant': project.id,
            'action': 'access_as_external',
            'object_type': 'network',
            'object_id': public_net.id
        }})
    except neutronclient.common.exceptions.Conflict:
        pass

    router = cloud.get_router(router_name)
    attach = False

    if not router:
        public_network_id = cloud.get_network(public_net_name).id
        print("create router for %s (%s)" % (project.name, public_net_name))
        router = cloud.create_router(
            name=router_name,
            ext_gateway_net_id=public_network_id,
            enable_snat=True,
            project_id=project.id
        )
        attach = True

    net = cloud.get_network(net_name)
    if not net:
        print("create network for %s (%s)" % (project.name, public_net_name))
        net = cloud.create_network(net_name, project_id=project.id)

    subnet = cloud.get_subnet(subnet_name)
    if not subnet:
        print("create subnetwork for %s (%s)" % (project.name, public_net_name))
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
neutron = os_client_config.make_client("network", cloud=CLOUDNAME)

with open("etc/quotaclasses.yml", "r") as fp:
    quotaclasses = yaml.load(fp)

project = cloud.get_project(PROJECT)
if not project:
    print("project %s does not exist" % PROJECT)
    sys.exit(1)

print("prepare project %s" % PROJECT)

if "quotaclass" not in project:
    print("quotaclass for project %s not set" % project.name)
else:
    if project.quotaclass not in quotaclasses:
        print("quotaclass %s for project %s not defined" % (project.quotaclass, project.name))
    else:
        check_quota(project, cloud)

        if project.quotaclass not in ["default", "service"]:
            domain = cloud.get_domain(project.domain_id)
            create_network_resources(project, domain)
