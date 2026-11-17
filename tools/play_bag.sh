#!/usr/bin/env bash
set -e

vln_repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$vln_repo_dir"
source /opt/ros/jazzy/setup.bash
source install/setup.bash
if [ -f .cache/ros2_compat_ws/install/local_setup.bash ]; then
  source .cache/ros2_compat_ws/install/local_setup.bash
fi
exec /usr/bin/python3 -m vln_perception.bag_viewer "$@"
