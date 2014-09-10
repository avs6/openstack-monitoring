#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Keystone monitoring script for Nagios
#
# Copyright © 2014 
#
# Author: Sofer Athlan-Guyot <sofer.athlan@enovance.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
import sys
import argparse
from keystoneclient.v2_0 import client
from glanceclient.client import Client as Gclient
from glanceclient.common import exceptions
import time
import logging
from datetime import datetime
import tempfile

STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2
STATE_UNKNOWN = 3


class OpenstackUtils:
    def __init__(self, glance_client, keystone_client):
        self.glance_client = glance_client
        self.keystone_client = keystone_client
        self.msgs = []
        self.start = totimestamp()
        self.notifications = ["image_creation_time=%s" % self.start]
        self.performances = []
        self.connection_done = False
        self.image = None
        try:
            self.images = [i
                           for i in self.glance_client.images.list()
                           if i.is_public is False
                           and i.owner == keystone_client.tenant_id]
        except Exception as e:
            script_critical("Cannot connect to glance API: %s\n" % e)

    def get_duration(self):
        return totimestamp() - self.start

    def create_image(self, image_name):
        if not self.msgs:
            try:
                tmp_file = tempfile.NamedTemporaryFile('w+b')
                tmp_file.truncate(1024*1024)
            except Exception as e:
                self.msgs.append("Cannot create file '%s': %s" %
                                 (tmp_file.name, e))
                return
            try:
                self.image = self.glance_client.images.create(
                    name=image_name,
                    disk_format='raw',
                    container_format='bare',
                    data=tmp_file,
                    is_public='false',
                    protected='false')
            except Exception as e:
                self.msgs.append("Cannot create the image %s (%s)"
                                 % (image_name, e))
            try:
                tmp_file.close()
            except Exception as e:
                self.msgs.append("Cannot delete the temporary file %s (%s)"
                                 % (tmp_file.name, e))

    def _image_status(self, image, timeout, count):
        deleted = False
        timer = 0
        while not deleted:
            time.sleep(1)
            if timer >= timeout:
                self.msgs.append(
                    "Could not delete the image %s within %d seconds "
                    % (image.name, timer)
                    + "(created at %s)"
                    % image.created_at)
                break
            timer += 1
            try:
                # the fisrt time imgage.get is trigger while the image
                # has disapeared, there is a nasty output : No
                # handlers could be found for logger
                # "glanceclient.common.http" which ruins the nagios
                # convention.  Adding this get rid of the message.
                logging.raiseExceptions = False
                image.get()
            except exceptions.HTTPNotFound:
                deleted = True
                if image.deleted is True:
                    deleted = True
            except Exception as e:
                self.msgs.append("Cannot delete the image %s (%s)"
                                 % (image.name, e))
                self.performances.append("undeleted_image_%s_%d=%s"
                                         % (image.name,
                                            count,
                                            image.created_at))
                break

    def check_existing_image(self, image_name, delete, timeout=45):
        count = 0
        for i in self.images:
            if i.name == image_name:
                if delete:
                    i.delete()
                    self._image_status(i, timeout, count)
                    self.notifications.append("undeleted_image_%s_%d=%s"
                                              % (i.name, count, i.created_at))
                count += 1
        if count > 0:
            if delete:
                self.notifications.append("Found '%s' present %d time(s)"
                                          % (image_name, count))
            else:
                self.msgs.append(
                    "Found '%s' present %d time(s). " % (image_name, count)
                    + "Won't create test image. "
                    + "Please check and delete.")

    def image_ready(self, timeout):
        if not self.msgs:
            timer = 0
            while self.image.status != "active":
                if self.image.status in ["error"]:
                    self.msgs.append("They were a problem creating the image.")
                    break
                elif timer >= timeout:
                    self.msgs.append(
                        "Cannot create the image: timeout %ds.  Will try to delete anyway."
                        % timeout)
                    break
                time.sleep(1)
                timer += 1
                self.image.get()

    def delete_image(self):
        # we delete it even if they was a problem.  We don't want any
        # leftover. For instance when the creation time out, then the
        # image may be in a queued state.  We delete this.
        if not self.msgs or self.image is not None:
            try:
                self.image.delete()
            except Exception as e:
                self.msgs.append("Problem deleting the image: %s" % e)

    def image_deleted(self, timeout):
        deleted = False
        timer = 0
        while not deleted and not self.msgs:
            time.sleep(1)
            if timer >= timeout:
                self.msgs.append("Could not delete the image within %d seconds"
                                 % timer)
                break
            timer += 1
            try:
                # check comment in _image_status.
                logging.raiseExceptions = False
                self.image.get()
            except exceptions.HTTPNotFound:
                deleted = True
            # TODO(chem): it's seems useless now.  Maybe with the v2
            # client.  Anyway it's harmless so I let it there.
            if self.image.deleted is True:
                deleted = True

    def display_status(self):

        if util.msgs:
            script_critical(", ".join(util.msgs))

        duration = util.get_duration()
        notification = ""
        if util.notifications:
            notification = "(" + ", ".join(util.notifications) + ")"
        performance = ""
        if util.performances:
            performance = " ".join(util.performances)
        print("OK - Glance image created and deleted in %d seconds %s| time=%d %s"
              % (duration, notification, duration, performance))


def script_unknown(msg):
    sys.stderr.write("UNKNOWN - %s (UTC: %s)\n" % (msg, datetime.utcnow()))
    sys.exit(STATE_UNKNOWN)


def script_critical(msg):
    sys.stderr.write("CRITICAL - %s (UTC: %s)\n" % (msg, datetime.utcnow()))
    sys.exit(STATE_CRITICAL)


def collect_args():
    parser = argparse.ArgumentParser(
        description='Check upload of glance image.')
    parser.add_argument('--auth_url', metavar='URL', type=str,
                        required=True,
                        help='Keystone URL')

    parser.add_argument('--username', metavar='username', type=str,
                        required=True,
                        help='username to use for authentication')

    parser.add_argument('--password', metavar='password', type=str,
                        required=True,
                        help='password to use for authentication')

    parser.add_argument('--tenant', metavar='tenant', type=str,
                        required=True,
                        help='tenant name to use for authentication')

    parser.add_argument('--endpoint_url', metavar='endpoint_url', type=str,
                        help='Override the catalog endpoint.')

    parser.add_argument('--endpoint_type', metavar='endpoint_type', type=str,
                        default="publicURL",
                        help='Endpoint type in the catalog request.'
                        + 'Public by default.')

    parser.add_argument('--image_name', metavar='image_name', type=str,
                        help='Name of the image to uplaod.')

    parser.add_argument('--force_delete', action='store_true',
                        help='If matching images are found delete them and add'
                        + 'a notification in the message instead of getting out'
                        + 'in critical state.')

    parser.add_argument('--timeout_delete', metavar='timeout_delete', type=int,
                        default=30,
                        help='Max number of second to delete an existing image'
                        + '(30 by default).')

    parser.add_argument('--timeout', metavar='timeout', type=int,
                        default=30,
                        help='Max number of second to create an image'
                        + '(30 by default)')

    parser.add_argument('--verbose', action='store_true',
                        help='Print requests on stderr.')
    return parser


def connect(args):
    try:
        keystone_client = client.Client(
            username=args.username,
            tenant_name=args.tenant,
            password=args.password,
            auth_url=args.auth_url,
            debug=args.verbose)

        keystone_client.authenticate()
    except Exception as e:
        script_critical("Authentication error: %s\n" % e)

    endpoint = ''
    if not args.endpoint_url:
        endpoint = keystone_client.service_catalog.url_for(
            service_type='image',
            endpoint_type='internalURL')
    else:
        endpoint = args.endpoint_url
    token = keystone_client.service_catalog.get_token()['id']
    glance_client = Gclient('1',
                            endpoint=endpoint,
                            token=token,
                            http_log_debug=args.verbose)
    util = OpenstackUtils(glance_client, keystone_client)

    return util


# python has no "toepoch" method: http://bugs.python.org/issue2736
# now, after checking http://stackoverflow.com/a/16307378,
# and http://stackoverflow.com/a/8778548 made my mind to this approach
def totimestamp(dt=None, epoch=datetime(1970, 1, 1)):
    if not dt:
        dt = datetime.utcnow()
    td = dt - epoch
    # return td.total_seconds()
    return int((td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6)
               / 1e6)

if __name__ == '__main__':
    args = collect_args().parse_args()
    util = connect(args)
    util.check_existing_image(args.image_name,
                              args.force_delete,
                              args.timeout_delete)
    util.create_image(args.image_name)
    util.image_ready(args.timeout)
    util.delete_image()
    util.image_deleted(args.timeout)
    util.display_status()
    sys.exit(STATE_OK)
