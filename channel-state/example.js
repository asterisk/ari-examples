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

    channel.ring(function(err) {
      if (err) {
        throw err;
      }
    });
    // answer the channel after 2 seconds
    var timer = setTimeout(answer, 2000);
    timers[channel.id] = timer;

    // callback that will answer the channel
    function answer() {
      console.log(util.format('Answering channel %s', channel.name));
      channel.answer(function(err) {
        if (err) {
          throw err;
        }
      });
      channel.startSilence(function(err) {
        if (err) {
          throw err;
        }
      });
      // hang up the channel in 4 seconds
      var timer = setTimeout(hangup, 4000);
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

  // handler for ChannelStateChange event
  function channelStateChange(event, channel) {
    console.log(util.format(
          'Channel %s is now: %s', channel.name, channel.state));
  }

  client.on('StasisStart', stasisStart);
  client.on('StasisEnd', stasisEnd);
  client.on('ChannelStateChange', channelStateChange);

  client.start('channel-state');
}
