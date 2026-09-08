#!/usr/bin/env python3
"""Create nbgrader assignment and test full workflow."""
import nbformat, os, subprocess

os.chdir("/home/jovyan/work/nbgrader")
os.makedirs("source/ps1", exist_ok=True)

# Create notebook with nbgrader metadata
nb = nbformat.v4.new_notebook()
nb.cells.append(nbformat.v4.new_markdown_cell("# Problem 1: Add two numbers"))

sol = nbformat.v4.new_code_cell("def add(a, b):\n    ### BEGIN SOLUTION\n    return a + b\n    ### END SOLUTION\n")
sol.metadata["nbgrader"] = {"grade": True, "solution": True}
nb.cells.append(sol)

test = nbformat.v4.new_code_cell("assert add(1, 2) == 3\nassert add(-1, 1) == 0")
test.metadata["nbgrader"] = {"grade": True, "solution": False}
nb.cells.append(test)

path = "source/ps1/p1.ipynb"
with open(path, "w") as f:
    nbformat.write(nb, f)
print("Notebook created:", path)

# Step 1: Update metadata
print("\n--- nbgrader update ---")
r = subprocess.run(["python3", "-m", "nbgrader", "update", "source/"], capture_output=True, text=True)
print(r.stdout[-200:] if r.stdout else "")
print(r.stderr[-200:] if r.stderr else "")

# Step 2: Generate assignment
print("\n--- nbgrader generate_assignment ---")
r = subprocess.run(["python3", "-m", "nbgrader", "generate_assignment", "ps1"], capture_output=True, text=True)
print(r.stdout[-300:] if r.stdout else "")
print(r.stderr[-300:] if r.stderr else "")
print("RC:", r.returncode)

if os.path.exists("release/ps1"):
    print("Release files:", os.listdir("release/ps1"))
else:
    print("ERROR: release/ps1 not created")

# Step 3: Release assignment
print("\n--- nbgrader release_assignment ---")
r = subprocess.run(["python3", "-m", "nbgrader", "release_assignment", "ps1"], capture_output=True, text=True)
print(r.stdout[-300:] if r.stdout else "")
print(r.stderr[-300:] if r.stderr else "")
print("RC:", r.returncode)

# Step 4: List
print("\n--- nbgrader list ---")
r = subprocess.run(["python3", "-m", "nbgrader", "list"], capture_output=True, text=True)
print(r.stdout[-300:] if r.stdout else "")
print(r.stderr[-300:] if r.stderr else "")

# Step 5: Check exchange
print("\n--- Exchange contents ---")
exchange = "/home/jovyan/work/nbgrader/exchange"
if os.path.exists(exchange):
    for root, dirs, files in os.walk(exchange):
        for f in files:
            print("  ", os.path.join(root, f))
else:
    print("Exchange dir not found")

print("\n=== nbgrader workflow test complete ===")
