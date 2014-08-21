#!/usr/bin/env python

import ari
import logging

logging.basicConfig(level=logging.ERROR)

client = ari.connect('http://localhost:8088', 'asterisk', 'asterisk')

current_channels = client.channels.list()
if len(current_channels) == 0:
    print "No channels currently :-("
else:
    print "Current channels:"
    for channel in current_channels:
        print channel.json.get('name')

def stasis_start_cb(channel_obj, ev):
    """Handler for StasisStart event"""

    channel = channel_obj.get('channel')
    print "Channel %s has entered the application" % channel.json.get('name')

    for key, value in channel.json.items():
        print "%s: %s" % (key, value)

def stasis_end_cb(channel, ev):
    """Handler for StasisEnd event"""

    print "%s has left the application" % channel.json.get('name')

client.on_channel_event('StasisStart', stasis_start_cb)
client.on_channel_event('StasisEnd', stasis_end_cb)

client.run(apps='channel-dump')
