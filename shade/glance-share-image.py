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

PROJECT_NAME = 'glance-share-image'
CONF = cfg.CONF
opts = [
    cfg.StrOpt('cloud', help='Managed cloud'),
    cfg.StrOpt('image', required=True, help='Image to share'),
    cfg.StrOpt('target', required=True, help='Target project')
]
CONF.register_cli_opts(opts)

if __name__ == '__main__':
    CONF(sys.argv[1:], project=PROJECT_NAME)

    shade = os_client_config.make_shade(cloud=CONF.cloud)
    glance = os_client_config.make_client('image', cloud=CONF.cloud)

    image = shade.get_image(CONF.image)
    project = shade.get_project(CONF.target)

    member = glance.image_members.create(image.id, project.id)
    glance.image_members.update(image.id, member.member_id, "accepted")
