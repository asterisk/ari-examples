/*jshint node: true*/
'use strict';

var ari = require('ari-client');
var util = require('util');

ari.connect('http://localhost:8088', 'asterisk', 'asterisk', clientLoaded);

// handler for client being loaded
function clientLoaded (err, client) {
  if (err) {
    throw err;
  }

  // handler for StasisStart event
  function stasisStart(event, channel) {
    console.log(util.format(
          'Monkeys! Attack %s!', channel.name));

    var playback = client.Playback();
    channel.play({media: 'sound:tt-monkeys'},
                  playback, function(err, newPlayback) {
      if (err) {
        throw err;
      }
    });
    playback.on('PlaybackFinished', playbackFinished);

    function playbackFinished(event, completedPlayback) {
      console.log(util.format(
          'Monkeys successfully vanquished %s; hanging them up',
          channel.name));
      channel.hangup(function(err) {
        if (err) {
          throw err;
        }
      });
    }
  }

  // handler for StasisEnd event
  function stasisEnd(event, channel) {
    console.log(util.format(
          'Channel %s just left our application', channel.name));
  }

  client.on('StasisStart', stasisStart);
  client.on('StasisEnd', stasisEnd);

  client.start('channel-playback-monkeys');
}
