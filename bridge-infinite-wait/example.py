#!/usr/bin/env python

import ari
import logging
import threading
 
logging.basicConfig(level=logging.ERROR)
 
client = ari.connect('http://localhost:8088', 'asterisk', 'asterisk')
 
# find or create a holding bridge
holding_bridge = None

# Announcer timer
announcer_timer = None

def find_or_create_bridge():
    """Find our infinite wait bridge, or create a new one

    Returns:
    The one and only holding bridge
    """

    global holding_bridge
    global announcer_timer

    if holding_bridge:
        return holding_bridge

    bridges = [candidate for candidate in client.bridges.list() if
               candidate.json['bridge_type'] == 'holding']
    if bridges:
        bridge = bridges[0]
        print "Using bridge %s" % bridge.id
    else:
        bridge = client.bridges.create(type='holding')
        bridge.startMoh()
        print "Created bridge %s" % bridge.id

    def play_announcement(bridge):
        """Play an announcement to the bridge"""

        def on_playback_finished(playback, ev):
            """Handler for the announcement's PlaybackFinished event"""
            global announcer_timer
            global holding_bridge

            holding_bridge.startMoh()

            announcer_timer = threading.Timer(30, play_announcement,
                                              [holding_bridge])
            announcer_timer.start()

        bridge.stopMoh()
        print "Letting everyone know we care..."
        thanks_playback = bridge.play(media='sound:thnk-u-for-patience')
        thanks_playback.on_event('PlaybackFinished', on_playback_finished)

    def on_channel_left_bridge(bridge, ev):
        """Handler for ChannelLeftBridge event"""
        global holding_bridge
        global announcer_timer

        channel = ev.get('channel')
        channel_count = len(bridge.json.get('channels'))

        print "Channel %s left bridge %s" % (channel.get('name'), bridge.id)
        if holding_bridge.id == bridge.id and channel_count == 0:
            if announcer_timer:
                announcer_timer.cancel()
                announcer_timer = None
                
            print "Destroying bridge %s" % bridge.id
            holding_bridge.destroy()
            holding_bridge = None

    holding_bridge = bridge
    holding_bridge.on_event('ChannelLeftBridge', on_channel_left_bridge)

    # After 30 seconds, let everyone in the bridge know that we care
    announcer_timer = threading.Timer(30, play_announcement, [holding_bridge])
    announcer_timer.start()

    return bridge


def stasis_start_cb(channel_obj, ev):
    """Handler for StasisStart event"""
 
    bridge = find_or_create_bridge()

    channel = channel_obj.get('channel')
    print "Channel %s just entered our application, adding it to bridge %s" % (
        channel.json.get('name'), holding_bridge.id)
 
    channel.answer()
    bridge.addChannel(channel=channel.id)
 
def stasis_end_cb(channel, ev):
    """Handler for StasisEnd event"""
 
    print "Channel %s just left our application" % channel.json.get('name')
 
client.on_channel_event('StasisStart', stasis_start_cb)
client.on_channel_event('StasisEnd', stasis_end_cb)
 
client.run(apps='bridge-infinite-wait')

