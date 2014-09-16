#!/usr/bin/env python

import logging
import requests
import ari

logging.basicConfig(level=logging.ERROR)

client = ari.connect('http://localhost:8088', 'asterisk', 'asterisk')

def safe_hangup(channel):
    try:
        print "Hanging up %s" % channel.json.get('name')
        channel.hangup()
    except requests.HTTPError as e:
        if e.response.status_code != requests.codes.not_found:
            raise e

def stasis_start_cb(channel_obj, ev):
    """Handler for StasisStart"""

    channel = channel_obj.get('channel')
    args = ev.get('args')

    if not args:
        print "No arguments? No dial for you %s" % channel.json.get('name')
        return

    if args and args[0] != 'inbound':
        # Only handle inbound channels here
        return

    if len(args) != 2:
        print "%s didn't tell us who to dial" % channel.json.get('name')
        channel.hangup()
        return

    channel.ring()

    try:
        outgoing = client.channels.originate(endpoint=args[1],
            app='bridge-dial', appArgs='dialed')
    except requests.HTTPError as e:
        print "Whoops, pretty sure %s wasn't valid" % args[1]
        channel.hangup()
        return

    channel.on_event('StasisEnd', lambda *args: safe_hangup(outgoing))
    outgoing.on_event('ChannelDestroyed', lambda *args: safe_hangup(channel))

    def outgoing_start_cb(channel_obj, ev):
        """StasisStart handler for our dialed channel"""

        print "%s answered; bridging with %s" % (outgoing.json.get('name'),
            channel.json.get('name'))
        channel.answer()

        bridge = client.bridges.create(type='mixing')
        bridge.addChannel(channel=[channel.id, outgoing.id])
        bridge.play(media='sound:tt-monkeys')
        # Clean up the bridge when done
        outgoing.on_event('StasisEnd', lambda *args: bridge.destroy())

    outgoing.on_event('StasisStart', outgoing_start_cb)


client.on_channel_event('StasisStart', stasis_start_cb)

client.run(apps='bridge-dial')

