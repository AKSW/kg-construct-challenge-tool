#!/bin/bash

# install the template into the challenge folders


set -eu

metadata_file="rmltk.json"
target_root_folders=("gtfs-madrid-bench")
script_dir="$(dirname "$(readlink -f "$0")")"

cd "$script_dir/../../"
cd "downloads/eswc-kgc-challenge-2023/"
challenge_root="$(pwd)"

for target_root_folder in "${target_root_folders[@]}"; do
    for dir in $target_root_folder/*; do
	if [[ ! -d "$dir" ]]; then
	    continue
	fi

	echo "=> $dir"
	name="$dir"
	
	name2="${name//_/ }"
	name2="${name2//\// \/ }"

	if [[ "$name" == */heterogeneity_* ]]; then
	    mappingfile="mapping.rml.ttl"
	elif [[ "$name" == */scale_* ]]; then
	    mappingfile="mapping.r2rml.ttl"
	else
	    echo "please add the mapping file name for ${name} to $0" >&2
	    exit 1
	fi

	NAME="$name" \
	NAME2="$name2" \
	TOOLNAME="rmltk" \
	TOOLRESOURCE="Rpt" \
	MAPPINGFILE="$mappingfile" \
	envsubst '$NAME$NAME2$TOOLNAME$TOOLRESOURCE$MAPPINGFILE' \
	< "$script_dir/$metadata_file.template" > "$dir/$metadata_file"

    done
done
