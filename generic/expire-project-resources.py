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


# imports

from datetime import timedelta, datetime
import os
import pytz

from dateutil.parser import *
import jinja2
import os_client_config
import requests
import shade
import yaml


# configuration

CLOUDNAME = os.environ.get("CLOUDNAME", "service")

PROJECTNAME = os.environ.get("PROJECTNAME", "sandbox")
DOMAINNAME = os.environ.get("DOMAINNAME", "Default")

MAILGUNKEY = os.environ.get("MAILGUNKEY", None)
MAILGUNAPI = os.environ.get("MAILGUNAPI", "https://api.mailgun.net/v3/betacloud.io/messages")
MAILGUNFROM = os.environ.get("MAILGUNFROM", "Betacloud Sag Wagon <noreply@betacloud.io>")

DELETION_TEMPLATE = os.environ.get("DELETION_TEMPLATE", "etc/expiration-deletion.yml.j2")
EXPIRATION_TEMPLATE = os.environ.get("EXPIRATION_TEMPLATE", "etc/expiration-reminder.yml.j2")
EXPIRATION_TIME = timedelta(hours=os.environ.get("EXPIRATION_TIME", 72))
MAX_EXPIRATION_TIME = timedelta(hours=os.environ.get("MAX_EXPIRATION_TIME", 144))

REMINDER_TIME = timedelta(hours=os.environ.get("REMINDER_TIME", 24))
NEXT_EXPIRATION_TIME = timedelta(hours=os.environ.get("NEXT_EXPIRATION_TIME", 24))


# helper

TRUE = ["Yes", "yes", "True", "true"]
FALSE = ["No", "no", "False", "false"]

# http://matthiaseisen.com/pp/patterns/p0198/
def render(tpl_path, context):
    path, filename = os.path.split(tpl_path)
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(path or './')
    ).get_template(filename).render(context)


def send_mail(to, payload):
    result = requests.post(
        MAILGUNAPI,
        auth=("api", MAILGUNKEY),
        data={"from": MAILGUNFROM,
              "to": to,
              "subject": payload["subject"],
              "text": payload["body"]})
    print result.text


# preparations

cloud = shade.openstack_cloud(cloud=CLOUDNAME)
compute = os_client_config.make_client("compute", cloud=CLOUDNAME)

result = cloud.get_domain(name_or_id=DOMAINNAME)
domain_id = result.id

result =  cloud.get_project(PROJECTNAME, domain_id=domain_id)
project_id = result.id

utc = pytz.UTC
now = utc.localize(datetime.now())


# logic

result = cloud.search_servers(filters={"project_id": project_id}, all_projects=True)

for server in result:

    delete_server = False
    created_at = parse(server.created_at)
    lifetime = now - created_at

    if not "expiration_datetime" in server.metadata.keys():
        expiration_datetime = now + EXPIRATION_TIME
        try:
            compute.servers.set_meta_item(server, "expiration_datetime", str(expiration_datetime))
            print("set expiration_datetime %s for new instance %s" % (expiration_datetime, server.id))
        except:
            pass
    else:
        expiration_datetime = parse(server.metadata.expiration_datetime)

        try:
            expiration_datetime - REMINDER_TIME < now
        except:
            expiration_datetime = pytz.utc.localize(expiration_datetime)

    if (MAILGUNKEY and
        expiration_datetime - REMINDER_TIME < now and
        ("expiration_reminder" in server.metadata.keys() and server.metadata.expiration_reminder not in TRUE)):
        user = cloud.get_user(name_or_id=server.user_id, domain_id=domain_id)
        print("reminder for instance %s is sent to %s (%s)" % (server.id, user.email, lifetime))
        context = {
            "type": "instance",
            "name":  server.name,
            "id":  server.id,
            "lifetime": lifetime,
            "expiration_datetime": expiration_datetime.strftime("%Y-%m-%d %H:%M"),
            "next_expiration_datetime": (expiration_datetime + NEXT_EXPIRATION_TIME).strftime("%Y-%m-%d %H:%M"),
            "project": PROJECTNAME,
            "max_expiration_time": str(MAX_EXPIRATION_TIME).split(" ", 1)[0],
            "reminder_time": str(REMINDER_TIME).split(" ", 1)[0],
            "next_expiration_time": str(NEXT_EXPIRATION_TIME).split(" ", 1)[0]
        }
        payload = yaml.load(render(EXPIRATION_TEMPLATE, context))
        send_mail(user.email, payload)
        compute.servers.set_meta_item(server, "expiration_reminder", str(True))

    elif expiration_datetime < now:
        print("instance %s has reached the desired lifetime (%s)" % (server.id, lifetime))
        delete_server = True

    elif expiration_datetime > created_at + MAX_EXPIRATION_TIME:
        print("instance %s has reached the maximum possible lifetime (%s)" % (server.id, lifetime))
        delete_server = True

    else:
        print("instance %s is within the possible lifetime: %s (%s remaining)" % (server.id, expiration_datetime, expiration_datetime - now))

    if delete_server:
        print("instance %s is deleted" % server.id)
        compute.servers.unlock(server)
        compute.servers.force_delete(server)

        if MAILGUNKEY:
            user = cloud.get_user(name_or_id=server.user_id, domain_id=domain_id)
            print("information about deletion of %s is sent to %s (%s)" % (server.id, user.email, lifetime))
            context = {
                "type": "instance",
                "name":  server.name,
                "id":  server.id,
                "lifetime": lifetime,
                "expiration_datetime": expiration_datetime.strftime("%Y-%m-%d %H:%M"),
                "project": PROJECTNAME
            }
            payload = yaml.load(render(DELETION_TEMPLATE, context))
            send_mail(user.email, payload)
