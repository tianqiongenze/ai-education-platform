#!/usr/bin/env python3
"""Fix: Let nbgrader update set schema_version=3, then DON'T touch it, then generate."""
import subprocess, os, json

os.chdir("/home/jovyan/work/nbgrader")

# Step 1: Re-create notebook fresh (no nbgrader metadata)
print("=== Create fresh notebook ===")
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
print("Fresh notebook created")

# Step 2: Add nbgrader metadata using nbformat API
print("\n=== Add nbgrader metadata ===")
r = subprocess.run(["python3", "-c", '''
import nbformat
nb = nbformat.read("source/ps1/p1.ipynb", as_version=4)
nb.cells[1].metadata["nbgrader"] = {"grade": True, "solution": True, "task": False, "grade_id": "solution_add"}
nb.cells[2].metadata["nbgrader"] = {"grade": True, "solution": False, "task": False, "grade_id": "test_add"}
nbformat.write(nb, open("source/ps1/p1.ipynb", "w"))
print("Metadata added")
'''], capture_output=True, text=True, timeout=10)
print(r.stdout)
if r.stderr: print("err:", r.stderr[:200])

# Step 3: Run nbgrader update (this sets schema_version=3)
print("\n=== nbgrader update source/ps1/p1.ipynb ===")
r = subprocess.run(["python3", "-m", "nbgrader", "update", "source/ps1/p1.ipynb"], capture_output=True, text=True, timeout=30)
print("stdout:", r.stdout[-200:] if r.stdout else "")
print("stderr:", r.stderr[-200:] if r.stderr else "")
print("RC:", r.returncode)

# Step 4: Verify metadata is correct (schema_version=3)
print("\n=== Verify metadata ===")
r = subprocess.run(["python3", "-c", '''
import nbformat
nb = nbformat.read("source/ps1/p1.ipynb", as_version=4)
for i, cell in enumerate(nb.cells):
    meta = cell.metadata.get("nbgrader", {})
    if meta:
        print(f"Cell {i}: {meta}")
'''], capture_output=True, text=True, timeout=10)
print(r.stdout)

# Step 5: generate_assignment (DO NOT modify metadata after update!)
print("\n=== generate_assignment ===")
r = subprocess.run(["python3", "-m", "nbgrader", "generate_assignment", "ps1"], capture_output=True, text=True, timeout=60)
print("stdout:", r.stdout[-300:] if r.stdout else "")
print("stderr:", r.stderr[-300:] if r.stderr else "")
print("RC:", r.returncode)

if os.path.exists("release/ps1"):
    print("\nRelease files:", os.listdir("release/ps1"))
    with open("release/ps1/p1.ipynb") as f:
        student_nb = json.load(f)
    print("Student notebook cells:", len(student_nb["cells"]))
    for i, c in enumerate(student_nb["cells"]):
        src = "".join(c.get("source", []))[:80]
        print(f"  Cell {i} ({c['cell_type']}): {src}")
    
    # Step 6: release
    print("\n=== release_assignment ===")
    r = subprocess.run(["python3", "-m", "nbgrader", "release_assignment", "ps1"], capture_output=True, text=True, timeout=60)
    print("stdout:", r.stdout[-200:] if r.stdout else "")
    print("stderr:", r.stderr[-200:] if r.stderr else "")
    
    # Step 7: list
    print("\n=== list ===")
    r = subprocess.run(["python3", "-m", "nbgrader", "list"], capture_output=True, text=True, timeout=60)
    print("stdout:", r.stdout[-200:] if r.stdout else "")
    
    # Exchange
    print("\n=== Exchange ===")
    for root, dirs, files in os.walk("/home/jovyan/work/nbgrader/exchange"):
        for f in files:
            print("  ", os.path.join(root, f))
else:
    print("ERROR: release/ps1 still not created")
    # Check if there are leftover old metadata
    r = subprocess.run(["python3", "-c", '''
import nbformat
nb = nbformat.read("source/ps1/p1.ipynb", as_version=4)
for i, cell in enumerate(nb.cells):
    meta = cell.metadata.get("nbgrader", {})
    if meta:
        sv = meta.get("schema_version", "MISSING")
        print(f"Cell {i}: schema_version={sv}, grade_id={meta.get(\"grade_id\")}, full={meta}")
'''], capture_output=True, text=True, timeout=10)
    print(r.stdout)

print("\n=== DONE ===")
