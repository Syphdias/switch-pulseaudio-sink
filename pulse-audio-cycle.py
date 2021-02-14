#!/usr/bin/env python3
"""Script to quickly switch through (wanted) pulseaudio sinks

You can provide a list of tuples to filter for

./pulse-audio-cycle.py -t -n '(Core|UE|GP104|Jabra)'
# cycle through filtered; no profle change
Headset1(Core) -> UE -> Monitor(GP104) -> Headset2(Jabra) -> [repeat]

./pulse-audio-cycle.py -t -n '(Core|UE|GP104|Jabra)' -p 'GP104' 'HDMI3'
# cycle through filtered and set proper profile
Headset1 -> UE -> Monitor(set profile) -> Headset2 -> [repeat]


# work cycle
good sound <-> headset

TODO:
    * Add function list all Sinks (Names + Description) and Profiles (N+D)
    * And mark active/default
"""
from sys import stderr
import re
import itertools
from argparse import ArgumentParser
from pulsectl import Pulse


def notify(title, text):
    """Use GTK to send notifications"""
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        gi.require_version('Notify', '0.7')
        from gi.repository import Notify

        Notify.init("pulse-audio-cycle")
        n = Notify.Notification.new(title, text)
        n.show()

    except ModuleNotFoundError:
        print(
            "Sorry, something went wrong with the notification. "
            "Are you using Gtk 3.0?",
            file=stderr,
        )


def main(args):
    pulse = Pulse("pulse-audio-cycle")

    # sink_default_name
    # card_default_name
    # card_profile_active
    current_sink = pulse.get_sink_by_name(
        pulse.server_info().default_sink_name)

    current_profile = pulse.card_info(current_sink.card).profile_active

    # TODO: get list of combinations for sink(filtered) - profile(active or filtered)
    # TODO: option to filter by name or description or both

    sink_pattern = args.sink
    profile_patterns = args.profile
    # ["sink_regex1", "profile_regex1"], ["sink_regex1", "profile_regex1"]]

    sinks = []
    # after loop: [sink1, sink2]
    sink_card_profiles = []
    # after loop: [(sink1, None),
    #              (sink2, sink2_profile3), (sink2, sink2_profile7)]

    for sink in pulse.sink_list():
        if re.search(sink_pattern, sink.description):
            sinks.append(sink)
        else:
            # this sink is not a match so we can skip the rest of the logic
            continue

        profile_count = 0
        available_profiles = [
            p for p in pulse.card_info(sink.card).profile_list
            if p.available]

        # loop over all available profiles for that card of the sink
        for profile in available_profiles:
            # loop over all provided profile patterns
            for profile_pattern_sink, profile_pattern_card in profile_patterns:
                profile_pattern_sink = re.compile(profile_pattern_sink)
                profile_pattern_card = re.compile(profile_pattern_card)

                # only check the profile pattern if the sink pattern matches
                if (
                    (re.search(profile_pattern_sink, sink.description) or
                        re.search(profile_pattern_sink, sink.name)) and
                    (re.search(profile_pattern_card, profile.description) or
                        re.search(profile_pattern_card, profile.name))
                ):
                    sink_card_profiles.append((sink, profile))
                    profile_count += 1
                    break   # one match in enough
            # after break it will go through the other profiles

        # if there was no profile match for a sink that add the tuple
        if profile_count == 0:
            sink_card_profiles.append((sink, None))

    # Also useful for finding all sinks and profiles: --dry -v -s '' -p '' ''
    if args.verbose:
        for sink, sink_profile in itertools.groupby(
                sink_card_profiles, key=lambda x: x[0]):
            print(f"Sink Name: {sink.name}")
            print(f"Sink Description: {sink.description}")
            title_bar = ("Profile Name", "Profile Description")
            print(f"  {title_bar[0]: <55} {title_bar[1]}")

            for _, profile in sink_profile:
                if profile:
                    print(f"  {profile.name: <55} {profile.description}")
                else:
                    print("No profile change")
            print()

    cycled = itertools.cycle(sink_card_profiles)
    next_item_is_new = False
    loop_count = 0
    new_sink, new_profile = None, None

    # loop until we find active config
    for sink, profile in cycled:
        loop_count += 1
        if next_item_is_new:
            new_sink, new_profile = sink, profile      # TODO: remove renaming?
            if args.verbose:
                print("New Sink:", sink)
                print("New profile:", profile)
            break
        elif loop_count > 100:
            print("No match found.", file=stderr)
            exit(1)

        # (actually card_index but sink.card is a index so: calling it "card")
        current_card = current_sink.card
        current_profile_name = current_profile.name

        try:
            profile_name = profile.name
        except AttributeError:
            profile_name = None

        if args.verbose >= 2:
            print("C:", current_card, current_profile_name)
            print("Is this:", sink.card, profile)
            print(sink.card == current_card,
                  current_profile_name is None,
                  profile_name == current_profile_name)
            print()

        # I need to compare cards (or their indices) because sinks change with profiles
        if (
            sink.card == current_card and
            (profile is None or profile_name == current_profile_name)
            # if profile_pattern is "A|B" but current profile is "C"? -> Next sink
        ):
            next_item_is_new = True

    # change profile if necessary
    if new_profile:
        card = pulse.card_info(new_sink.card)
        if args.verbose:
            print(f"Set profile to {new_profile.name}")
        if not args.dry:
            pulse.card_profile_set(card, new_profile)

        # sink changed due to card porfile change
        new_sink = [s for s in pulse.sink_list()
                    if s.card == new_sink.card][0]
        # THOUGHT: replace new_sink.card with card.index

    # change sink (has to be done always because card profile also changes sink)
    if args.verbose:
        print(f"Set default sink to {new_sink.name}")
    if not args.dry:
        pulse.sink_default_set(new_sink)

    # move all input sinks (apps/X clients) to new output sink
    for input_sink in pulse.sink_input_list():
        if args.verbose:
            print(f" Switching {input_sink.proplist['application.name']}")
        if not args.dry:
            pulse.sink_input_move(input_sink.index, new_sink.index)

    # Show notification
    if args.notify:
        details = f"New Sink: {new_sink.description}"
        if new_profile:
            details += f"\nNew Profile: {new_profile.description}"

        notify("Sink Changed", details)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "-n", "--notify",
        action="store_true", default=False,
        help="Use this to notify which Sink and Profile was swiched to",
    )
    # NODO: default setting only makes sense to force displaying default sink in
    # interactive menu
    # parser.add_argument(
    #     "--default", "-d",
    #     default=False,
    #     help="",
    # )
    # NODO: this will always toggle/cycle for now
    # parser.add_argument(
    #     "--toggle", "-t",
    #     help="",
    # )
    parser.add_argument(
        "-p", "--profile",
        nargs=2,
        action="append",
        default=[["", ""]],
        metavar=("SINK_REGEX", "PROFILE_REGEX"),
        help="With \"regex_for_sink regex_for_profile_the_card_should_get\". "
             "Can be provides multiple times – for different sinks patterns."
    )
    # examples:
    #   # headset(w/goodsound) -> speaker(any) -> …
    #   ./$0 -s 'headset|speakers' -p 'headset' 'goodsound'
    #
    #   # headset(w/goodsound) -> headset(s/voice)-> speaker(any) -> …
    #   ./$0 -s 'headset|speakers' -p 'headset' 'goodsound|voice'
    #
    #   # headset(w/goodsound) -> headset(s/voice)-> speaker(w/p1) -> speaker(w/p2) -> …
    #   ./$0 -s 'headset|speakers' -p 'headset' 'goodsound|voice' -p 'speaker' 'p1|p2'

    parser.add_argument(
        "-s", "--sink",
        default="",
        metavar="SINK_REGEX",
        help="Regex pattern of sinks to cylce through. "
             "Use in combination with --profile to set profiles during cycle"
    )
    # TODO: change sink_regex to card_regex but add option to also try sink description/name
    parser.add_argument(
        "--dry",
        action="store_true", default=False,
        help="Don't change sinks or profile (Useless without -v)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="count", default=0,
        help="Print extra details for debugging purposes"
    )

    args = parser.parse_args()

    main(args)
