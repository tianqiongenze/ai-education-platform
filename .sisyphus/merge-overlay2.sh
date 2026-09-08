#!/bin/bash
set -e

SRC="/var/lib/docker/overlay2"
DST="/home/docker-data/overlay2"

echo "Source: $(ls "$SRC" | wc -l) entries"
echo "Dest: $(ls "$DST" | wc -l) entries"

# Copy only directories that don't already exist in destination
count=0
for item in "$SRC"/*; do
  name=$(basename "$item")
  if [ ! -e "$DST/$name" ]; then
    cp -a "$item" "$DST/"
    count=$((count + 1))
  fi
done

echo "Copied $count missing entries"
echo "Dest now: $(ls "$DST" | wc -l) entries"
echo "Done merging"
