/*jshint node:true*/
'use strict';

var ari = require('ari-client');
var util = require('util');

var timer = null;
ari.connect('http://localhost:8088', 'asterisk', 'asterisk', clientLoaded);

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
          newBridge.startMoh(function(err) {
            if (err) {
              throw err;
            }
          });
          joinBridge(newBridge);

          timer = setTimeout(play_announcement, 30000);

          // callback that will let our users know how much we care
          function play_announcement() {
            console.log('Letting everyone know we care...');
            newBridge.stopMoh(function(err) {
              if (err) {
                throw err;
              }

              var playback = client.Playback();
              newBridge.play({media: 'sound:thnk-u-for-patience'},
                             playback, function(err, playback) {
                if (err) {
                  throw err;
                }
              });
              playback.on('PlaybackFinished', function(event, playback) {
                newBridge.startMoh(function(err) {
                  if (err) {
                    throw err;
                  }
                });
                timer = setTimeout(play_announcement, 30000);
              });
            });
          }
        });
      }
    });

    function joinBridge(bridge) {
      channel.on('ChannelLeftBridge', function(event, instances) {
        channelLeftBridge(event, instances, bridge);
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
      });
    }

    // Handler for ChannelLeftBridge event
    function channelLeftBridge(event, instances, bridge) {
      var holdingBridge = instances.bridge;
      var channel = instances.channel;

      console.log('Channel %s left bridge %s', channel.name, bridge.id);

      if (holdingBridge.id === bridge.id &&
          holdingBridge.channels.length === 0) {

        if (timer) {
          clearTimeout(timer);
        }

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

  console.log('starting');
  client.start('bridge-infinite-wait');
}
