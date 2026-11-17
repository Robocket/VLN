#!/usr/bin/env bash
set -e

vln_repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$vln_repo_dir"
source /opt/ros/jazzy/setup.bash
source install/setup.bash
exec /usr/bin/python3 -m vln_perception.offline_mapping "$@"
