#!/bin/bash

counter=0

while true
do
  counter=$((counter+1))
  echo "I made a TCP connetion; Loop = $counter"
  sleep 1  # Optional: Add a delay to control loop speed
done
