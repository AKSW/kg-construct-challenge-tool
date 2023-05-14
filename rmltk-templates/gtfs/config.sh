# bash config

target_root_folders=("gtfs-madrid-bench")

get_mappingfile() {
    local name="$1"
    if [[ "$name" == */heterogeneity_* ]]; then
        echo "mapping.rml.ttl"
    elif [[ "$name" == */scale_* ]]; then
        echo "mapping.r2rml.ttl"
    else
        echo "please add the mapping file name for ${name} to ${script}" >&2
        exit 1
    fi
}
