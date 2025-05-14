#!/bin/bash

vnstati -i wlo1 -d 31 -c 60 -o /tmp/vnstati-d31.png
vnstati -i wlo1 -h 24 -c 5  -o /tmp/vnstati-h24.png
vnstati -i wlo1 -w 4 -c 5   -o /tmp/vnstati-w4.png
vnstati -i wlo1 -m 1 -c 5   -o /tmp/vnstati-m1.png
