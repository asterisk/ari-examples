#!/usr/bin/env python

import ari
import logging
import uuid

logging.basicConfig(level=logging.ERROR)

client = ari.connect('http://localhost:8088', 'asterisk', 'asterisk')

def stasis_end_cb(channel, ev):
    """Handler for StasisEnd event"""

    print "Channel %s just left our application" % channel.json.get('name')

def stasis_start_cb(channel_obj, ev):
    """Handler for StasisStart event"""

    def playback_finished(playback, ev):
        """Callback when the monkeys have finished howling"""

        target_uri = playback.json.get('target_uri')
        channel_id = target_uri.replace('channel:', '')
        channel = client.channels.get(channelId=channel_id)

        print "Monkeys successfully vanquished %s; hanging them up" % channel.json.get('name')
        channel.hangup()

    channel = channel_obj.get('channel')
    print "Monkeys! Attack %s!" % channel.json.get('name')

    playback_id = str(uuid.uuid4())
    playback = channel.playWithId(playbackId=playback_id,
                                  media='sound:tt-monkeys')
    playback.on_event('PlaybackFinished', playback_finished)

client.on_channel_event('StasisStart', stasis_start_cb)
client.on_channel_event('StasisEnd', stasis_end_cb)

client.run(apps='channel-playback-monkeys')
