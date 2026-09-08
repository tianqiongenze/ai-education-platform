#!/usr/bin/env python3
"""Fix nbgrader 0.9.5 metadata and test workflow."""
import subprocess, json, os

os.chdir("/home/jovyan/work/nbgrader")
os.makedirs("source/ps1", exist_ok=True)

# Create notebook WITHOUT nbgrader metadata first (plain notebook)
nb = {
    "cells": [
        {"cell_type": "markdown", "metadata": {}, "source": ["# Problem 1: Add two numbers\n"]},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "source": ["def add(a, b):\n    ### BEGIN SOLUTION\n    return a + b\n    ### END SOLUTION\n"], "outputs": []},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "source": ["assert add(1, 2) == 3\nassert add(-1, 1) == 0\n"], "outputs": []}
    ],
    "metadata": {}, "nbformat": 4, "nbformat_minor": 5
}
with open("source/ps1/p1.ipynb", "w") as f:
    json.dump(nb, f, indent=1)
print("Plain notebook created")

# Use nbgrader's own API to add metadata correctly
print("\n=== Add nbgrader metadata via API ===")
r = subprocess.run([
    "python3", "-c", """
import nbformat
nb = nbformat.read("source/ps1/p1.ipynb", as_version=4)
# Cell 1 (index 1) = solution cell
nb.cells[1].metadata.nbgrader = {"grade": True, "solution": True, "task": False, "grade_id": "solution_add"}
# Cell 2 (index 2) = test cell  
nb.cells[2].metadata.nbgrader = {"grade": True, "solution": False, "task": False, "grade_id": "test_add"}
nbformat.write(nb, open("source/ps1/p1.ipynb", "w"))
print("Metadata added via nbformat API")
"""
], capture_output=True, text=True, timeout=30)
print(r.stdout)
if r.stderr: print("stderr:", r.stderr[:200])

# Run nbgrader update --force to fix any metadata issues
print("\n=== nbgrader update --force ===")
r = subprocess.run(["python3", "-m", "nbgrader", "update", "--force", "source/"], capture_output=True, text=True, timeout=30)
print("stdout:", r.stdout[-300:] if r.stdout else "")
print("stderr:", r.stderr[-300:] if r.stderr else "")
print("RC:", r.returncode)

# Generate assignment
print("\n=== generate_assignment ===")
r = subprocess.run(["python3", "-m", "nbgrader", "generate_assignment", "ps1"], capture_output=True, text=True, timeout=60)
print("stdout:", r.stdout[-300:] if r.stdout else "")
print("stderr:", r.stderr[-300:] if r.stderr else "")
print("RC:", r.returncode)

if os.path.exists("release/ps1"):
    print("Release files:", os.listdir("release/ps1"))
    # Check the student version
    with open("release/ps1/p1.ipynb") as f:
        student_nb = json.load(f)
    print("Student notebook cells:", len(student_nb["cells"]))
    for i, c in enumerate(student_nb["cells"]):
        src = "".join(c.get("source", []))[:60]
        print(f"  Cell {i} ({c['cell_type']}): {src}")
else:
    print("ERROR: release/ps1 not created")

# Release
print("\n=== release_assignment ===")
r = subprocess.run(["python3", "-m", "nbgrader", "release_assignment", "ps1"], capture_output=True, text=True, timeout=60)
print("stdout:", r.stdout[-300:] if r.stdout else "")
print("stderr:", r.stderr[-300:] if r.stderr else "")
print("RC:", r.returncode)

# List
print("\n=== list ===")
r = subprocess.run(["python3", "-m", "nbgrader", "list"], capture_output=True, text=True, timeout=60)
print("stdout:", r.stdout[-300:] if r.stdout else "")

# Exchange
print("\n=== Exchange ===")
exchange = "/home/jovyan/work/nbgrader/exchange"
if os.path.exists(exchange):
    for root, dirs, files in os.walk(exchange):
        for f in files:
            print("  ", os.path.join(root, f))
else:
    print("Not found")

print("\n=== DONE ===")
