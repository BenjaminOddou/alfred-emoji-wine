#!/bin/bash

# Install platform agnostic version of Pillow (put this script inside the workflow folder along with fuse.py)
mkdir -p temp
pip3 install delocate -t temp # install delocate library in temp folder to fuse binaries
pip3 download --only-binary=:all: --platform macosx_10_10_x86_64 Pillow -d temp # binary whl for intel chips
pip3 download --only-binary=:all: --platform macosx_11_0_arm64 Pillow -d temp # binary whl for arm64 chips
final_binary=$(python3 fuse.py) # fuse binaries into universal binary
mkdir -p lib
pip3 install "$final_binary" -t lib # install pillow using universal binary
rm -r temp