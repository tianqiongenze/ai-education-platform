#!/usr/bin/env python3
"""Use nbgrader's own AssignmentsApp to create assignment from scratch."""
import subprocess, os

os.chdir("/home/jovyan/work/nbgrader")

# Step 1: Run nbgrader update on the specific notebook
print("=== nbgrader update source/ps1/p1.ipynb ===")
r = subprocess.run(["python3", "-m", "nbgrader", "update", "source/ps1/p1.ipynb"], capture_output=True, text=True, timeout=30)
print("stdout:", r.stdout[-300:] if r.stdout else "")
print("stderr:", r.stderr[-300:] if r.stderr else "")
print("RC:", r.returncode)

# Step 2: Check what metadata format nbgrader 0.9.5 expects
print("\n=== Check nbgrader schema ===")
r = subprocess.run(["python3", "-c", """
import json, nbformat
# Read the notebook and check metadata
nb = nbformat.read("source/ps1/p1.ipynb", as_version=4)
for i, cell in enumerate(nb.cells):
    meta = cell.metadata.get("nbgrader", {})
    print(f"Cell {i}: nbgrader={meta}")
"""], capture_output=True, text=True, timeout=10)
print(r.stdout)
if r.stderr: print("stderr:", r.stderr[:200])

# Step 3: Try with nbgrader's own assignment toolbar format
# nbgrader 0.9.5 uses schema_version in metadata
print("\n=== Fix: Add schema_version to nbgrader metadata ===")
r = subprocess.run(["python3", "-c", """
import nbformat
nb = nbformat.read("source/ps1/p1.ipynb", as_version=4)
for i, cell in enumerate(nb.cells):
    if "nbgrader" in cell.metadata:
        cell.metadata["nbgrader"]["schema_version"] = 1
        print(f"Cell {i}: added schema_version=1")
nbformat.write(nb, open("source/ps1/p1.ipynb", "w"))
print("Done")
"""], capture_output=True, text=True, timeout=10)
print(r.stdout)
if r.stderr: print("stderr:", r.stderr[:200])

# Step 4: generate_assignment
print("\n=== generate_assignment ===")
r = subprocess.run(["python3", "-m", "nbgrader", "generate_assignment", "ps1"], capture_output=True, text=True, timeout=60)
print("stdout:", r.stdout[-300:] if r.stdout else "")
print("stderr:", r.stderr[-300:] if r.stderr else "")
print("RC:", r.returncode)

if os.path.exists("release/ps1"):
    print("Release files:", os.listdir("release/ps1"))
else:
    # Step 5: Try generate with --force
    print("\n=== generate_assignment --force ===")
    r = subprocess.run(["python3", "-m", "nbgrader", "generate_assignment", "--force", "ps1"], capture_output=True, text=True, timeout=60)
    print("stdout:", r.stdout[-300:] if r.stdout else "")
    print("stderr:", r.stderr[-300:] if r.stderr else "")
    print("RC:", r.returncode)
    
    if os.path.exists("release/ps1"):
        print("Release files:", os.listdir("release/ps1"))

# Step 6: release
print("\n=== release_assignment ===")
r = subprocess.run(["python3", "-m", "nbgrader", "release_assignment", "ps1"], capture_output=True, text=True, timeout=60)
print("stdout:", r.stdout[-300:] if r.stdout else "")
print("stderr:", r.stderr[-300:] if r.stderr else "")

# Step 7: list
print("\n=== list ===")
r = subprocess.run(["python3", "-m", "nbgrader", "list"], capture_output=True, text=True, timeout=60)
print("stdout:", r.stdout[-300:] if r.stdout else "")

# Exchange
print("\n=== Exchange ===")
for root, dirs, files in os.walk("/home/jovyan/work/nbgrader/exchange"):
    for f in files:
        print("  ", os.path.join(root, f))

print("\n=== DONE ===")
