# Asterisk ARI examples

This repository contains a collection of ARI examples, written primarily in
Python and JavaScript (Node.js). These ARI examples coincide with ARI
documentation on the Asterisk wiki:

https://wiki.asterisk.org/wiki/display/AST/Getting+Started+with+ARI

The Python examples use the ari-py library:

https://github.com/asterisk/ari-py

The JavaScript examples use the node-ari-client library:

https://github.com/asterisk/node-ari-client

# Example Directory

## Channels

### channel-dump

Dump basic information about the channels in an Asterisk system.

### channel-state

Observe changes in channel state and Answer a channel.

### channel-playback-monkeys

Play howler monkeys (with great anger) on a channel.

### channel-tones

Manipulate locale specific indication tones on a channel.

### channel-aa

Build a simple IVR/automated attendant by handling DTMF keypresses.

## Bridges

### bridge-hold

Place all channels that enter into an application into a single holding bridge.

### bridge-infinite-area

Place all channels that enter into an application into a holding bridge. Once all channels have left the bridge, destroy it.

### bridge-dial

Dial an endpoint and put the resulting channel in a mixing bridge with the original Stasis channel. Gracefully handle hangups from either end.

# License

Copyright (c) 2014, Digium, Inc. All rights reserved.

See the LICENSE.txt file for more information.

