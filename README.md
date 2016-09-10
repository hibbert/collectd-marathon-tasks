collectd-marathon-tasks
=======================

A [collectd](http://collectd.org) plugin for [Marathon](https://mesosphere.github.io/marathon/) running on
[Apache Mesos](http://mesos.apache.org) using collectd's
[Python plugin](http://collectd.org/documentation/manpages/collectd-python.5.shtml) to publish the uptime of Marathon tasks.

This plugin is inspired by the [Mesos Python plugin](https://github.com/rayrod2030/collectd-mesos) and Kevin Lynch's [Marathon Python plugin](https://github.com/klynch/collectd-marathon).

1. It collects data from Marathon's `/v2/tasks` API endpoint and publishes uptime information of tasks.
2. It collects data from Marathon's `/v2/apps` API endpoint and publishes number of instances per application.

Install
-------
 1. Place `marathon_tasks.py` and `marathon_app_instances.py` in /opt/collectd/lib/collectd/plugins/python (assuming you have collectd installed to /opt/collectd).
 2. Configure the plugin (see below).
 3. Restart collectd.

Configuration
-------------
 * See examples `marathon_tasks.conf` and `marathon_app_instances.conf`

Requirements
------------
 * collectd 4.9+
 * Marathon 0.8.0 or greater

License
-------
This software is released under the Apache License
