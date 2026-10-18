#!/usr/bin/env python3
"""Run the pinned HyperFrames inside a project. Usage: python3 hf.py <project> lint|snapshot|render ... [args]"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

if len(sys.argv) < 3:
    sys.exit(__doc__)
proj = common.project(sys.argv[1])
argv, env = common.hf_command(sys.argv[2:])
sys.exit(subprocess.run(argv, cwd=proj, env=env).returncode)
