#!/bin/sh

for test in test/*.py
do
  printf "%-50s %s" $test
  if python3 $test > /dev/null 2> /dev/null; then
    printf "    \e[32m ... ok\n\e[39m"
  else
    printf "    \e[31m ... error\n\e[39m"
  fi
done
