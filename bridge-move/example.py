#!/usr/bin/env python

import logging
import requests
import ari

logging.basicConfig(level=logging.ERROR)

client = ari.connect('http://localhost:8088', 'asterisk', 'asterisk')

# Our one and only holding bridge
holding_bridge = None


def find_or_create_holding_bridge():
    """Find our infinite wait bridge, or create a new one

    Returns:
    The one and only holding bridge
    """
    global holding_bridge

    if holding_bridge:
        return holding_bridge

    bridges = [candidate for candidate in client.bridges.list() if
               candidate.json['bridge_type'] == 'holding']
    if bridges:
        bridge = bridges[0]
        print "Using bridge {}".format(bridge.id)
    else:
        bridge = client.bridges.create(type='holding')
        bridge.startMoh()
        print "Created bridge {}".format(bridge.id)

    holding_bridge = bridge
    return holding_bridge


def safe_hangup(channel):
    """Safely hang up the specified channel"""
    try:
        channel.hangup()
        print "Hung up {}".format(channel.json.get('name'))
    except requests.HTTPError as e:
        if e.response.status_code != requests.codes.not_found:
            raise e


def safe_bridge_destroy(bridge):
    """Safely destroy the specified bridge"""
    try:
        bridge.destroy()
    except requests.HTTPError as e:
        if e.response.status_code != requests.codes.not_found:
            raise e


def stasis_start_cb(channel_obj, ev):
    """Handler for StasisStart"""

    channel = channel_obj.get('channel')
    channel_name = channel.json.get('name')
    args = ev.get('args')

    if not args:
        print "Error: {} didn't provide any arguments!".format(channel_name)
        return

    if args and args[0] != 'inbound':
        # Only handle inbound channels here
        return

    if len(args) != 2:
        print "Error: {} didn't tell us who to dial".format(channel_name)
        channel.hangup()
        return

    wait_bridge = find_or_create_holding_bridge()
    wait_bridge.addChannel(channel=channel.id)

    try:
        outgoing = client.channels.originate(endpoint=args[1],
                                             app='bridge-move',
                                             appArgs='dialed')
    except requests.HTTPError:
        print "Whoops, pretty sure %s wasn't valid" % args[1]
        channel.hangup()
        return

    channel.on_event('StasisEnd', lambda *args: safe_hangup(outgoing))
    outgoing.on_event('StasisEnd', lambda *args: safe_hangup(channel))

    def outgoing_start_cb(channel_obj, ev):
        """StasisStart handler for our dialed channel"""

        print "{} answered; bridging with {}".format(outgoing.json.get('name'),
                                                     channel.json.get('name'))

        wait_bridge = find_or_create_holding_bridge()
        wait_bridge.removeChannel(channel=channel.id)

        bridge = client.bridges.create(type='mixing')
        bridge.addChannel(channel=[channel.id, outgoing.id])

        # Clean up the bridge when done
        channel.on_event('StasisEnd', lambda *args:
                         safe_bridge_destroy(bridge))
        outgoing.on_event('StasisEnd', lambda *args:
                          safe_bridge_destroy(bridge))

    outgoing.on_event('StasisStart', outgoing_start_cb)


client.on_channel_event('StasisStart', stasis_start_cb)

client.run(apps='bridge-move')
