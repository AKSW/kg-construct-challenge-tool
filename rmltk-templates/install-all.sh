#!/bin/bash

# install all templates into the challenge folders

set -eu
set -o pipefail

toolname="rmltk"
metadata_file="${toolname}.json"

script_dir="$(dirname "$(readlink -f "$0")")"

# assume this script is placed in challenge-tool/templates
cd "$script_dir/../"
cd "downloads/eswc-kgc-challenge-2023/"
challenge_root="$(pwd)"

for script in "$script_dir"/*/config.sh; do
    parent="$(basename "$(dirname "$script")")"
    echo "::: $parent"
    . "$script"


    for target_root_folder in "${target_root_folders[@]}"; do
        for dir in $target_root_folder/*; do
            if [[ ! -d "$dir" ]]; then
                continue
            fi

            echo "=> $dir"
            name="$dir"
        
            name2="${name//_/ }"
            name2="${name2//\// \/ }"

            mappingfile="$(get_mappingfile "$name")"

            NAME="$name" \
            NAME2="$name2" \
            TOOLNAME="${toolname}" \
            TOOLRESOURCE="Rpt" \
            MAPPINGFILE="$mappingfile" \
            envsubst '$NAME$NAME2$TOOLNAME$TOOLRESOURCE$MAPPINGFILE' \
            < "$script_dir/$parent/${metadata_file%.*}.yml.template" \
            | python3 -c 'import sys,yaml,json; json.dump(yaml.safe_load(sys.stdin),sys.stdout,indent=2)' \
            > "$dir/$metadata_file"
        done
    done
done

