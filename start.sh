#!/usr/bin/env bash
cd "$(dirname "$0")"
VENV_PY="$HOME/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
if [ -f "$VENV_PY" ]; then
  "$VENV_PY" main.py
else
  python3 main.py
fi
