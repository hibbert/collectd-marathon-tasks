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
from   datetime import datetime
import dateutil.parser
import pytz
import time
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

    MARATHON_URL = "http://" + MARATHON_HOST + ":" + str(MARATHON_PORT) + "/v2/apps/?embed=app.tasks"

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
            dispatch_metrics = {}
            app_id = app.get("id", "")
            task_prefix = app_id.replace("/", "_")
            if task_prefix.startswith("_"):
                task_prefix = task_prefix[1:]
            instances = int(app.get("instances", "0"))
            dispatch_metrics["expected"] = instances
            if "tasks" in app:
                start_times = []
                for task in app["tasks"]:
                    started_at_time = dateutil.parser.parse(task["startedAt"])
                    start_times.append(started_at_time)
                dispatch_metrics["uptime_1m"] = get_running_instances(start_times, 60)
                dispatch_metrics["uptime_5m"] = get_running_instances(start_times, 300)
                dispatch_metrics["uptime_10m"] = get_running_instances(start_times, 600)
                dispatch_metrics["uptime_15m"] = get_running_instances(start_times, 900)
                dispatch_metrics["uptime_30m"] = get_running_instances(start_times, 1800)
                

            dispatch_stat(task_prefix, 'count', dispatch_metrics)
    except requests.exceptions.HTTPError as e:
        collectd.error('marathon_apps plugin: Error connecting to %s - %r' % (MARATHON_URL, e))

def get_running_instances(start_times, minimal_uptime):
    now = datetime.now(pytz.utc)
    count = 0
    for started_at_time in start_times:
        uptime_secs = int((now - started_at_time).total_seconds())
        if uptime_secs >= minimal_uptime:
            count += 1
    return count

def dispatch_stat(plugin_instance, type, dispatch_metrics):
    """Read a key from info response data and dispatch a value"""
    for type_instance in dispatch_metrics.keys():
        val = collectd.Values(plugin='marathon_apps')
        val.plugin_instance = plugin_instance
        val.type = type
        val.type_instance = type_instance
        val.values = [dispatch_metrics[type_instance]]
        # https://github.com/collectd/collectd/issues/716
        val.meta = {'0': True}
        val.dispatch()

def log_verbose(msg):
    if not VERBOSE_LOGGING:
        return
    collectd.info('marathon_apps plugin [verbose]: %s' % msg)

collectd.register_config(configure_callback)
collectd.register_read(read_callback)

