#!/usr/bin/env python

import ari
import logging
import threading

logging.basicConfig(level=logging.ERROR)

client = ari.connect('http://localhost:8088', 'asterisk', 'asterisk')

# Note: this uses the 'extra' sounds package
sounds = ['press-1', 'or', 'press-2']

channel_timers = {}

class MenuState(object):
    """A small tracking object for the channel in the menu"""

    def __init__(self, current_sound, complete):
        self.current_sound = current_sound
        self.complete = complete


def play_intro_menu(channel):
    """Play our intro menu to the specified channel

    Since we want to interrupt the playback of the menu when the user presses
    a DTMF key, we maintain the state of the menu via the MenuState object.
    A menu completes in one of two ways:
    (1) The user hits a key
    (2) The menu finishes to completion

    In the case of (2), a timer is started for the channel. If the timer pops,
    a prompt is played back and the menu restarted.

    Keyword Arguments:
    channel  The channel in the IVR
    """

    menu_state = MenuState(0, False)

    def play_next_sound(menu_state):
        """Play the next sound, if we should

        Keyword Arguments:
        menu_state The current state of the IVR

        Returns:
        None if no playback should occur
        A playback object if a playback was started
        """
        if menu_state.current_sound == len(sounds) or menu_state.complete:
            return None
        try:
            current_playback = channel.play(media='sound:%s' %
                                            sounds[menu_state.current_sound])
        except:
            current_playback = None
        return current_playback

    def queue_up_sound(channel, menu_state):
        """Start up the next sound and handle whatever happens

        Keywords Arguments:
        channel    The channel in the IVR
        menu_state The current state of the menu
        """

        def on_playback_finished(playback, ev, menu_state):
            """Callback handler for when a playback is finished

            Keyword Arguments:
            playback   The playback object that finished
            ev         The PlaybackFinished event
            menu_state The current state of the menu
            """
            unsubscribe_playback_event()
            queue_up_sound(channel, menu_state)

        def menu_timeout(channel, menu_state):
            """Callback called by a timer when the menu times out"""
            print 'Channel %s stopped paying attention...' % \
                channel.json.get('name')
            channel.play(media='sound:are-you-still-there')
            play_intro_menu(channel)

        def cancel_menu(channel, ev, current_playback, menu_state):
            """Cancel the menu, as the user did something"""
            menu_state.complete = True
            try:
                current_playback.stop()
            except:
                pass
            unsubscribe_cancel_menu_events()
            return

        current_playback = play_next_sound(menu_state)
        if not current_playback:
            # only start timer if menu is not complete
            if menu_state.current_sound == len(sounds) and \
                    menu_state.complete == False:
                # Menu played, start a timer!
                timer = threading.Timer(10, menu_timeout, [channel, menu_state])
                channel_timers[channel.id] = timer
                timer.start()
            return

        menu_state.current_sound += 1
        playback_event = current_playback.on_event('PlaybackFinished',
                                                   on_playback_finished,
                                                   menu_state)

        # If the user hits a key or hangs up, cancel the menu operations
        dtmf_event = channel.on_event('ChannelDtmfReceived', cancel_menu,
                                      current_playback, menu_state)
        stasis_end_event = channel.on_event('StasisEnd', cancel_menu,
                                            current_playback, menu_state)

        def unsubscribe_cancel_menu_events():
            """Unsubscribe to the ChannelDtmfReceived and StasisEnd events"""
            dtmf_event.close()
            stasis_end_event.close()

        def unsubscribe_playback_event():
            """Unsubscribe to the PlaybackFinished event"""
            playback_event.close()

    queue_up_sound(channel, menu_state)


def handle_extension_one(channel):
    """Handler for a channel pressing '1'

    Keyword Arguments:
    channel The channel in the IVR
    """
    channel.play(media='sound:you-entered')
    channel.play(media='digits:1')
    play_intro_menu(channel)


def handle_extension_two(channel):
    """Handler for a channel pressing '2'

    Keyword Arguments:
    channel The channel in the IVR
    """
    channel.play(media='sound:you-entered')
    channel.play(media='digits:2')
    play_intro_menu(channel)


def cancel_timeout(channel):
    """Cancel the timeout timer for the channel

    Keyword Arguments:
    channel The channel in the IVR
    """
    timer = channel_timers.get(channel.id)
    if timer:
        timer.cancel()
        del channel_timers[channel.id]


def on_dtmf_received(channel, ev):
    """Our main DTMF handler for a channel in the IVR

    Keyword Arguments:
    channel The channel in the IVR
    digit   The DTMF digit that was pressed
    """

    # Since they pressed something, cancel the timeout timer
    cancel_timeout(channel)
    digit = int(ev.get('digit'))

    print 'Channel %s entered %d' % (channel.json.get('name'), digit)
    if digit == 1:
        handle_extension_one(channel)
    elif digit == 2:
        handle_extension_two(channel)
    else:
        print 'Channel %s entered an invalid option!' % channel.json.get('name')
        channel.play(media='sound:option-is-invalid')
        play_intro_menu(channel)


def stasis_start_cb(channel_obj, ev):
    """Handler for StasisStart event"""

    channel = channel_obj.get('channel')
    print "Channel %s has entered the application" % channel.json.get('name')

    channel.answer()
    channel.on_event('ChannelDtmfReceived', on_dtmf_received)
    play_intro_menu(channel)


def stasis_end_cb(channel, ev):
    """Handler for StasisEnd event"""

    print "%s has left the application" % channel.json.get('name')
    cancel_timeout(channel)


client.on_channel_event('StasisStart', stasis_start_cb)
client.on_channel_event('StasisEnd', stasis_end_cb)

client.run(apps='channel-aa')


