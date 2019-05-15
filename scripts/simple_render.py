#!/bin/python3
""" Generates renderings of towers for academic figures.

For a given tower, two sets of images will be generated:

1) With textures and background
2) With wireframe and no background
"""

import os
import sys
import glob
import json
import pprint
import argparse
import shlex
import subprocess
import numpy as np
from blockworld import towers
from blockworld.utils import json_encoders

from pytower.render import interface

from pytower.utils import Config
CONFIG = Config()

def get_data(tower_path):
    """Gets a given trial info from disk

    Arguments:
        tower_path (str): Path to tower json
    """

    with open(tower_path, 'r') as f:
        data = json.load(f)
    tower = towers.simple_tower.load(data['struct'])
    trace = data['trace']
    return tower, trace


def render_tower(tower_json, output_path, resolution,
                 mode):
    """
    Helper function that processes a tower.
    """

    tower, trace = get_data(tower_json)

    scene_str = json.dumps(tower.serialize())
    interface.render(scene_str, [trace], output_path, mode,
                     resolution = resolution)



def main():
    parser = argparse.ArgumentParser(
        formatter_class = argparse.ArgumentDefaultsHelpFormatter,
        description = 'Renders the towers in a given directory')
    parser.add_argument('--src', type = str, default = 'towers',
                        help = 'Path to tower jsons')
    parser.add_argument('--mode', type=str, default='none',
                        choices=['none', 'motion', 'frozen', 'default'],
                        help="Way to render")
    parser.add_argument('--res', type = int, nargs = 2, default = (512,512),
                        help = 'Resolution for images')

    args = parser.parse_args()

    if os.path.isfile(args.src):
        # If individual tower, save render in common directory
        src = [args.src]
        out = '{0!s}_rendered'.format(os.path.dirname(args.src))
    else:
        # Otherwise save in `renders` destination
        src = os.path.join(CONFIG['PATHS', 'towers'], args.src)
        src = glob.glob(os.path.join(src, '*.json'))
        out = os.path.join(CONFIG['PATHS', 'renders'], args.src)

    if not os.path.isdir(out):
        os.mkdir(out)

    for tower_j in src:
        tower_name = os.path.splitext(os.path.basename(tower_j))[0]
        tower_base = os.path.join(out, tower_name)
        if not os.path.isdir(tower_base):
            os.mkdir(tower_base)
        render_tower(tower_j, tower_base, args.res, args.mode)

if __name__ == '__main__':
    main()
