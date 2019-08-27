# pytower
hello world

## Contributing

All team members must 

1. Create a branch based off the current master
2. Add commits to that new branch
3. push the new branch and submit a pull request to master

## Setup

### Config

Simple setups on local hosts should run fine with the `default.conf`.
However, if there are any issues with `singularity` the create a `user.conf`
with correct attributes.

`default.conf` reads as:
```ini
[ENV]
exec:singularity # the path to singularity binary
path:julia-cont  # the path to the singularity container
python:pyenv     # the name of the conda environment
julia_depot:.julia  # the relative path to set JULIA_DEPOT_PATH
mounts:
```
As of now there are some extraneous sections in `default.conf` which 
could be of use later.

```ini
[PATHS]
databases:output/databases
traces:output/traces
renders:output/renders
```

### Environment building

Simply run `setup.sh` in the root of this repo as follows

```bash
chmod +x setup.sh
./setup.sh
```

You will be prompted for sudo when building the container.

`setup.sh` will then create the container at the path specified in the config (`julia-cont` by default).

> NOTE: Like many commands in this setup, variables will be bound to those specified in `user.conf` if present or `default.conf`

## Runtime


### Interacting with the container

After running `setup.sh`, you can now use `run.sh` to use the environment.

The synatx of `run.sh` is simply:
```bash
./run.sh <command>
```

Where `command` can be any arbitrary bash expression.

For example, you can probe the python version in the conda environment using:
```
>: ./run.sh python3 --version
No user config found, using default
INFO for ENV
        path => julia-cont
        mounts => 
        exec => singularity
        julia_depot => .julia
        python => pyenv
Python 3.6.8 :: Anaconda, Inc.

```
As you can see `./run.sh` first

1. Loads the available config
2. Reads out the config
3. Executes the command

## Interacting with Julia

Getting into the `julia` repl is simply

```
>: ./run.sh julia
```
```
No user config found, using default
INFO for ENV
        path => julia-cont
        mounts => 
        exec => singularity
        julia_depot => .julia
        python => pyenv
               _
   _       _ _(_)_     |  Documentation: https://docs.julialang.org
  (_)     | (_) (_)    |
   _ _   _| |_  __ _   |  Type "?" for help, "]?" for Pkg help.
  | | | | | | |/ _` |  |
  | | |_| | | | (_| |  |  Version 1.1.0 (2019-01-21)
 _/ |\__'_|_|_|\__'_|  |  Official https://julialang.org/ release
|__/                   |

julia> 
```

To make sure that `JULIA_DEPOT_PATH` is set to that in the config:

```julia
julia> DEPOT_PATH
1-element Array{String,1}:
 ".julia"

julia> 

```

### Running package

To activate the package (ie rely on `Project.toml` and `Manifest.toml`) run

```julia
(v1.1) pkg> activate .

(kinezoo) pkg> instantiate
  Updating registry at `.julia/registries/General`
  Updating git-repo `https://github.com/JuliaRegistries/General.git`

```

You can then reference code within the repo or import dependencies:

```julia
julia> using LightGraphs
```

You can additionally pre-compile dependencies using:

```julia
(kinezoo) pkg> precompile
Precompiling project...
