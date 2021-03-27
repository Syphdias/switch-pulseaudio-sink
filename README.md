# Switch-pulseaudio-sink
This repository includes two tools to switch pulseaudio default output and the
output for every application to another sink.

## pulse-audio-cycle.py

This python script aims to toggle between different outputs by cycling through
different cards and profiles (A card plus profile lead to a sink). Cards and
profiles can be filtered by providing a regex pattern.
It can send a notification via GTK 3, if wanted.

If you do not filter for profile, the profile of the card will just stay the
same.

To get a list of all Cards and Profiles:
```sh
./pulse-audio-cycle.py -v --dry --use-sink-description --with-unavailable
```

To get a overview of all options use:
```
❯ ./pulse-audio-cycle.py --help
usage: pulse-audio-cycle.py [-h] [-n] [-p CARD_REGEX PROFILE_REGEX]
                            [-c CARD_REGEX] [--use-sink-description]
                            [--with-unavailable] [--dry] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -n, --notify          Use this to notify which Sink and Profile was swiched
                        to
  -p CARD_REGEX PROFILE_REGEX, --profile CARD_REGEX PROFILE_REGEX
                        With regex_for_card
                        regex_for_profile_the_card_should_get. Can be
                        provides multiple times – for different card
                        patterns.
  -c CARD_REGEX, --card CARD_REGEX
                        Regex pattern of cards to cylce through. Use in
                        combination with --profile to set profiles during
                        cycle
  --use-sink-description
                        Instead of only looking at card names, also match
                        regex against sink description
  --with-unavailable    Don't skip unavailable profiles (if they match the
                        pattern).
  --dry                 Don't change sinks or profile (Useless without -v)
  -v, --verbose         Print extra details for debugging purposes
```

### Caveat

Unlike [`switch-audio-sink.sh`](#switch-audio-sink.sh) it does not offer an
interactive selection. If anybody needs it, feel to open a PR with a new option
for `--selection-command 'demenu'` or something of that sort. Currently I do not
have a use case for interactivity.

### Requirements
* pulsectl
* python 3.6
  (Because of format strings)
* GTK 3.0 for notifications


## switch-audio-sink.sh

This rough bash script either works interactively to offer a selection of
pulseaudio sinks to switch output default to (and all running applications) or
toggles by a provided regex. It cannot switch profiles.

It precedes [`pulse-audio-cycle.py`](#pulse-audio-cycle.py). Since
`switch-audio-sink.sh` offers interactivity which `pulse-audio-cycle.py` does
not, I kept the bash script for now. If the python version ever gets an
interactive mode, it will be obsolete and get removed.

### Options
* You can toggle by using `-t PATTERN`
* You can send notification via `notify-send` with `-n`
* Show current default output in dmenu with `-d`

### Requirements
* `pactl`
* `dmenu` if you use it interactively and not toggle trough options with `-t`
* `notify-send` if you use `-n`

# Installing
Just put the script you need in a place you like, e.g. `~/.local/bin/`.

# Contributions
If you like to contribute to this repository, just open a PR and I will have a look at it.

# License
MIT License

Copyright (c) 2021 Syphdias
