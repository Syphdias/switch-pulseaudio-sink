#!/usr/bin/env bash
# Prompts user to select an audio device (output sink) to be used
# as default output and set it for all active applications (input sinks).
# (requires `pactl` and `dmenu`)

set -o errexit
set -o pipefail

LANG="en_US.utf-8"

while getopts ndt opts; do
    case "$opts" in
        n)      notify=true;;
        d)      default=true;;
        t)      toggle=true;;
        [?])    echo >&2 "Usage: $0 [-n] [-d|-t] [searchpattern]"
                exit 1;;
        esac
done
shift $((OPTIND-1))
sink_search_pattern="$@"

# get all output devices and all active applications
SINK_OUTPUTS=$(pactl list sinks \
               | grep -Po '(?<=Description: ).*')
SINK_INPUT_INDICES=$(pactl list sink-inputs \
                     | grep '^Sink Input #' |sed 's/.*#//' || true)
CURRENT_DEFAULT_SINK_OUTPUT="$(pactl info |grep -Po '(?<=Default Sink: ).*')"
CURRENT_DEFAULT_SINK_OUTPUT=$(pactl list sinks \
                              | grep -ie 'Description:' -e "Name: $CURRENT_DEFAULT_SINK_OUTPUT" \
                              | grep -FA1 'Name:' \
                              | grep -Po '(?<=Description: ).*')
CURRENT_DEFAULT_SINK_OUTPUT_INDEX=$(pactl list sinks \
                                    | grep -Fe 'Sink #' -e "Description: $CURRENT_DEFAULT_SINK_OUTPUT" \
                                    | grep -FB1 'Description:' \
                                    | grep -Po '(?<=Sink #).*' || true)

# remove default sink if not explicitly wanted
if [ "$default" != "true" -a "$toggle" != "true" ]; then
    SINK_OUTPUTS=$(grep -vF "$CURRENT_DEFAULT_SINK_OUTPUT" <<<"$SINK_OUTPUTS")
fi

# filter for search pattern
sink_output_index=$(pactl list sinks \
                    | grep -iEe 'Sink #' -e "Description: .*${sink_search_pattern}" \
                    | grep -FB1 'Description:' \
                    | grep -Po '(?<=Sink #).*' || true)
SINK_OUTPUTS=$(pactl list sinks \
               | grep -iEe "Description: .*${sink_search_pattern}" \
               | grep -Po '(?<=Description: ).*' || true)
match_count=$(grep '^' -c <<<"$sink_output_index")

if [ $match_count -eq 1 ]; then
    # select sink output
    sink_output_index=$sink_output_index
    selected_sink_output=$(pactl list sinks \
                           | grep -e "^Sink #$sink_output_index" -e "Description:" \
                           | grep -FA1 "Sink #$sink_output_index" \
                           | grep -Po '(?<=Description: ).*')

elif [ $match_count -lt 1 ]; then
    echo >&2 "No matches for sink pattern"
    exit 1

elif [ "$toggle" == "true" ]; then
    # toggle through selected
    new_output_sink_index=""
    for output_index in $sink_output_index; do
        if [ $output_index -gt $CURRENT_DEFAULT_SINK_OUTPUT_INDEX ]; then
            new_output_sink_index=$output_index
            break
        fi
    done
    # fallback to first match if no output sink was found
    if [ -z "$new_output_sink_index" ]; then
        new_output_sink_index=$(head -1 <<<"$sink_output_index")
    fi

    sink_output_index=$new_output_sink_index
    selected_sink_output=$(pactl list sinks \
                           | grep -e "^Sink #$sink_output_index" -e "Description:" \
                           | grep -FA1 "Sink #$sink_output_index" \
                           | grep -Po '(?<=Description: ).*')

else
    # fall back to interactive select and prompt user to select an audio device
    selected_sink_output=$(printf "$SINK_OUTPUTS" \
                           | dmenu -i -fn "Roboto Mono for Powerline-11" -p "Select sink:")
    sink_output_index=$(pactl list sinks \
                        | grep -Fe 'Sink #' -e "Description: $selected_sink_output" \
                        | grep -FB1 'Description:' \
                        | grep -Po '(?<=Sink #).*')
fi

# set new default sink for new applications
pactl set-default-sink $sink_output_index

# set new sink for every application
while read sink_input_index; do
    pactl move-sink-input $sink_input_index $sink_output_index 2>/dev/null || true
done <<<$SINK_INPUT_INDICES

[ "$notify" == "true" ] \
    && notify-send -u normal "Sink Changed" "New Sink: $selected_sink_output"
