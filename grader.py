#!/usr/bin/env python3
"""Grader for industrial IoT projects. Verifies software-engineering standards:
directory structure, SDD/README docs, tests, and that the native test command passes.

Usage: python3 grader.py <project_dir> --lang <java|python|go|rust>
Prints a JSON + human-readable quality report and exits 0 on PASS, 1 on FAIL.
"""
from __future__ import annotations
import argparse, json, os, re, subprocess, sys, pathlib

# language -> (test command, test file globs expected, src dir expected, build files)
LANG_CONFIG = {
    "java": dict(
        test_cmd=["mvn", "-q", "clean", "test"],
        markers=["pom.xml", "README.md", "docs/SDD.md"],
        src_marker="src/main/java", test_marker="src/test/java",
        doc_min_words=1500,
    ),
    "python": dict(
        test_cmd=["python3", "-m", "pytest", "-q", "--cov=src", "--cov-report=term-missing"],
        markers=["requirements.txt", "README.md", "docs/SDD.md"],
        src_marker="src", test_marker="tests",
        doc_min_words=1500,
    ),
    "go": dict(
        test_cmd=["go", "test", "-cover", "./..."],
        markers=["go.mod", "README.md", "docs/SDD.md"],
        src_marker="internal", test_marker="_test.go",
        doc_min_words=1500,
    ),
    "rust": dict(
        test_cmd=["cargo", "test", "--quiet"],
        markers=["Cargo.toml", "README.md", "docs/SDD.md"],
        src_marker="src", test_marker="tests",
        doc_min_words=1500,
        env_extra={"CARGO_HOME": "/home/jovyan/.cargo"},
    ),
}


def count_words(path: str) -> int:
    try:
        with open(path, encoding="utf-8") as f:
            return len(f.read().split())
    except Exception:
        return 0


def has_file(root: str, rel: str) -> bool:
    return os.path.isfile(os.path.join(root, rel))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--lang", required=True, choices=list(LANG_CONFIG))
    args = ap.parse_args()

    root = os.path.abspath(args.project_dir)
    cfg = LANG_CONFIG[args.lang]
    checks = []
    score = 0
    max_score = 0

    def add(name, ok, detail, pts=1):
        nonlocal score, max_score
        max_score += pts
        if ok:
            score += pts
        checks.append({"check": name, "pass": bool(ok), "detail": detail, "points": pts})

    # 1. directory structure
    src_ok = os.path.isdir(os.path.join(root, cfg["src_marker"]))
    add("src/module directory present", src_ok, cfg["src_marker"], pts=2)
    # test directory / test files
    if args.lang == "go":
        test_files = list(pathlib.Path(root).rglob("*_test.go"))
        add("Go _test.go files present", len(test_files) > 0, f"{len(test_files)} test files", pts=2)
    else:
        test_ok = os.path.isdir(os.path.join(root, cfg["test_marker"]))
        add("test directory present", test_ok, cfg["test_marker"], pts=2)

    # 2. markers (build files + docs)
    for m in cfg["markers"]:
        add(f"present: {m}", has_file(root, m), m, pts=1)

    # 3. SDD doc word count
    sdd = os.path.join(root, "docs", "SDD.md")
    wc = count_words(sdd)
    add("SDD >= min words", wc >= cfg["doc_min_words"], f"{wc} words (min {cfg['doc_min_words']})", pts=2)

    # 4. architecture diagram (plantuml/mermaid) present in docs
    diag = any(pathlib.Path(root).rglob("*.puml")) or "```mermaid" in pathlib.Path(sdd).read_text() if os.path.isfile(sdd) else False
    add("architecture diagram present", bool(diag), "puml or mermaid", pts=1)

    # 5. multiple modules with real business logic (count source files)
    if args.lang == "java":
        src_files = list(pathlib.Path(root).rglob("src/main/**/*.java"))
    elif args.lang == "python":
        src_files = list(pathlib.Path(root).rglob("src/**/*.py"))
    elif args.lang == "go":
        src_files = list(pathlib.Path(root).rglob("internal/**/*.go"))
    else:
        src_files = list(pathlib.Path(root).rglob("src/**/*.rs"))
    src_count = len([f for f in src_files if "test" not in f.name.lower()])
    add("multiple source modules", src_count >= 5, f"{src_count} source files (min 5)", pts=2)

    # 6. run the test command
    env = dict(os.environ)
    env.update(cfg.get("env_extra", {}))
    if args.lang == "rust":
        env.setdefault("CARGO_HOME", "/home/jovyan/.cargo")
    print(f"[grader] running: {' '.join(cfg['test_cmd'])} (cwd={root})", file=sys.stderr)
    proc = subprocess.run(cfg["test_cmd"], cwd=root, capture_output=True, text=True, env=env, timeout=900)
    tail = (proc.stdout + proc.stderr)[-1500:]
    test_ok = proc.returncode == 0
    # count tests passed if visible
    n_tests = None
    for line in (proc.stdout + proc.stderr).splitlines():
        m = re.search(r"Tests run:\s*(\d+)", line)
        if m:
            n_tests = int(m.group(1))
    add("test command passes (exit 0)", test_ok, f"exit={proc.returncode}, tests~{n_tests}", pts=6)

    # coverage heuristic for python/go
    cov_line = None
    for line in (proc.stdout + proc.stderr).splitlines():
        if "TOTAL" in line and "%" in line:  # python pytest-cov
            cov_line = line.strip()
        if "coverage:" in line and "%" in line:  # go
            cov_line = line.strip()
    add("coverage reported", cov_line is not None, cov_line or "no coverage line", pts=2)

    pct = round(100.0 * score / max_score, 1) if max_score else 0.0
    passed = test_ok and pct >= 70.0
    result = {
        "lang": args.lang,
        "project_dir": root,
        "score": f"{score}/{max_score}",
        "percent": pct,
        "verdict": "PASS" if passed else "FAIL",
        "tests_run": n_tests,
        "coverage_line": cov_line,
        "checks": checks,
        "command_output_tail": tail,
    }
    print(json.dumps(result, indent=2))
    print(f"\n=== VERDICT: {result['verdict']} ({pct}% of {max_score}) — tests exit={proc.returncode} ===")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
