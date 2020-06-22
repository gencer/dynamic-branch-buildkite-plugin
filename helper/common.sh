#!/usr/bin/env bash

function build_and_run_docker
{
	local docker_tag="dynamic-branch"

    docker build -f ./Dockerfile -t "$docker_tag" . >&2

    docker run $(printenv | sed -n "s/\(^BUILDKITE[^=]*\).*/--env \1/gp") -t "$docker_tag"
}

function upload_pipeline
{
	local file_path="$1"
	if grep -q "^steps:[[:space:]]*$" "$file_path"; then
        echo "--- Uploaded"
        cat "$file_path"
        buildkite-agent pipeline upload "$file_path"
    fi
}
