/*jshint node:true*/
'use strict';

var ari = require('ari-client');
var util = require('util');

ari.connect('http://ari.js:8088', 'user', 'secret', clientLoaded);

var menu = {
  // valid menu options
  options: [1, 2],
  // note: this uses the 'extra' sounds package
  sounds: ['sound:press-1', 'sound:or', 'sound:press-2']
};

var timers = {};

// Handler for client being loaded
function clientLoaded (err, client) {
  if (err) {
    throw err;
  }

  client.on('StasisStart', stasisStart);
  client.on('StasisEnd', stasisEnd);

  // Handler for StasisStart event
  function stasisStart(event, channel) {
    console.log('Channel %s has entered the application', channel.name);

    channel.on('ChannelDtmfReceived', dtmfReceived);

    channel.answer(function(err) {
      if (err) {
        throw err;
      }

      playIntroMenu(channel);
    });
  }

  // Handler for StasisEnd event
  function stasisEnd(event, channel) {
    console.log('Channel %s has left the application', channel.name);

    // clean up listeners
    channel.removeListener('ChannelDtmfReceived', dtmfReceived);
    cancelTimeout(channel);
  }

  // Main DTMF handler
  function dtmfReceived(event, channel) {
    cancelTimeout(channel);
    var digit = parseInt(event.digit);

    console.log('Channel %s entered %d', channel.name, digit);

    // will be non-zero if valid
    var valid = ~menu.options.indexOf(digit);
    if (valid) {
      handleDtmf(channel, digit);
    } else {
      console.log('Channel %s entered an invalid option!', channel.name);

      channel.play({media: 'sound:option-is-invalid'}, function(err, playback) {
        if (err) {
          throw err;
        }

        playIntroMenu(channel);
      });
    }
  }

  /**
   * Play our intro menu to the specified channel
   * 
   * Since we want to interrupt the playback of the menu when the user presses
   * a DTMF key, we maintain the state of the menu via the MenuState object.
   * A menu completes in one of two ways:
   * (1) The user hits a key
   * (2) The menu finishes to completion
   *
   * In the case of (2), a timer is started for the channel. If the timer pops,
   * a prompt is played back and the menu restarted.
   **/
  function playIntroMenu(channel) {
    var state = {
      currentSound: menu.sounds[0],
      currentPlayback: undefined,
      done: false
    };

    channel.on('ChannelDtmfReceived', cancelMenu);
    channel.on('StasisEnd', cancelMenu);
    queueUpSound();

    // Cancel the menu, as the user did something
    function cancelMenu() {
      state.done = true;
      if (state.currentPlayback) {
        state.currentPlayback.stop(function(err) {
          // ignore errors
        });
      }

      // remove listeners as future calls to playIntroMenu will create new ones
      channel.removeListener('ChannelDtmfReceived', cancelMenu);
      channel.removeListener('StasisEnd', cancelMenu);
    }

    // Start up the next sound and handle whatever happens
    function queueUpSound() {
      if (!state.done) {
        // have we played all sounds in the menu?
        if (!state.currentSound) {
          var timer = setTimeout(stillThere, 10 * 1000);
          timers[channel.id] = timer;
        } else {
          var playback = client.Playback();
          state.currentPlayback = playback;

          channel.play({media: state.currentSound}, playback, function(err) {
            // ignore errors
          });
          playback.once('PlaybackFinished', function(event, playback) {
            queueUpSound();
          });

          var nextSoundIndex = menu.sounds.indexOf(state.currentSound) + 1;
          state.currentSound = menu.sounds[nextSoundIndex];
        }
      }
    }

    // plays are-you-still-there and restarts the menu
    function stillThere() {
      console.log('Channel %s stopped paying attention...', channel.name);

      channel.play({media: 'sound:are-you-still-there'}, function(err) {
        if (err) {
          throw err;
        }

        playIntroMenu(channel);
      });
    }
  }

  // Cancel the timeout for the channel
  function cancelTimeout(channel) {
    var timer = timers[channel.id];

    if (timer) {
      clearTimeout(timer);
      delete timers[channel.id];
    }
  }

  // Handler for channel pressing valid option
  function handleDtmf(channel, digit) {
    var parts = ['sound:you-entered', util.format('digits:%s', digit)];
    var done = 0;

    var playback = client.Playback();
    channel.play({media: 'sound:you-entered'}, playback, function(err) {
      // ignore errors
      channel.play({media: util.format('digits:%s', digit)}, function(err) {
        // ignore errors
        playIntroMenu(channel);
      });
    });
  }

  client.start('channel-dump');
}
