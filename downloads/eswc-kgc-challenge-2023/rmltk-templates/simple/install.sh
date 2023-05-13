#!/bin/bash

# install the template into the challenge folders


set -eu

metadata_file="rmltk.json"
target_root_folders=("duplicated-values"
		     "empty-values"
		     "mappings"
		     "properties"
		     "records"
		     "joins/*")
script_dir="$(dirname "$(readlink -f "$0")")"

cd "$script_dir/../.."
challenge_root="$(pwd)"

for target_root_folder in "${target_root_folders[@]}"; do
    for dir in $target_root_folder/*; do
	if [[ ! -d "$dir" ]]; then
	    continue
	fi

	echo "=> $dir"
	name="$(basename "$dir")"
	name2="${name//_/ }"
	NAME="$name" NAME2="$name2" envsubst '$NAME$NAME2' < "$script_dir/$metadata_file.template" > "$dir/$metadata_file"

    done
done
