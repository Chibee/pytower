#!/bin/python3
""" Evaluates a batch of blocks for stimuli generation.

Performs a series of analysis.

1. Physics differentials. (Optional)

Given an exhaustive dataframe (all configurations for a given set of towers),
determine how each configuration changes physical stability and direction of
falling.

2. Computes a histogram over the 2-D differential space.

Each configuration across towers is plotted where each dimension
is normalized by the average and variance of the entire pool.
"""

import os
import sys
import glob
import copy
import json
import hashlib
import argparse
import datetime

import numpy as np
from pprint import pprint
from dask import distributed
from dask_jobqueue import SLURMCluster
from blockworld.utils.json_encoders import TowerEncoder

from pytower.generator.noisy_gen import PushedSim
from pytower.generator.simple_gen import SimpleGen

from pytower.utils import Config
CONFIG = Config()

def evaluate_tower(base, size, gen, phys, pred, out, debug = False):
    """ Encapsulation for searching for interesting towers.

    Generates a random tower from the provided base and
    determine if it is an interesting tower.

    Arguments:
    - base (dict): A `dict` containing the fields:
                 {
                   'base' : Tower base to build over (can be `None`)
                   'k'    : The number of blocks to add
                   'idx'  : ...
                 }
    - gen (blockworld.Generator): Creates towers and their configurations
    - phys (blockworld.TowerEntropy): Evaluates the physical properties of towers
    - mode (str): Use 'angle' for difference in angle and 'instability' for instability

    Returns:
    A tuple (passed, mut) where `passed` is `True` if the tower is interesting and
    `mut` is the mutation type (None if `passed == False`)
    """
    # Build base tower
    tower = gen(base, size)
    # compute stats over towers
    trace, stats, _ = phys.analyze(tower)
    # evaluate metrics
    print(stats['instability'], stats['instability_mu'])
    passed = pred(stats) or debug
    hashed = None
    if passed:

        result = {
            'struct': tower.serialize(),
            'stats' : stats,
            'trace' : trace,
        }
        # Package results for json
        # Save the resulting tower using the content of `result` for
        # the hash / file name
        r_str = json.dumps(result, indent = 4, sort_keys = True,
                             cls = TowerEncoder)
        hashed = hashlib.md5()
        hashed.update(r_str.encode('utf-8'))
        hashed = hashed.hexdigest()
        out_file = out.format(hashed)
        print('Writing to ' + out_file)
        with open(out_file, 'w') as f:
            f.write(r_str)

    return (passed, hashed)

def create_predicate(mode, thresh):
    if mode == 'stable':
        pred = lambda t: all([
            t['instability'] == 0,
            t['instability_mu'] < thresh])
    else:
        pred = lambda t: all([
            t['instability'] >= thresh,
            t['instability_mu'] >= thresh])
    return pred

def main():

    parser = argparse.ArgumentParser(
        description = 'Evaluates a batch of blocks for stimuli generation.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--total', type = int, help = 'Number of towers to generate',
                        default = 1)
    parser.add_argument('--size', type = int, help = 'The size of each tower.',
                        default = 10)
    parser.add_argument('--base', type = int, nargs = 2, default = (2,2),
                        help = 'Dimensions of base.')
    parser.add_argument('--base_path', type = str,
                        help = 'Path to base tower.')
    parser.add_argument('--shape', type = int, nargs = 3, default = (3,1,1),
                        help = 'Dimensions of block (x,y,z).')
    parser.add_argument('--out', type = str, help = 'Path to save towers.')
    parser.add_argument('--noise', type = float, default = 0.15,
                        help = 'Noise to add to positions.')
    parser.add_argument('--force', type = float, default = 900.0,
                        help = 'Force to push blocks')
    parser.add_argument('--metric', type = str, default = 'stable',
                        choices = ['stable', 'unstable'],
                        help = 'Type of predicate.')
    parser.add_argument('--threshold', type = float, default = 0.0,
                        help = 'Upper bound of instability.')
    parser.add_argument('--slurm', action = 'store_true',
                        help = 'Use dask distributed on SLURM.')
    parser.add_argument('--batch', type = int, default = 1,
                        help = 'Number of towers to search concurrently.')
    parser.add_argument('--debug', action = 'store_true',
                        help = 'Run in debug (no rejection).')
    args = parser.parse_args()

    if args.debug:
        print('Running in debug mode. Will not reject towers')

    # Figure out where to save towers
    if args.out is None:
        suffix = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
        out_d =  '_'.join(("simple", args.metric, suffix))
        out_d = os.path.join(CONFIG['PATHS', 'towers'], out_d)
    else:
        out_d = os.path.join(CONFIG['PATHS', 'towers'], args.out)
    print('Saving new towers to {0!s}'.format(out_d))

    # Either build tower from scratch or ontop of a base
    if args.base_path is None:
        base = args.base
    else:
        base = towers.simple_tower.load(args.base_path)
        out_d += '_extended'

    # Keep track of how many towers have been created
    if os.path.isdir(out_d):
        files = glob.glob(os.path.join(out_d, '*.json'))
        results = np.array(files)
    else:
        os.mkdir(out_d)
        results = np.full(args.total, '', dtype = object)

    out_path = os.path.join(out_d, '{0!s}.json')
    enough_scenes = lambda l: len(np.argwhere(l == '')) == 0

    # Define the predicate for rejection sampling
    predicate = create_predicate(args.metric, args.threshold)

    # Initialize the tower builder and simulator
    materials = {'Wood' : 1.0}
    gen = SimpleGen(materials, 'local', args.shape)
    phys = PushedSim(noise = args.noise, force = args.force,
                     frames = 240)
    params = {
        'base' : base,
        'size' : args.size,
        'gen'  : gen,
        'phys' : phys,
        'pred' : predicate,
        'out'  : out_path,
        'debug': args.debug,
    }
    eval_tower = lambda x: evaluate_tower(**params)

    # Distribute tasks using Dask
    if enough_scenes(results):
        print('All done')
    else:
        client = initialize_dask(args.batch, slurm = args.slurm)
        # Submit first batch of towers
        ac = distributed.as_completed(
            client.map(eval_tower,
                       np.repeat(None, args.batch),
                       pure = False)
        )
        for future in ac:
            # Retrieve future's result
            (passed, hashed_path) = future.result()
            # Determine if the tower had interesting configurations
            if passed:
                check = np.argwhere(results == '')
                if len(check) == 0:
                    print('Removing', hashed_path)
                    os.remove(out_path.format(hashed_path))
                else:
                    results[check[0]] = hashed_path

            # Delete future for good measure
            client.cancel(future)
            # Check to see if more trials are needed
            n_pending = ac.count()
            if not enough_scenes(results) and (n_pending < args.batch):
                ac.update(
                    client.map(eval_tower,
                               np.repeat(None, args.batch - n_pending),
                               pure = False)
                )
            else:
                client.cancel(ac.futures)

        client.close()

def initialize_dask(n, factor = 5, slurm = False):

    if not slurm:
        cores =  len(os.sched_getaffinity(0))
        cluster = distributed.LocalCluster(processes = False,
                                           n_workers = 1,
                                           threads_per_worker = 1)

    else:
        n = min(100, n)
        py = './enter_conda.sh python3'
        params = {
            'python' : py,
            'cores' : 1,
            'memory' : '512MB',
            'walltime' : '180',
            'processes' : 1,
            'job_extra' : [
                '--qos use-everything',
                '--array 0-{0:d}'.format(n - 1),
                '--requeue',
                '--output "/dev/null"'
            ],
            'env_extra' : [
                'JOB_ID=${SLURM_ARRAY_JOB_ID%;*}_${SLURM_ARRAY_TASK_ID%;*}',
                'source /etc/profile.d/modules.sh',
                'cd {0!s}'.format(CONFIG['PATHS', 'root']),
            ]
        }
        cluster = SLURMCluster(**params)
        print(cluster.job_script())
        cluster.scale(1)

    print(cluster.dashboard_link)
    return distributed.Client(cluster)


if __name__ == '__main__':
   main()
