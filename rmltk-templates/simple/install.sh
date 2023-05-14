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

	mappingfile="mapping.rml.ttl"

	NAME="$name" \
	NAME2="$name2" \
	TOOLNAME="rmltk" \
	TOOLRESOURCE="Rpt" \
	MAPPINGFILE="$mappingfile" \
	envsubst '$NAME$NAME2$TOOLNAME$TOOLRESOURCE$MAPPINGFILE' \
	< "$script_dir/$metadata_file.template" > "$dir/$metadata_file"

    done
done
