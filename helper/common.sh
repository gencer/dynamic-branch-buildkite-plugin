#!/usr/bin/env bash

TAG="dynamic-branch"
REMOTE_TAG="${BUILDKITE_PLUGIN_DYNAMIC_BRANCH_DOCKER_TAG:-bryan2402/bk-plugins:${TAG}}"

function build_and_push_docker
{
	local DOCKERFILE_PATH="${1:?Expecting 1st argument to be a Dockerfile path}"
	docker build -f "$DOCKERFILE_PATH" -t "$TAG" .
    docker tag "$TAG" "$REMOTE_TAG"
    docker push "$REMOTE_TAG"
}

function pull_and_run_docker
{
	local BK_DIR="${1:?Expecting 1st argument to be a directory}"
    docker run $(printenv | sed -n "s/\(^BUILDKITE[^=]*\).*/--env \1/gp") --env BK_DIR="$BK_DIR" -v "${BK_DIR}:/bk" "$REMOTE_TAG"
}

function upload_pipeline
{
	if grep -q "^steps:[[:space:]]*$" "$EXE_BRANCH"; then
        echo "--- Uploaded" && cat "$EXE_BRANCH"
        echo
        buildkite-agent pipeline upload "$EXE_BRANCH"
    fi
}

function run_plugin
{
	plugin_root="${1:?Expecting 1st argument to be a directory}"
	set -a
    eval $(pull_and_run_docker "${plugin_root}/.buildkite")
    set +a

    if [[ -f "$EXE_BRANCH" ]]; then
        upload_pipeline "$EXE_BRANCH"
        rm "$EXE_BRANCH"
    fi
}
