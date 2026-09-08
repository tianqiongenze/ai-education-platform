#!/usr/bin/env python3
"""PrairieLearn Autograder v2 - Multi-language grading with CockroachDB persistence."""
import os, subprocess, tempfile, time
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2

app = Flask(__name__)
CORS(app)

DB_HOST = os.environ.get("PGHOST", "cockroachdb.infra.svc.cluster.local")
DB_PORT = os.environ.get("PGPORT", "26257")
DB_NAME = os.environ.get("PGDATABASE", "prairielearn")
DB_USER = os.environ.get("PGUSER", "root")
TEACHER_KEY = "pl-teacher-2026"
STUDENT_KEY = "pl-student-2026"
LANG_EXTS = {"python": ".py", "go": ".go", "java": ".java", "rust": ".rs", "c": ".c", "javascript": ".js"}


def get_db():
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, sslmode="disable")


def init_db():
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                student_name STRING NOT NULL,
                course_id STRING NOT NULL,
                assignment_id STRING NOT NULL,
                score FLOAT NOT NULL,
                max_score FLOAT DEFAULT 100,
                language STRING NOT NULL,
                tests_passed INT DEFAULT 0,
                tests_total INT DEFAULT 0,
                lint_errors INT DEFAULT 0,
                feedback TEXT,
                submitted_at TIMESTAMPTZ DEFAULT now()
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_scores_course ON scores (course_id, assignment_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_scores_student ON scores (student_name)")
        conn.commit()
        conn.close()
        print("DB initialized")
    except Exception as e:
        print(f"DB init error: {e}")


def check_key(level="student"):
    key = request.headers.get("X-API-Key", "")
    if level == "teacher" and key != TEACHER_KEY:
        return False
    if level == "student" and key not in (TEACHER_KEY, STUDENT_KEY):
        return False
    return True


def save_score(r):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute(
            "INSERT INTO scores (student_name, course_id, assignment_id, score, max_score, "
            "language, tests_passed, tests_total, lint_errors, feedback) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                r.get("student_name", ""),
                r.get("course_id", ""),
                r.get("assignment_id", ""),
                r.get("score", 0),
                r.get("max_score", 100),
                r.get("language", ""),
                r.get("tests", {}).get("passed", 0),
                r.get("tests", {}).get("total", 0),
                r.get("lint", {}).get("errors", 0),
                r.get("feedback", ""),
            ),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB save error: {e}")


def run_lint(code, language):
    ext = LANG_EXTS.get(language, ".txt")
    with tempfile.TemporaryDirectory() as workdir:
        f = os.path.join(workdir, f"code{ext}")
        with open(f, "w") as fh:
            fh.write(code)
        errors, warnings, details = 0, 0, []
        if language == "python":
            try:
                r = subprocess.run(["pycodestyle", "--max-line-length=120", f], capture_output=True, text=True, timeout=10)
                if r.returncode != 0:
                    lines = [l for l in r.stdout.strip().split("\n") if l.strip()]
                    errors = len(lines)
                    details = lines[:5]
            except Exception as e:
                details.append(f"pycodestyle error: {str(e)[:50]}")
        elif language == "go":
            try:
                r = subprocess.run(["gofmt", "-l", f], capture_output=True, text=True, timeout=10)
                if r.stdout.strip():
                    warnings = 1
                    details.append("gofmt: formatting issues")
            except Exception:
                pass
        return {"errors": errors, "warnings": warnings, "details": details}


def run_grading(code, language, tests, assignment_id):
    result = {
        "assignment_id": assignment_id,
        "language": language,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tests": {"passed": 0, "failed": 0, "total": 0, "details": []},
        "lint": {"errors": 0, "warnings": 0, "details": []},
        "score": 0,
        "max_score": 100,
        "feedback": "",
    }
    ext = LANG_EXTS.get(language, ".txt")
    with tempfile.TemporaryDirectory() as workdir:
        code_file = os.path.join(workdir, f"submission{ext}")
        with open(code_file, "w") as f:
            f.write(code)

        # Lint
        lint_result = run_lint(code, language)
        result["lint"] = lint_result

        # Tests (Python only for now)
        if tests and language == "python":
            test_file = os.path.join(workdir, "test_submission.py")
            with open(test_file, "w") as f:
                f.write(tests)
            try:
                r = subprocess.run(
                    ["python3", "-m", "pytest", test_file, "-v", "--tb=short"],
                    capture_output=True, text=True, timeout=30, cwd=workdir,
                )
                for line in r.stdout.split("\n"):
                    if "PASSED" in line:
                        result["tests"]["passed"] += 1
                        result["tests"]["total"] += 1
                        result["tests"]["details"].append({"test": line.strip()[:60], "status": "PASS"})
                    elif "FAILED" in line:
                        result["tests"]["failed"] += 1
                        result["tests"]["total"] += 1
                        result["tests"]["details"].append({"test": line.strip()[:60], "status": "FAIL"})
            except subprocess.TimeoutExpired:
                result["tests"]["failed"] = 1
                result["tests"]["total"] = 1
                result["tests"]["details"].append({"test": "timeout", "status": "FAIL"})
            except Exception as e:
                result["tests"]["failed"] = 1
                result["tests"]["total"] = 1
                result["tests"]["details"].append({"test": "error", "status": "FAIL", "error": str(e)[:100]})

        # Score
        test_score = (result["tests"]["passed"] / max(result["tests"]["total"], 1)) * 60
        lint_score = max(0, 20 - result["lint"]["errors"] * 2)
        quality_score = 20
        result["score"] = round(test_score + lint_score + quality_score, 1)

        if result["score"] >= 90:
            result["feedback"] = "\u4f18\u79c0! \u4ee3\u7801\u8d28\u91cf\u9ad8\uff0c\u6d4b\u8bd5\u5168\u90e8\u901a\u8fc7\u3002"
        elif result["score"] >= 80:
            result["feedback"] = "\u826f\u597d\u3002\u4ee3\u7801\u57fa\u672c\u6b63\u786e\uff0c\u6709\u5c11\u91cf\u95ee\u9898\u3002"
        elif result["score"] >= 60:
            result["feedback"] = "\u53ca\u683c\u3002\u9700\u8981\u6539\u8fdb\u4ee3\u7801\u8d28\u91cf\u548c\u6d4b\u8bd5\u8986\u76d6\u3002"
        else:
            result["feedback"] = "\u4e0d\u53ca\u683c\u3002\u8bf7\u68c0\u67e5\u4ee3\u7801\u9519\u8bef\u5e76\u8865\u5145\u6d4b\u8bd5\u3002"
    return result


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": "autograder", "version": "2.0"})


@app.route("/api/courses")
def list_courses():
    return jsonify({"courses": [
        {"id": "python-industrial", "name": "Python\u5de5\u4e1a\u5206\u6790\u9879\u76ee", "language": "python"},
        {"id": "java-mes", "name": "Java MES\u7cfb\u7edf", "language": "java"},
        {"id": "go-gateway", "name": "Go\u5de5\u4e1a\u7f51\u5173", "language": "go"},
        {"id": "rust-audit", "name": "Rust\u5b89\u5168\u5ba1\u8ba1", "language": "rust"},
    ]})


@app.route("/api/assignments/<course_id>")
def list_assignments(course_id):
    a = {
        "python-industrial": [
            {"id": "ps1", "name": "Python\u57fa\u7840", "points": 100},
            {"id": "ps2", "name": "\u6807\u51c6Python", "points": 100},
        ],
        "java-mes": [{"id": "js1", "name": "Spring Boot\u57fa\u7840", "points": 100}],
        "go-gateway": [{"id": "gs1", "name": "Gin\u6846\u67b6", "points": 100}],
        "rust-audit": [{"id": "rs1", "name": "Actix-Web", "points": 100}],
    }
    return jsonify({"assignments": a.get(course_id, [])})


@app.route("/api/grade", methods=["POST"])
def grade_submission():
    if not check_key("student"):
        return jsonify({"error": "Invalid API key"}), 403
    data = request.json
    result = run_grading(
        data.get("code", ""),
        data.get("language", "python"),
        data.get("tests", ""),
        data.get("assignment_id", "unknown"),
    )
    result["student_name"] = data.get("student_name", "anonymous")
    result["course_id"] = data.get("course_id", "unknown")
    save_score(result)
    return jsonify(result)


@app.route("/api/lint", methods=["POST"])
def lint_code():
    if not check_key("student"):
        return jsonify({"error": "Invalid API key"}), 403
    data = request.json
    return jsonify(run_lint(data.get("code", ""), data.get("language", "python")))


@app.route("/api/report/<course_id>")
def grade_report(course_id):
    if not check_key("teacher"):
        return jsonify({"error": "Teacher API key required"}), 403
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "SELECT student_name, assignment_id, score, max_score, tests_passed, "
        "tests_total, lint_errors, feedback, submitted_at "
        "FROM scores WHERE course_id = %s ORDER BY submitted_at DESC",
        (course_id,),
    )
    rows = c.fetchall()
    conn.close()
    return jsonify({
        "course_id": course_id,
        "total": len(rows),
        "results": [
            {
                "student_name": r[0], "assignment_id": r[1], "score": r[2],
                "max_score": r[3], "tests_passed": r[4], "tests_total": r[5],
                "lint_errors": r[6], "feedback": r[7], "submitted_at": str(r[8]),
            }
            for r in rows
        ],
    })


@app.route("/api/student/<name>/scores")
def student_scores(name):
    if not check_key("student"):
        return jsonify({"error": "Invalid API key"}), 403
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "SELECT course_id, assignment_id, score, max_score, feedback, submitted_at "
        "FROM scores WHERE student_name = %s ORDER BY submitted_at DESC",
        (name,),
    )
    rows = c.fetchall()
    conn.close()
    return jsonify({
        "student": name,
        "total": len(rows),
        "scores": [
            {
                "course_id": r[0], "assignment_id": r[1], "score": r[2],
                "max_score": r[3], "feedback": r[4], "submitted_at": str(r[5]),
            }
            for r in rows
        ],
    })


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=3000, debug=False)
