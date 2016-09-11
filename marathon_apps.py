#! /usr/bin/python
#
# Copyright 2015 Kevin Lynch
# Copyright 2016 Moz, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
import base64
import collectd
import json
import numbers
import requests

MARATHON_HOST = "localhost"
MARATHON_PORT = 8080
MARATHON_USER = None
MARATHON_PASS = None
MARATHON_URL = ""
VERBOSE_LOGGING = False

def configure_callback(conf):
    """Received configuration information"""
    global MARATHON_HOST, MARATHON_PORT, MARATHON_URL, VERBOSE_LOGGING
    global MARATHON_USER, MARATHON_PASS
    for node in conf.children:
        if node.key == 'Host':
            MARATHON_HOST = node.values[0]
        elif node.key == 'Port':
            MARATHON_PORT = int(node.values[0])
        elif node.key == 'User':
            MARATHON_USER = node.values[0]
        elif node.key == 'Pass':
            MARATHON_PASS = node.values[0]
        elif node.key == 'Verbose':
            VERBOSE_LOGGING = bool(node.values[0])
        else:
            collectd.warning('marathon_apps plugin: Unknown config key: %s.' % node.key)

    MARATHON_URL = "http://" + MARATHON_HOST + ":" + str(MARATHON_PORT) + "/v2/apps"

    log_verbose('Configured with host=%s, port=%s, url=%s' % (MARATHON_HOST, MARATHON_PORT, MARATHON_URL))


def read_callback():
    """Parse stats response from Marathon"""
    log_verbose('Read callback called')
    try:
        base64string = ""
        if MARATHON_USER is not None:
	    base64string = base64.encodestring('%s:%s' % (MARATHON_USER, MARATHON_PASS)).replace('\n', '')
        headers = {}
        headers["Authorization"] = "Basic {}".format(base64string)
        r = requests.get(MARATHON_URL, headers=headers)
        data = json.loads(r.text)
        for app in data.get("apps"):
            app_id = app.get("id", "")
            task_prefix = app_id.replace("/", "_")
            if task_prefix.startswith("_"):
                task_prefix = task_prefix[1:]
            instances = int(app.get("instances", "0"))
            dispatch_stat(app_id, 'count', task_prefix, instances)
    except requests.exceptions.HTTPError as e:
        collectd.error('marathon_apps plugin: Error connecting to %s - %r' % (MARATHON_URL, e))


def dispatch_stat(plugin_instance, type, type_instance, value):
    """Read a key from info response data and dispatch a value"""
    if value is None:
        collectd.warning('marathon_apps plugin: Value not found for %s/%s' % (plugin_instance, type_instance))
        return
    log_verbose('Sending value[%s]: %s=%s' % (plugin_instance, type_instance, value))

    val = collectd.Values(plugin='marathon_apps')
    val.plugin_instance = plugin_instance
    val.type = type
    val.type_instance = type_instance
    val.values = [value]
    # https://github.com/collectd/collectd/issues/716
    val.meta = {'0': True}
    val.dispatch()


def log_verbose(msg):
    if not VERBOSE_LOGGING:
        return
    collectd.info('marathon_apps plugin [verbose]: %s' % msg)

collectd.register_config(configure_callback)
collectd.register_read(read_callback)
