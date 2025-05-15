#!/bin/bash

vnstati -i wlo1 -h 24 -c 5   -o /tmp/vnstati-h24.png
vnstati -i wlo1 -d 31 -c 60  -o /tmp/vnstati-d31.png
vnstati -i wlo1 -m 1  -c 240 -o /tmp/vnstati-m1.png

convert /tmp/vnstati-h24.png \
        /tmp/vnstati-d31.png \
        /tmp/vnstati-m1.png  -background transparent -splice 0x10 -append /tmp/vnstati-all.png
