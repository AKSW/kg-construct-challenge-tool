#!/bin/bash

# install all templates into the challenge folders

set -eu

script_dir="$(dirname "$(readlink -f "$0")")"

for script in "$script_dir"/*/install.sh; do
    echo "::: $(basename "$(dirname "$script")")"
    "$script"
done

