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

import random
import string
import sys

from oslo_config import cfg
from oslo_log import log
import shade

PROJECT_NAME = "instance-spawner"
CONF = cfg.CONF
LOG = log.getLogger(PROJECT_NAME)

opts = [
    cfg.StrOpt('cloud',
               help='Managed cloud'),
]
CONF.register_cli_opts(opts)


def get_image(name):
    result = CLOUD.get_image(name)
    if not result:
        LOG.error("image %s not found" % name)
    return result


def get_flavor(name):
    result = CLOUD.get_flavor(name)
    if not result:
        LOG.error("flavor %s not found" % name)
    return result


def get_network(name):
    result = CLOUD.get_network(name)
    if not result:
        LOG.error("network %s not found" % name)
    return result


def start():
    image = get_image(CONF.command.image)
    flavor = get_flavor(CONF.command.flavor)
    network = get_network(CONF.command.network)

    if not(image and flavor and network):
        LOG.error("ensure existence of requested image, flavor, and network")
    else:
        number = CONF.command.number
        while number % CONF.command.parallel:
            number = number + 1
        for x in range(1, number + 1, CONF.command.parallel):
            name = "%s-%s" % (
                CONF.command.prefix,
                ''.join(random.sample(string.ascii_lowercase, 6)))
            LOG.info("spawning instance(s) %s (%d of %d)" % (
                     name, (x + CONF.command.parallel - 1), number))

            try:
                CLOUD.create_server(
                    name, image=image, flavor=flavor, network=CONF.command.network,
                    key_name=CONF.command.key, wait=True, auto_ip=CONF.command.floating,
                    security_groups=['default'], min_count=CONF.command.parallel,
                    max_count=CONF.command.parallel)
            except shade.OpenStackCloudException as e:
                LOG.error(e)


def add_command_parsers(subparsers):
    parser = subparsers.add_parser('start')
    parser.set_defaults(func=start)
    parser.add_argument('--flavor', required=True,
                        help='Flavor name or ID')
    parser.add_argument('--floating', action='store_true', default=False,
                        help='Assign floating IP address')
    parser.add_argument('--image', required=True,
                        help='Image name or ID')
    parser.add_argument('--key', required=True,
                        help='SSH key name')
    parser.add_argument('--network', required=True,
                        help='Network name or ID')
    parser.add_argument('--number', required=True, type=int,
                        help='Number of instances')
    parser.add_argument('--parallel', required=False, type=int, default=1,
                        help='Spawn in parallel')
    parser.add_argument('--prefix', required=True,
                        help='Instance name prefix')

commands = cfg.SubCommandOpt('command', title='Commands',
                             help='Show available commands.',
                             handler=add_command_parsers)
CONF.register_cli_opts([commands])


if __name__ == '__main__':
    log.register_options(CONF)
    CONF(sys.argv[1:], project=PROJECT_NAME)
    log.set_defaults()
    log.setup(CONF, PROJECT_NAME)
    shade.simple_logging(debug=CONF.debug)
    CLOUD = shade.openstack_cloud(cloud=CONF.cloud)
    CONF.command.func()
