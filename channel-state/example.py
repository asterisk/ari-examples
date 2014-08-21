#!/usr/bin/env python

import ari
import logging
import threading

logging.basicConfig(level=logging.ERROR)

client = ari.connect('http://localhost:8088', 'asterisk', 'asterisk')

channel_timers = {}

def stasis_end_cb(channel, ev):
    """Handler for StasisEnd event"""

    print "Channel %s just left our application" % channel.json.get('name')

    # Cancel any pending timers
    timer = channel_timers.get(channel.id)
    if timer:
        timer.cancel()
        del channel_timers[channel.id]

def stasis_start_cb(channel_obj, ev):
    """Handler for StasisStart event"""

    def answer_channel(channel):
        """Callback that will actually answer the channel"""
        print "Answering channel %s" % channel.json.get('name')
        channel.answer()
        channel.startSilence()

        # Hang up the channel in 4 seconds
        timer = threading.Timer(4, hangup_channel, [channel])
        channel_timers[channel.id] = timer
        timer.start()

    def hangup_channel(channel):
        """Callback that will actually hangup the channel"""

        print "Hanging up channel %s" % channel.json.get('name')
        channel.hangup()

    channel = channel_obj.get('channel')
    print "Channel %s has entered the application" % channel.json.get('name')

    channel.ring()
    # Answer the channel after 2 seconds
    timer = threading.Timer(2, answer_channel, [channel])
    channel_timers[channel.id] = timer
    timer.start()

def channel_state_change_cb(channel, ev):
    """Handler for changes in a channel's state"""
    print "Channel %s is now: %s" % (channel.json.get('name'),
                                     channel.json.get('state'))

client.on_channel_event('StasisStart', stasis_start_cb)
client.on_channel_event('ChannelStateChange', channel_state_change_cb)
client.on_channel_event('StasisEnd', stasis_end_cb)

client.run(apps='channel-state')
