#!/usr/bin/env python

# FIXME(berendt): use python3

import random
import string
import sys

from oslo_config import cfg
import os_client_config
import openstack

PROJECT_NAME = 'create-test-project'
CONF = cfg.CONF
opts = [
  cfg.BoolOpt('random', help='Generate random names', default=False),
  cfg.IntOpt('quotamultiplier', help='Quota multiplier', default='1'),
  cfg.StrOpt('cloud', help='Managed cloud', default='service'),
  cfg.StrOpt('domain', help='Domain', default='testbed'),
  cfg.StrOpt('projectname', help='Projectname', default='test-123'),
  cfg.StrOpt('quotaclass', help='Quota class', default='basic'),
  cfg.StrOpt('username', help='Username', default='test-123'),
  cfg.StrOpt('owner', help='Owner of the project', default='operations@betacloud.io')
]
CONF.register_cli_opts(opts)

CONF(sys.argv[1:], project=PROJECT_NAME)
conn = openstack.connect(cloud=CONF.cloud)

if CONF.random:
    username = "test-" + "".join(random.choice(string.ascii_letters) for x in range(8)).lower()
    projectname = "test-" + "".join(random.choice(string.ascii_letters) for x in range(8)).lower()
else:
    username = CONF.username
    projectname = CONF.projectname

password = "".join(random.choice(string.ascii_letters + string.digits) for x in range(16))

# FIXME(berendt): use get_domain
domain = conn.identity.find_domain(CONF.domain)

# FIXME(berendt): use get_project
project = conn.identity.find_project(projectname, domain_id=domain.id)
if not project:
    project = conn.create_project(name=projectname, domain_id=domain.id)

# FIXME(berendt): use openstacksdk
keystone = os_client_config.make_client('identity', cloud=CONF.cloud)
keystone.projects.update(project=project.id, quotaclass=CONF.quotaclass)
keystone.projects.update(project=project.id, quotamultiplier=CONF.quotamultiplier)
keystone.projects.update(project=project.id, has_domain_network="False")
keystone.projects.update(project=project.id, has_public_network="True")
keystone.projects.update(project=project.id, owner=CONF.owner)

user = conn.identity.find_user(username, domain_id=domain.id)
if not user:
    user = conn.create_user(name=username, password=password, default_project=project, domain_id=domain.id)
else:
    conn.update_user(user, password=password)

# FIXME(berendt): check existing assignments
conn.grant_role("_member_", user=user.id, project=project.id, domain=domain.id)
conn.grant_role("heat_stack_owner", user=user.id, project=project.id, domain=domain.id)

print("domain: %s (%s)" % (CONF.domain, domain.id))
print("project: %s (%s)" % (projectname, project.id))
print("user: %s (%s)" % (username, user.id))
print("password: " + password)
