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

import sys

import os_client_config
from oslo_config import cfg
import shade

PROJECT_NAME = 'list-orphaned-resources'
CONF = cfg.CONF
opts = [
  cfg.StrOpt('cloud', help='Managed cloud'),
]
CONF.register_cli_opts(opts)

def check(servicename, resourcename, resources, projects):
    for resource in resources:
        try:
            if hasattr(resource, "tenant_id"):
                project_id = resource.tenant_id
            elif hasattr(resource, "project_id"):
                project_id = resource.project_id
            elif hasattr(resource, "os-vol-tenant-attr:tenant_id"):
                project_id = getattr(resource, "os-vol-tenant-attr:tenant_id")
            else:
                project_id = resource.get("project_id")
        except:
            print dir(resource)

        if hasattr(resource, "id"):
            resource_id = resource.id
        else:
            resource_id = resource.get("id")

        if project_id and project_id not in projects:
            print("%s - %s: %s (project: %s)" % (servicename, resourcename, resource_id, project_id))

if __name__ == '__main__':
    CONF(sys.argv[1:], project=PROJECT_NAME)
    keystone = os_client_config.make_client('identity', cloud=CONF.cloud)
    clients = {
        "cinder": os_client_config.make_client('volume', cloud=CONF.cloud),
        "glance": os_client_config.make_client('image', cloud=CONF.cloud),
        "neutron": os_client_config.make_client('network', cloud=CONF.cloud),
        "nova": os_client_config.make_client('compute', cloud=CONF.cloud),
    }

    domains = [x for x in keystone.domains.list() if x.name != "heat_user_domain"]

    projects = []
    for domain in domains:
        projects_in_domain = [x.id for x in keystone.projects.list(domain=domain.id)]
        projects = projects + projects_in_domain

    check("nova", "server", clients["nova"].servers.list(search_opts={"all_tenants": True}), projects)

    check("neutron", "port", clients["neutron"].list_ports()["ports"], projects)
    check("neutron", "router", clients["neutron"].list_routers()["routers"], projects)
    check("neutron", "network", clients["neutron"].list_networks()["networks"], projects)
    check("neutron", "subnet", clients["neutron"].list_subnets()["subnets"], projects)
    check("neutron", "floatingip", clients["neutron"].list_floatingips()["floatingips"], projects)

    check("glance", "image", clients["glance"].images.list(), projects)

    check("cinder", "volume", clients["cinder"].volumes.list(search_opts={"all_tenants": True}), projects)
    check("cinder", "volume-snapshot", clients["cinder"].volume_snapshots.list(search_opts={"all_tenants": True}), projects)
    check("cinder", "backups", clients["cinder"].backups.list(search_opts={"all_tenants": True}), projects)
