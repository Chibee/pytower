#!/bin/bash

# This script will setup the project environment

# Change any of these values as you see fit.
# For initial run, all should be set to true.
BUILDCONT=true
BUILDPENV=true

. load_config.sh

# Define the path to the container
CONT="${ENV['path']}"

# 1) Create the singularity container (requires sudo)
if [ $BUILDCONT = true ]; then
    if [ -f "$CONT" ]; then
        echo "Older container found...removing"
        rm -f "$CONT"
    fi
    echo "Building container..."
    if [ ! -f "blender.tar.bz2" ]; then
        wget "https://www.dropbox.com/s/3f39ste5xh6rjkt/blender.tar.bz2?dl=0" -O "blender.tar.bz2"
    fi
    sudo ${ENV['exec']} build $CONT Singularity
else
    echo "Not building container at ${CONT}"
fi

# Initializes python env
if [ $BUILDPENV = true ]; then
    ${ENV['exec']} exec $CONT bash <<EOF
    if [ ! -d ${ENV[python]} ]; then
       yes | conda create -p ${ENV[python]} python=3.6
    fi
    source activate ${PWD}/${ENV[python]}
    python3 -m pip install -r requirements.txt
    python3 -m pip install -e .
    source deactivate
EOF
fi
