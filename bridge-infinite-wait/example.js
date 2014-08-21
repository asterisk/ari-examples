/*jshint node:true*/
'use strict';

var ari = require('ari-client');
var util = require('util');

ari.connect('http://ari.js:8088', 'user', 'secret', clientLoaded);

// handler for client being loaded
function clientLoaded (err, client) {
  if (err) {
    throw err;
  }

  // handler for StasisStart event
  function stasisStart(event, channel) {
    console.log('Channel %s just entered our application', channel.name);

    // find or create a holding bridge
    client.bridges.list(function(err, bridges) {
      if (err) {
        throw err;
      }

      var bridge = bridges.filter(function(candidate) {
        return candidate.bridge_type === 'holding';
      })[0];

      if (bridge) {
        console.log('Using bridge %s', bridge.id);
        joinBridge(bridge);
      } else {
        client.bridges.create({type: 'holding'}, function(err, newBridge) {
          if (err) {
            throw err;
          }

          console.log('Created bridge %s', newBridge.id);
          joinBridge(newBridge);
        });
      }
    });

    function joinBridge(bridge) {
      bridge.on('ChannelLeftBridge', function(event, instances) {
        channelLeftBridge(event, instances, bridge);
      });

      bridge.startMoh(function(err) {
        if (err) {
          throw err;
        }
      });
      bridge.addChannel({channel: channel.id}, function(err) {
        if (err) {
          throw err;
        }
      });
      channel.answer(function(err) {
        if (err) {
          throw err;
        }

        channel.play({media: 'sound:thnk-u-for-patience'},
            function(err, playback) {

          if (err) {
            throw err;
          }
        });
      });
    }

    // Handler for ChannelLeftBridge event
    function channelLeftBridge(event, instances, bridge) {
      var holdingBridge = instances.bridge;
      var channel = instances.channel;

      console.log('Channel %s left bridge %s', channel.name, bridge.id);

      if (holdingBridge.id === bridge.id &&
          holdingBridge.channels.length === 0) {

        bridge.destroy(function(err) {
          if (err) {
            throw err;
          }
        });
      }
    }
  }

  // handler for StasisEnd event
  function stasisEnd(event, channel) {
    console.log('Channel %s just left our application', channel.name);
  }

  client.on('StasisStart', stasisStart);
  client.on('StasisEnd', stasisEnd);

  client.start('bridge-hold');
}
