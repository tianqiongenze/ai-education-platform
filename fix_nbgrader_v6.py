#!/usr/bin/env python3
"""Create nbgrader notebook with complete v3 metadata and test full workflow."""
import subprocess, json, os, nbformat

os.chdir("/home/jovyan/work/nbgrader")
os.makedirs("source/ps1", exist_ok=True)

# Create notebook with COMPLETE v3 nbgrader metadata (all required fields)
nb = nbformat.v4.new_notebook()
nb.cells.append(nbformat.v4.new_markdown_cell("# Problem 1: Add two numbers"))

# Solution cell - all required fields for v3
sol = nbformat.v4.new_code_cell("def add(a, b):\n    ### BEGIN SOLUTION\n    return a + b\n    ### END SOLUTION\n")
sol.metadata["nbgrader"] = {
    "grade": True,
    "solution": True,
    "task": False,
    "locked": False,
    "points": 1.0,
    "grade_id": "sol_add",
    "schema_version": 3,
    "cell_type": "code",
}
nb.cells.append(sol)

# Test cell
test = nbformat.v4.new_code_cell("assert add(1, 2) == 3\nassert add(-1, 1) == 0")
test.metadata["nbgrader"] = {
    "grade": True,
    "solution": False,
    "task": False,
    "locked": True,
    "points": 0.0,
    "grade_id": "test_add",
    "schema_version": 3,
    "cell_type": "code",
}
nb.cells.append(test)

with open("source/ps1/p1.ipynb", "w") as f:
    nbformat.write(nb, f)
print("Notebook created with complete v3 metadata")

# Verify
nb2 = nbformat.read("source/ps1/p1.ipynb", as_version=4)
for i, cell in enumerate(nb2.cells):
    meta = cell.metadata.get("nbgrader", {})
    if meta:
        print(f"  Cell {i}: {meta}")

# generate_assignment
print("\n=== generate_assignment ===")
r = subprocess.run(["python3", "-m", "nbgrader", "generate_assignment", "ps1"], capture_output=True, text=True, timeout=60)
print("stdout:", r.stdout[-300:] if r.stdout else "")
print("stderr:", r.stderr[-300:] if r.stderr else "")
print("RC:", r.returncode)

if os.path.exists("release/ps1"):
    print("\nRelease files:", os.listdir("release/ps1"))
    
    # Show student version (solutions stripped)
    with open("release/ps1/p1.ipynb") as f:
        student_nb = json.load(f)
    print("Student notebook:")
    for i, c in enumerate(student_nb["cells"]):
        src = "".join(c.get("source", []))[:80]
        print(f"  Cell {i} ({c['cell_type']}): {src}")
    
    # release_assignment
    print("\n=== release_assignment ===")
    r = subprocess.run(["python3", "-m", "nbgrader", "release_assignment", "ps1"], capture_output=True, text=True, timeout=60)
    print("stdout:", r.stdout[-200:] if r.stdout else "")
    print("stderr:", r.stderr[-200:] if r.stderr else "")
    
    # list
    print("\n=== list ===")
    r = subprocess.run(["python3", "-m", "nbgrader", "list"], capture_output=True, text=True, timeout=60)
    print("stdout:", r.stdout[-200:] if r.stdout else "")
    
    # exchange
    print("\n=== Exchange ===")
    for root, dirs, files in os.walk("/home/jovyan/work/nbgrader/exchange"):
        for f in files:
            print("  ", os.path.join(root, f))
else:
    print("ERROR: release/ps1 not created")

print("\n=== DONE ===")
