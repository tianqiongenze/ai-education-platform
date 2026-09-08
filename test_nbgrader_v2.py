#!/usr/bin/env python3
"""Install nbgrader 0.8.7 and test full assignment workflow."""
import subprocess, json, os

os.chdir("/home/jovyan/work/nbgrader")
os.makedirs("source/ps1", exist_ok=True)

# Step 0: Install nbgrader 0.8.7
print("=== Install nbgrader 0.8.7 ===")
r = subprocess.run(["pip", "install", "--quiet", "nbgrader==0.8.7"], capture_output=True, text=True, timeout=120)
print("Install:", r.returncode)

import nbgrader
print("Version:", nbgrader.__version__)

# Step 1: Create notebook with 0.8.x compatible metadata
print("\n=== Create assignment ===")
nb = {
    "cells": [
        {"cell_type": "markdown", "metadata": {}, "source": ["# Problem 1: Add two numbers\n"]},
        {"cell_type": "code", "execution_count": None, "metadata": {"nbgrader": {"grade": True, "solution": True, "task": False, "grade_id": "cell-sol"}}, "source": ["def add(a, b):\n", "    ### BEGIN SOLUTION\n", "    return a + b\n", "    ### END SOLUTION\n"], "outputs": []},
        {"cell_type": "code", "execution_count": None, "metadata": {"nbgrader": {"grade": True, "solution": False, "task": False, "grade_id": "cell-test"}}, "source": ["assert add(1, 2) == 3\n", "assert add(-1, 1) == 0\n"], "outputs": []}
    ],
    "metadata": {}, "nbformat": 4, "nbformat_minor": 4
}
with open("source/ps1/p1.ipynb", "w") as f:
    json.dump(nb, f, indent=1)
print("Notebook created")

# Step 2: Generate assignment
print("\n=== generate_assignment ===")
r = subprocess.run(["python3", "-m", "nbgrader", "generate_assignment", "ps1"], capture_output=True, text=True, timeout=60)
print("stdout:", r.stdout[-300:] if r.stdout else "")
print("stderr:", r.stderr[-300:] if r.stderr else "")
print("RC:", r.returncode)

if os.path.exists("release/ps1"):
    print("Release files:", os.listdir("release/ps1"))

# Step 3: Release assignment
print("\n=== release_assignment ===")
r = subprocess.run(["python3", "-m", "nbgrader", "release_assignment", "ps1"], capture_output=True, text=True, timeout=60)
print("stdout:", r.stdout[-300:] if r.stdout else "")
print("stderr:", r.stderr[-300:] if r.stderr else "")
print("RC:", r.returncode)

# Step 4: List assignments
print("\n=== list ===")
r = subprocess.run(["python3", "-m", "nbgrader", "list"], capture_output=True, text=True, timeout=60)
print("stdout:", r.stdout[-300:] if r.stdout else "")
print("stderr:", r.stderr[-300:] if r.stderr else "")

# Step 5: Check exchange
print("\n=== Exchange contents ===")
exchange = "/home/jovyan/work/nbgrader/exchange"
if os.path.exists(exchange):
    for root, dirs, files in os.walk(exchange):
        for f in files:
            print("  ", os.path.join(root, f))
else:
    print("Exchange dir not found")

print("\n=== nbgrader workflow test complete ===")
