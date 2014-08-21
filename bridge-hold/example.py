#!/usr/bin/env python

import ari
import logging

logging.basicConfig(level=logging.ERROR)

client = ari.connect('http://localhost:8088', 'asterisk', 'asterisk')

# find or create a holding bridge
bridges = [candidate for candidate in client.bridges.list() if
           candidate.json['bridge_type'] == 'holding']
if bridges:
    bridge = bridges[0]
    print "Using bridge %s" % bridge.id
else:
    bridge = client.bridges.create(type='holding')
    print "Created bridge %s" % bridge.id

def stasis_start_cb(channel_obj, ev):
    """Handler for StasisStart event"""

    channel = channel_obj.get('channel')
    print "Channel %s just entered our application, adding it to bridge %s" % (
        channel.json.get('name'), bridge.id)

    channel.answer()
    bridge.addChannel(channel=channel.id)
    bridge.startMoh()

def stasis_end_cb(channel, ev):
    """Handler for StasisEnd event"""

    print "Channel %s just left our application" % channel.json.get('name')

client.on_channel_event('StasisStart', stasis_start_cb)
client.on_channel_event('StasisEnd', stasis_end_cb)

client.run(apps='bridge-hold')
