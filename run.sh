#!/bin/bash

. load_config.sh

echo "INFO for ENV"
for i in "${!ENV[@]}";do
    echo -e "\t$i => ${ENV[$i]}";
done

# Define the path to the container and conda env
CONT="${ENV['path']}"
PYENV="${ENV['python']}"

# Parse the incoming command
COMMAND="$@"

# Enter the container and run the command
SING="${ENV['exec']} exec --nv"
mounts=(${ENV[mounts]})
BS=""
for i in "${mounts[@]}";do
    if [[ $i ]]; then
        BS="${BS} -B $i:$i"
    fi
done

${SING} ${BS} ${CONT} bash -c "source activate ${PWD}/${ENV[python]} \
        && exec $COMMAND \
        && source deactivate"
