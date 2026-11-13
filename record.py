#!/usr/bin/env python3
"""Run a command, pass its output through, and save that output for the dashboard to show.

Usage: python3 record.py out/selftest.json python3 test_run.py
Exits with the command's exit code. The file holds the command, its output, the UTC time and, in
GitHub Actions, the link to the run's log.
"""
import json, os, subprocess, sys

import dashboard

out, cmd = sys.argv[1], sys.argv[2:]
p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
sys.stdout.write(p.stdout)
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
shown = ["python3" if os.path.basename(c).startswith("python") and i == 0 else c for i, c in enumerate(cmd)]
with open(out, "w", encoding="utf-8") as fh:
    json.dump(dict(command=" ".join(shown), output=p.stdout, exit=p.returncode, **dashboard.provenance()), fh, indent=1)
    fh.write("\n")
sys.exit(p.returncode)
