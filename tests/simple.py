#!/usr/bin/env python3

import logging
import os
import random
import string
import sys

from oslo_config import cfg
import openstack

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')

PROJECTNAME = 'tests'
CONF = cfg.CONF
opts = [
  cfg.StrOpt('cloud', default='testbed'),
  cfg.StrOpt('flavor', default='1C-1GB-10GB'),
  cfg.StrOpt('image', default='Ubuntu 18.04'),
  cfg.StrOpt('network', default='net-to-public-testbed')
]

CONF.register_cli_opts(opts)
CONF(sys.argv[1:], project=PROJECTNAME)

conn = openstack.connect(cloud=CONF.cloud)

image = conn.compute.find_image(CONF.image)
flavor = conn.compute.find_flavor(CONF.flavor)
network = conn.network.find_network(CONF.network)

name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

logging.info("Create server %s" % name)
server = conn.compute.create_server(
    name=name,
    image_id=image.id,
    flavor_id=flavor.id,
    networks=[{"uuid": network.id}]
)

logging.info("Wait for server %s" % name)
server = conn.compute.wait_for_server(server)

logging.info("Delete server %s" % name)
conn.compute.delete_server(server)
