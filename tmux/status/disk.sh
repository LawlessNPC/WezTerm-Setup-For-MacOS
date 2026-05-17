#!/usr/bin/env sh

df -h / 2>/dev/null | awk 'NR == 2 { print "HD " $5 " " $4 " free" }'
