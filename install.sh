#!/bin/bash

set -ex
for pkg in curl sox libsox-fmt-mp3 libttspico-utils; do
  sudo apt-get install -y $pkg
done

perl -MCPAN -e shell install URI::Escape

