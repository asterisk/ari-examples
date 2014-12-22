using AsterNET.ARI;
using System;
using System.Threading;

namespace channel_state
{
    class Program
    {
        private static ARIClient _ari;
        static void Main(string[] args)
        {
            _ari = new ARIClient(new StasisEndpoint("localhost", 8088, "asterisk", "asterisk"), "channel-state");
            _ari.OnStasisStartEvent += ari_OnStasisStartEvent;
            _ari.OnStasisEndEvent += ari_OnStasisEndEvent;
            _ari.OnChannelStateChangeEvent += ari_OnChannelStateChangeEvent;

            Console.WriteLine("Press any key to exit");
            Console.ReadKey();

            _ari.Disconnect();
        }

        static void ari_OnChannelStateChangeEvent(object sender, AsterNET.ARI.Models.ChannelStateChangeEvent e)
        {
            Console.WriteLine("Channel {0} is now {1}", e.Channel.Id, e.Channel.State);
        }

        static void ari_OnStasisEndEvent(object sender, AsterNET.ARI.Models.StasisEndEvent e)
        {
            Console.WriteLine("Channel {0} just left our application", e.Channel.Id);
        }

        static void ari_OnStasisStartEvent(object sender, AsterNET.ARI.Models.StasisStartEvent e)
        {
            Console.WriteLine("Channel {0} has entered the application", e.Channel.Id);
            _ari.Channels.Ring(e.Channel.Id);
            Thread.Sleep(2000);     // wait 2 seconds
            Console.WriteLine("Answering channel {0}", e.Channel.Id);

            _ari.Channels.Answer(e.Channel.Id);
            _ari.Channels.StartSilence(e.Channel.Id);
            Thread.Sleep(4000);     // wait 4 seconds

            Console.WriteLine("hanging up channel {0}", e.Channel.Id);
            _ari.Channels.Hangup(e.Channel.Id);
        }
    }
}
