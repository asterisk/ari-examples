/*jshint node: true*/
'use strict';

var ari = require('ari-client');
var util = require('util');

var timers = {};
ari.connect('http://localhost:8088', 'asterisk', 'asterisk', clientLoaded);

// handler for client being loaded
function clientLoaded (err, client) {
  if (err) {
    throw err;
  }

  // handler for StasisStart event
  function stasisStart(event, channel) {
    console.log(util.format(
          'Channel %s has entered the application', channel.name));

    var playback = client.Playback();
    channel.play({media: 'tone:ring;tonezone=fr'},
                 playback, function(err, newPlayback) {
      if (err) {
        throw err;
      }
    });
    // answer the channel after 8 seconds
    var timer = setTimeout(answer, 8000);
    timers[channel.id] = timer;

    // callback that will answer the channel
    function answer() {
      console.log(util.format('Answering channel %s', channel.name));
      playback.stop(function(err) {
        if (err) {
          throw err;
        }
      });
      channel.answer(function(err) {
        if (err) {
          throw err;
        }
      });
      // hang up the channel in 1 seconds
      var timer = setTimeout(hangup, 1000);
      timers[channel.id] = timer;
    }

    // callback that will hangup the channel
    function hangup() {
      console.log(util.format('Hanging up channel %s', channel.name));
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
    var timer = timers[channel.id];
    if (timer) {
      clearTimeout(timer);
      delete timers[channel.id];
    }
  }

  client.on('StasisStart', stasisStart);
  client.on('StasisEnd', stasisEnd);

  client.start('channel-tones');
}
