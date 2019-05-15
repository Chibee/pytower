import os
import json
import shlex
import argparse
import subprocess

from blockworld.utils import json_encoders

dir_path = os.path.dirname(os.path.realpath(__file__))
render_path = os.path.join(dir_path, 'render.py')

mat_path = os.path.join(dir_path, 'materials.blend')
cmd = '/blender/blender -noaudio --background -P {0!s}'

default_res = (512,512)

def render(scene_str, traces, out, mode,
           theta = 0., blocks = None, materials = mat_path,
           resolution = default_res
):
    """ Subprocess call to blender

    Arguments:
        scene_str (str): The serialized tower scene
        traces (dict): A collection of positions and orientations for each
                       block across time.
        theta (float): The camera angle in radians
        out (str): The directory to save renders
    """
    if not os.path.isdir(out):
        os.mkdir(out)
    t_path = os.path.join(out, 'trace.json')
    with open(t_path, 'w') as temp:
        json.dump(traces, temp, cls = json_encoders.TowerEncoder)

    _cmd = cmd.format(render_path)
    _cmd = shlex.split(_cmd)
    _cmd += [
        '--',
        '--materials',
        materials,
        '--out',
        out,
        '--save_world',
        '--scene',
        scene_str,
        '--trace',
        t_path,
        '--resolution',
        *list(map(str, resolution)),
        '--render_mode',
        mode,
        '--theta',
        '{0:f}'.format(theta),
    ]
    if not blocks is None:
        _cmd += ['--blocks', ] + list(map(str, blocks))
    p = subprocess.run(_cmd)
