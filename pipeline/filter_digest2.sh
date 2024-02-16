#!/bin/bash

# loop over 366 nights
for i in {1..366}; do

    # check if file does not exist, pad night with 0s to 4 characters
    if [ ! -f "night_$(printf "%04d" $i).filtered.dat" ]; then

        # if file does not exist, create it
        grep -a -v tracklet "night_$(printf "%04d" $i).dat" > "night_$(printf "%04d" $i).filtered.dat"

    fi
done
