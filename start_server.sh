#!/usr/bin/env bash
set -euo pipefail
LIBSTDCPP_PATH=$(dirname $(find /nix/store -name 'libstdc++.so.6' | head -n 1 || true))
if [ -n "${LIBSTDCPP_PATH}" ]; then
  export LD_LIBRARY_PATH="${LIBSTDCPP_PATH}:${LD_LIBRARY_PATH:-}"
fi
python api_server_cloud.py
