#!/usr/bin/env sh

uptime 2>/dev/null | awk -F'load averages?: ' '
  NF > 1 {
    split($2, loads, " ")
    print "LOAD " loads[1]
  }
'
