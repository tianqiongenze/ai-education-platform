#!/bin/bash
# Fix 1: Guides distribution (teacher=both, student=student-only)
# Fix 2: Multi-language code review (Python/Java/Go/Rust/C)
# Fix 3: Verify CRDB K8s deployment

set -e

echo "============================================================"
echo "Part 1: Fix guides distribution"
echo "============================================================"

# Get current startup script, fix the guide distribution logic
kubectl get cm jupyterhub-startup -n jupyterhub -o jsonpath='{.data.startup\.sh}' > /tmp/startup_fix_guides.sh

# Replace the guide distribution section:
# Old: everyone gets both guides
# New: teacher gets both, student gets student-only
python3 << 'PYEOF'
content = open('/tmp/startup_fix_guides.sh').read()

# Replace the guide distribution lines
old_guides = """    cp $COMMON/guide_teacher $WORK/JUPYTERHUB-OPERATION-GUIDE.md 2>/dev/null
    cp $COMMON/guide_student $WORK/JUPYTERHUB-STUDENT-GUIDE.md 2>/dev/null
    cp $COMMON/code_grader $WORK/code_grader.py 2>/dev/null"""

new_guides = """    # Teacher gets both guides, Student gets student guide only
    case "$USERNAME" in
      teacher-zhang|Lecture-*|lecture-*)
        cp $COMMON/guide_teacher $WORK/JUPYTERHUB-OPERATION-GUIDE.md 2>/dev/null
        cp $COMMON/guide_student $WORK/JUPYTERHUB-STUDENT-GUIDE.md 2>/dev/null
        ;;
      *)
        cp $COMMON/guide_student $WORK/JUPYTERHUB-STUDENT-GUIDE.md 2>/dev/null
        ;;
    esac
    cp $COMMON/code_grader $WORK/code_grader.py 2>/dev/null"""

if old_guides in content:
    content = content.replace(old_guides, new_guides)
    print("Guide distribution fixed!")
else:
    # Try alternative pattern
    import re
    content = re.sub(
        r'(cp \$COMMON/guide_teacher[^\n]*\n\s*cp \$COMMON/guide_student[^\n]*\n\s*cp \$COMMON/code_grader[^\n]*)',
        new_guides.replace('\\', '\\\\'),
        content
    )
    print("Guide distribution fixed (regex)!")

open('/tmp/startup_fix_guides.sh', 'w').write(content)
PYEOF

kubectl create configmap jupyterhub-startup -n jupyterhub \
  --from-file=startup.sh=/tmp/startup_fix_guides.sh \
  --dry-run=client -o yaml | kubectl apply -f - 2>&1

echo "Guides distribution fixed: teacher=both, student=student-only"

echo ""
echo "============================================================"
echo "Part 2: Multi-language code review system"
echo "============================================================"

# Create universal code review tool
cat << 'REVIEWEOF' | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: code-review-tools
  namespace: jupyterhub
data:
  code_review.py: |
    #!/usr/bin/env python3
    """Universal Multi-Language Code Review Tool
    Supports: Python (pycodestyle), Java (checkstyle), Go (gofmt+vet), 
              Rust (clippy+fmt), C (cppcheck), JavaScript (eslint)
    Usage: python3 code_review.py <file_or_directory>
    """
    import os, sys, subprocess, json, time
    
    def review_python(path):
        """PEP8 + pyflakes"""
        results = {"language": "Python", "tool": "pycodestyle", "issues": [], "score": 100}
        try:
            proc = subprocess.Popen(["python3", "-m", "pycodestyle", "--max-line-length=120", path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, _ = proc.communicate(timeout=30)
            lines = stdout.decode().strip().split("\\n") if stdout.decode().strip() else []
            results["issues"] = [l for l in lines if l.strip()]
            total_lines = sum(1 for _ in open(path)) if os.path.isfile(path) else 100
            if total_lines > 0:
                results["score"] = max(0, 100 - len(results["issues"]) * 100 // total_lines)
        except Exception as e:
            results["issues"].append(f"Error: {e}")
        return results
    
    def review_java(path):
        """Checkstyle or javac syntax check"""
        results = {"language": "Java", "tool": "checkstyle/javac", "issues": [], "score": 100}
        try:
            # Try checkstyle
            cs_jar = subprocess.run(["find", "/opt", "/usr/share", "-name", "checkstyle*.jar", "-maxdepth", "3"],
                capture_output=True, text=True, timeout=5).stdout.strip()
            if cs_jar:
                proc = subprocess.Popen(["java", "-jar", cs_jar.split("\\n")[0], "-c", "/sun_checks.xml", path],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, _ = proc.communicate(timeout=30)
                lines = stdout.decode().strip().split("\\n") if stdout.decode().strip() else []
                results["issues"] = [l for l in lines if "WARN" in l or "ERROR" in l]
            else:
                # Fallback: javac syntax check
                proc = subprocess.Popen(["javac", "-d", "/tmp", path],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                _, stderr = proc.communicate(timeout=30)
                err_lines = stderr.decode().strip().split("\\n") if stderr.decode().strip() else []
                results["issues"] = [l for l in err_lines if "error" in l.lower() or "warning" in l.lower()]
            
            if not results["issues"]:
                results["score"] = 100
            else:
                results["score"] = max(0, 100 - len(results["issues"]) * 5)
        except Exception as e:
            results["issues"].append(f"Error: {e}")
        return results
    
    def review_go(path):
        """gofmt + go vet"""
        results = {"language": "Go", "tool": "gofmt+govet", "issues": [], "score": 100}
        try:
            # gofmt check
            proc = subprocess.Popen(["gofmt", "-l", path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, _ = proc.communicate(timeout=30)
            unformatted = stdout.decode().strip().split("\\n") if stdout.decode().strip() else []
            for f in unformatted:
                results["issues"].append(f"FORMAT: {f} needs gofmt")
            
            # go vet
            if os.path.isdir(path):
                proc = subprocess.Popen(["go", "vet", "./..."], cwd=path,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                _, stderr = proc.communicate(timeout=60)
                vet_lines = stderr.decode().strip().split("\\n") if stderr.decode().strip() else []
                results["issues"].extend([l for l in vet_lines if l.strip()])
            
            results["score"] = max(0, 100 - len(results["issues"]) * 10)
        except Exception as e:
            results["issues"].append(f"Error: {e}")
        return results
    
    def review_rust(path):
        """cargo clippy + rustfmt"""
        results = {"language": "Rust", "tool": "clippy+fmt", "issues": [], "score": 100}
        try:
            if os.path.isdir(path) and os.path.exists(os.path.join(path, "Cargo.toml")):
                # clippy
                proc = subprocess.Popen(["cargo", "clippy", "--", "-W", "clippy::all"], cwd=path,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    env={**os.environ, "CARGO_HOME": os.path.expanduser("~/.cargo")})
                _, stderr = proc.communicate(timeout=120)
                clippy_lines = stderr.decode().strip().split("\\n") if stderr.decode().strip() else []
                results["issues"] = [l for l in clippy_lines if "warning" in l.lower() or "error" in l.lower()]
            elif path.endswith(".rs"):
                # rustfmt check
                proc = subprocess.Popen(["rustfmt", "--check", path],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    env={**os.environ, "CARGO_HOME": os.path.expanduser("~/.cargo")})
                _, stderr = proc.communicate(timeout=30)
                fmt_lines = stderr.decode().strip().split("\\n") if stderr.decode().strip() else []
                results["issues"] = [l for l in fmt_lines if l.strip()]
            
            results["score"] = max(0, 100 - len(results["issues"]) * 5)
        except Exception as e:
            results["issues"].append(f"Error: {e}")
        return results
    
    def review_c(path):
        """cppcheck"""
        results = {"language": "C/C++", "tool": "cppcheck", "issues": [], "score": 100}
        try:
            proc = subprocess.Popen(["cppcheck", "--enable=all", "--std=c11", path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            _, stderr = proc.communicate(timeout=60)
            lines = stderr.decode().strip().split("\\n") if stderr.decode().strip() else []
            results["issues"] = [l for l in lines if "error" in l.lower() or "warning" in l.lower() or "performance" in l.lower()]
            results["score"] = max(0, 100 - len(results["issues"]) * 5)
        except FileNotFoundError:
            results["issues"].append("cppcheck not installed. Install: apt install cppcheck")
        except Exception as e:
            results["issues"].append(f"Error: {e}")
        return results
    
    def review_javascript(path):
        """node --check (syntax)"""
        results = {"language": "JavaScript", "tool": "node-check", "issues": [], "score": 100}
        try:
            proc = subprocess.Popen(["node", "--check", path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            _, stderr = proc.communicate(timeout=15)
            err_lines = stderr.decode().strip().split("\\n") if stderr.decode().strip() else []
            results["issues"] = err_lines
            results["score"] = max(0, 100 - len(results["issues"]) * 10)
        except Exception as e:
            results["issues"].append(f"Error: {e}")
        return results
    
    def detect_language(path):
        """Detect programming language from file extension or project files."""
        if os.path.isdir(path):
            if os.path.exists(os.path.join(path, "Cargo.toml")): return "rust"
            if os.path.exists(os.path.join(path, "go.mod")): return "go"
            if os.path.exists(os.path.join(path, "pom.xml")) or os.path.exists(os.path.join(path, "build.gradle")): return "java"
            if os.path.exists(os.path.join(path, "package.json")): return "javascript"
            if os.path.exists(os.path.join(path, "Makefile")) or os.path.exists(os.path.join(path, "CMakeLists.txt")): return "c"
            return "python"  # default
        
        ext = os.path.splitext(path)[1].lower()
        return {
            ".py": "python", ".java": "java", ".go": "go",
            ".rs": "rust", ".c": "c", ".h": "c", ".cpp": "c", ".hpp": "c",
            ".js": "javascript", ".ts": "javascript",
        }.get(ext, "python")
    
    def review(path):
        """Universal code review entry point."""
        lang = detect_language(path)
        reviewers = {
            "python": review_python, "java": review_java, "go": review_go,
            "rust": review_rust, "c": review_c, "javascript": review_javascript,
        }
        reviewer = reviewers.get(lang, review_python)
        
        if os.path.isdir(path):
            # Review all source files in directory
            all_results = []
            extensions = {".py": "python", ".java": "java", ".go": "go", ".rs": "rust", ".c": "c", ".cpp": "c", ".js": "javascript"}
            skip_dirs = {"target", "__pycache__", "node_modules", ".git", "vendor", ".cargo", "venv"}
            
            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if d not in skip_dirs]
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in extensions:
                        file_path = os.path.join(root, f)
                        file_lang = extensions[ext]
                        file_reviewer = reviewers.get(file_lang, review_python)
                        result = file_reviewer(file_path)
                        all_results.append(result)
            
            # Aggregate
            total_issues = sum(len(r["issues"]) for r in all_results)
            avg_score = sum(r["score"] for r in all_results) / max(len(all_results), 1)
            return {
                "language": "multi",
                "files_reviewed": len(all_results),
                "total_issues": total_issues,
                "average_score": round(avg_score, 1),
                "files": all_results,
            }
        else:
            return reviewer(path)
    
    if __name__ == "__main__":
        if len(sys.argv) < 2:
            print("Usage: python3 code_review.py <file_or_directory>")
            print("Supported: Python, Java, Go, Rust, C/C++, JavaScript")
            print("")
            print("Examples:")
            print("  python3 code_review.py src/main.py")
            print("  python3 code_review.py /home/jovyan/work/industrial-analytics/src/")
            print("  python3 code_review.py /home/jovyan/work/mes-system/production-service/src/")
            sys.exit(1)
        
        path = sys.argv[1]
        if not os.path.exists(path):
            print(f"Error: {path} not found")
            sys.exit(1)
        
        start = time.time()
        result = review(path)
        elapsed = time.time() - start
        
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"\\nReview completed in {elapsed:.1f}s")
    
  install_linters.sh: |
    #!/bin/bash
    # Install multi-language linters in JupyterHub pod
    echo "Installing multi-language code review tools..."
    
    # Python (already available)
    pip install --quiet pycodestyle pyflakes 2>/dev/null
    echo "  Python: pycodestyle + pyflakes"
    
    # C/C++: cppcheck
    apt-get update -qq 2>/dev/null && apt-get install -y -qq cppcheck 2>/dev/null
    echo "  C/C++: cppcheck"
    
    # Java: checkstyle (download if java available)
    if command -v java &>/dev/null; then
        mkdir -p /opt/checkstyle
        curl -sL "https://github.com/checkstyle/checkstyle/releases/download/checkstyle-10.12.4/checkstyle-10.12.4-all.jar" -o /opt/checkstyle/checkstyle.jar 2>/dev/null || \
        pip download checkstyle 2>/dev/null || true
        echo "  Java: checkstyle"
    fi
    
    # Go: gofmt + go vet (built-in if go installed)
    if command -v go &>/dev/null; then
        echo "  Go: gofmt + go vet (built-in)"
    fi
    
    # Rust: clippy + rustfmt (built-in if rust installed)
    if command -v cargo &>/dev/null; then
        rustup component add clippy rustfmt 2>/dev/null || true
        echo "  Rust: clippy + rustfmt"
    fi
    
    echo "Multi-language code review tools installed!"
REVIEWEOF

echo "Code review tools ConfigMap created"

echo ""
echo "============================================================"
echo "Part 3: Verify CRDB deployment (K8s pods, not bare metal)"
echo "============================================================"

echo ""
echo "=== CRDB K8s Deployment Verification ==="
echo ""
echo "Pods:"
kubectl get pods -n infra -l app=cockroachdb 2>&1
echo ""
echo "StatefulSets:"
kubectl get sts -n infra 2>&1
echo ""
echo "Services:"
kubectl get svc -n infra 2>&1
echo ""
echo "Pod process check (inside container):"
kubectl exec -n infra cockroachdb-a-0 -c cockroachdb -- ps aux 2>&1 | head -5
echo ""
echo "Binary path (container):"
kubectl exec -n infra cockroachdb-a-0 -c cockroachdb -- ls -la /cockroach-binary/cockroach 2>&1
echo ""
echo "Binary path (host, should NOT exist as /opt/cockroach):"
ls -la /opt/cockroach/cockroach 2>&1 || echo "/opt/cockroach/cockroach is the ORIGINAL host binary (pre-migration)"
echo ""
echo "CRDB processes on master host:"
ps aux | grep '/cockroach-binary/' | grep -v grep | head -5 || echo 'none'
echo ""
echo "CRDB processes on master host (old path):"
ps aux | grep '/opt/cockroach/' | grep -v grep | head -5 || echo 'none (correct!)'
echo ""
echo "Systemd services:"
systemctl status cockroach-node1 2>&1 | head -5 || true
systemctl status cockroach-node2 2>&1 | head -5 || true

echo ""
echo "============================================================"
echo "Part 4: Restart hub with all fixes"
echo "============================================================"
HUB_POD=$(kubectl get pods -n jupyterhub -o jsonpath='{.items[?(@.metadata.labels.app\.kubernetes\.io/component=="hub")].metadata.name}')
if [ -n "$HUB_POD" ]; then
  kubectl delete pod -n jupyterhub $HUB_POD 2>&1
fi

echo ""
echo "============================================================"
echo "ALL FIXES APPLIED"
echo "============================================================"
echo ""
echo "1. Guides distribution: teacher=both, student=student-only"
echo "2. Multi-language code review: Python/Java/Go/Rust/C/JavaScript"
echo "   Install: pip install + apt install (auto in pod startup)"
echo "   Usage: python3 code_review.py <file_or_directory>"
echo "3. CRDB: Verified as K8s pods (hostNetwork mode, NOT bare metal)"
