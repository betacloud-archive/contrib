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

from datetime import timedelta, datetime
import logging
import os
import sys
import pytz

from dateutil.parser import *
import jinja2
from oslo_config import cfg
import openstack
import requests
import yaml

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')

PROJECT_NAME = 'list-outdated-resources'
CONF = cfg.CONF
opts = [
  cfg.StrOpt('cloud', help='Managed cloud', default='service'),
  cfg.StrOpt('domainid', help='Domain ID', required=True),
  cfg.StrOpt('projectname', help='Project name, required=True'),
  cfg.IntOpt('threshold', help='Threshold in days', default=30),
  cfg.StrOpt('mailgunapi', default='https://api.mailgun.net/v3/betacloud.io/messages'),
  cfg.StrOpt('mailgunkey', required=False),
  cfg.StrOpt('mailgunfrom', default='Betacloud Operations <noreply@betacloud.io>')
]
CONF.register_cli_opts(opts)

# http://matthiaseisen.com/pp/patterns/p0198/
def render(tpl_path, context):
    path, filename = os.path.split(tpl_path)
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(path or './')
    ).get_template(filename).render(context)

def send_mail(to, payload, mailgunfrom, mailgunapi, mailgunkey):
    logging.info("send mail to %s" % to)
    result = requests.post(
        mailgunapi,
        auth=("api", mailgunkey),
        data={"from": mailgunfrom,
              "to": to,
              "subject": payload["subject"],
              "text": payload["body"]})
    logging.debug(result.text)

if __name__ == '__main__':
    CONF(sys.argv[1:], project=PROJECT_NAME)
    cloud = openstack.connect(cloud=CONF.cloud)
    project = cloud.get_project(CONF.projectname, domain_id=CONF.domainid)

    utc = pytz.UTC
    now = utc.localize(datetime.now())

    threshold = timedelta(days=CONF.threshold)

    for instance in cloud.list_servers(filters={"project_id": project.id}):
        created_at = parse(instance.properties['created_at'])
        expiration = created_at + threshold

        if instance.status == "ACTIVE" and expiration < now:
            user = cloud.get_user(instance.user_id)
            logging.info("instance %s (%s) from %s: %s" % (instance.name, instance.id, user.name, created_at.strftime("%Y-%m-%d %H:%M")))

            if CONF.mailgunkey:
                context = {
                    "type": "instance",
                    "name":  instance.name,
                    "id":  instance.id,
                    "project": project.name
                }
                payload = yaml.load(render("templates/outdated-resource.yml.j2", context))
                send_mail(user.email, payload, CONF.mailgunfrom, CONF.mailgunapi, CONF.mailgunkey)
