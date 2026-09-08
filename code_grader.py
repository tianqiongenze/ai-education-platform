#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Code Grading System - 代码评分系统
Supports: plagiarism detection (查重), AI-generated detection (AI率),
PEP8 compliance, test pass rate, comprehensive report generation.
"""
import ast
import difflib
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Tuple

@dataclass
class GradeResult:
    student_id: str
    project_name: str
    code_files: List[str] = field(default_factory=list)
    total_lines: int = 0
    pep8_score: float = 0.0
    test_pass_rate: float = 0.0
    plagiarism_score: float = 0.0  # 0=original, 100=fully copied
    ai_detection_score: float = 0.0  # 0=human-like, 100=AI-generated
    overall_grade: str = "F"
    report: Dict = field(default_factory=dict)

class CodeGrader:
    """Main grading engine."""

    def __init__(self, work_dir="/home/jovyan/work"):
        self.work_dir = work_dir
        self.results = []

    def grade_project(self, student_id, project_dir, project_name):
        """Grade a single project."""
        result = GradeResult(student_id=student_id, project_name=project_name)

        # Collect Python files
        py_files = []
        for root, dirs, files in os.walk(project_dir):
            if 'target' in root or '__pycache__' in root or '.git' in root:
                continue
            for f in files:
                if f.endswith('.py'):
                    py_files.append(os.path.join(root, f))
        result.code_files = py_files
        result.total_lines = sum(self._count_lines(f) for f in py_files)

        # PEP8 score
        result.pep8_score = self._check_pep8(py_files)

        # Test pass rate
        result.test_pass_rate = self._run_tests(project_dir)

        # Plagiarism check (against other students' code)
        result.plagiarism_score = self._check_plagiarism(project_dir, student_id)

        # AI detection
        result.ai_detection_score = self._detect_ai_generated(py_files)

        # Overall grade
        result.overall_grade = self._calculate_grade(result)
        result.report = self._generate_report(result)

        self.results.append(result)
        return result

    def _count_lines(self, filepath):
        try:
            with open(filepath) as f:
                return sum(1 for line in f if line.strip())
        except:
            return 0

    def _check_pep8(self, py_files):
        """Check PEP8 compliance using pycodestyle."""
        if not py_files:
            return 0.0
        try:
            import pycodestyle
            checker = pycodestyle.StyleGuide(quiet=True)
            total_errors = 0
            total_lines = 0
            for f in py_files:
                with open(f) as fh:
                    total_lines += sum(1 for _ in fh)
                result = checker.check_files([f])
                total_errors += result.total_errors
            if total_lines == 0:
                return 0.0
            score = max(0, 100 - (total_errors / max(total_lines, 1) * 100))
            return round(score, 1)
        except ImportError:
            # Fallback: basic checks
            score = 100.0
            for f in py_files:
                with open(f) as fh:
                    for line in fh:
                        if '\t' in line:  # Tabs instead of spaces
                            score -= 1
                        if len(line) > 120:  # Line too long
                            score -= 0.5
            return round(max(0, score), 1)

    def _run_tests(self, project_dir):
        """Run pytest and return pass rate."""
        try:
            result = subprocess.run(
                ['python3', '-m', 'pytest', '--tb=no', '-q'],
                capture_output=True, text=True,
                cwd=project_dir,
                timeout=60,
                env={**os.environ, 'PYTHONPATH': project_dir}
            )
            output = result.stdout + result.stderr
            # Parse: "5 passed" or "3 passed, 2 failed"
            passed = len(re.findall(r'\b(\d+)\s+passed\b', output))
            failed = len(re.findall(r'\b(\d+)\s+failed\b', output))
            total = passed + failed
            if total == 0:
                return 0.0
            return round(passed / total * 100, 1)
        except Exception:
            return 0.0

    def _check_plagiarism(self, project_dir, student_id):
        """Check plagiarism by comparing code structure with other projects."""
        # Simple approach: hash normalized code and compare
        own_hash = self._project_hash(project_dir)
        similar_count = 0
        total_compared = 0

        # Compare with other projects in work dir
        for other_dir in os.listdir(self.work_dir):
            other_path = os.path.join(self.work_dir, other_dir)
            if not os.path.isdir(other_path) or other_path == project_dir:
                continue
            if 'industrial' in other_dir or 'security' in other_dir or 'mes' in other_dir:
                other_hash = self._project_hash(other_path)
                if other_hash:
                    total_compared += 1
                    similarity = self._similarity(project_dir, other_path)
                    if similarity > 0.7:
                        similar_count += 1

        if total_compared == 0:
            return 0.0
        return round(similar_count / total_compared * 100, 1)

    def _project_hash(self, project_dir):
        """Generate a hash of normalized code in project."""
        code_parts = []
        for root, dirs, files in os.walk(project_dir):
            if 'target' in root or '__pycache__' in root:
                continue
            for f in sorted(files):
                if f.endswith('.py'):
                    try:
                        with open(os.path.join(root, f)) as fh:
                            code = fh.read()
                            # Normalize: remove comments, whitespace
                            normalized = re.sub(r'#.*', '', code)
                            normalized = re.sub(r'\s+', ' ', normalized).strip()
                            code_parts.append(normalized)
                    except:
                        pass
        if not code_parts:
            return None
        combined = '\n'.join(code_parts)
        return hashlib.md5(combined.encode()).hexdigest()

    def _similarity(self, dir1, dir2):
        """Calculate code similarity between two directories."""
        files1 = self._get_all_code(dir1)
        files2 = self._get_all_code(dir2)
        if not files1 or not files2:
            return 0.0
        # Compare using difflib
        code1 = '\n'.join(files1)
        code2 = '\n'.join(files2)
        ratio = difflib.SequenceMatcher(None, code1, code2).ratio()
        return ratio

    def _get_all_code(self, directory):
        """Get all Python code as a list of strings."""
        code = []
        for root, dirs, files in os.walk(directory):
            if 'target' in root or '__pycache__' in root:
                continue
            for f in sorted(files):
                if f.endswith('.py'):
                    try:
                        with open(os.path.join(root, f)) as fh:
                            code.append(fh.read())
                    except:
                        pass
        return code

    def _detect_ai_generated(self, py_files):
        """Detect if code is AI-generated using heuristics."""
        ai_indicators = 0
        total_checks = 0
        for f in py_files:
            try:
                with open(f) as fh:
                    content = fh.read()
                    lines = content.split('\n')
                    total_checks += 10

                    # Check 1: Perfect docstrings on every function
                    try:
                        tree = ast.parse(content)
                        for node in ast.walk(tree):
                            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                                total_checks += 1
                                ds = ast.get_docstring(node)
                                if ds and len(ds) > 20 and ds[0].isupper():
                                    ai_indicators += 1  # Perfect docstring
                    except:
                        pass

                    # Check 2: Consistent type hints everywhere
                    if '-> ' in content or ': str' in content or ': int' in content:
                        type_hint_count = content.count('-> ') + content.count(': str') + content.count(': int')
                        if type_hint_count > 5:
                            ai_indicators += 2  # Heavy type hints

                    # Check 3: Very clean formatting (no PEP8 violations)
                    violations = 0
                    for line in lines:
                        if '\t' in line: violations += 1
                        if len(line) > 120: violations += 1
                    if violations == 0 and len(lines) > 20:
                        ai_indicators += 1

                    # Check 4: Comments explaining obvious things
                    comment_ratio = sum(1 for l in lines if l.strip().startswith('#')) / max(len(lines), 1)
                    if comment_ratio > 0.15:  # >15% comments
                        ai_indicators += 2

                    # Check 5: Perfect error handling everywhere
                    try_count = content.count('try:')
                    except_count = content.count('except')
                    if try_count > 3 and try_count == except_count:
                        ai_indicators += 2  # Perfect try/except pairing

            except:
                pass

        if total_checks == 0:
            return 0.0
        score = min(100, (ai_indicators / total_checks) * 100)
        return round(score, 1)

    def _calculate_grade(self, result):
        """Calculate overall letter grade."""
        score = (
            result.pep8_score * 0.2 +
            result.test_pass_rate * 0.4 +
            (100 - result.plagiarism_score) * 0.2 +
            (100 - result.ai_detection_score) * 0.2
        )
        if score >= 90: return "A"
        if score >= 80: return "B"
        if score >= 70: return "C"
        if score >= 60: return "D"
        return "F"

    def _generate_report(self, result):
        """Generate detailed report for a student."""
        return {
            "student_id": result.student_id,
            "project": result.project_name,
            "code_files": len(result.code_files),
            "total_lines": result.total_lines,
            "scores": {
                "pep8_compliance": result.pep8_score,
                "test_pass_rate": result.test_pass_rate,
                "originality": 100 - result.plagiarism_score,
                "human_authorship": 100 - result.ai_detection_score,
            },
            "plagiarism_score": result.plagiarism_score,
            "ai_detection_score": result.ai_detection_score,
            "overall_grade": result.overall_grade,
            "feedback": self._feedback(result),
        }

    def _feedback(self, r):
        feedbacks = []
        if r.pep8_score < 75:
            feedbacks.append("PEP8 规范性不足，建议使用 pylint 改进代码风格")
        if r.test_pass_rate < 100:
            feedbacks.append(f"测试通过率 {r.test_pass_rate}%，请修复失败的测试用例")
        if r.plagiarism_score > 30:
            feedbacks.append(f"查重率 {r.plagiarism_score}%，疑似重复代码较多")
        if r.ai_detection_score > 60:
            feedbacks.append(f"AI 率 {r.ai_detection_score}%，代码风格疑似 AI 生成")
        if not feedbacks:
            feedbacks.append("各项指标均达标，代码质量优秀！")
        return feedbacks

    def generate_summary_report(self):
        """Generate a summary report for all graded students."""
        report = {
            "report_date": __import__('datetime').datetime.now().isoformat(),
            "total_students": len(self.results),
            "grade_distribution": {},
            "average_scores": {},
            "students": [],
        }

        grades = [r.overall_grade for r in self.results]
        for g in ['A', 'B', 'C', 'D', 'F']:
            report["grade_distribution"][g] = grades.count(g)

        if self.results:
            report["average_scores"] = {
                "pep8": round(sum(r.pep8_score for r in self.results) / len(self.results), 1),
                "test_pass": round(sum(r.test_pass_rate for r in self.results) / len(self.results), 1),
                "originality": round(sum(100 - r.plagiarism_score for r in self.results) / len(self.results), 1),
                "human_authorship": round(sum(100 - r.ai_detection_score for r in self.results) / len(self.results), 1),
            }

        for r in self.results:
            report["students"].append(r.report)

        return report


def main():
    """Main: grade all projects and generate reports."""
    grader = CodeGrader(work_dir="/home/jovyan/work")

    # Grade all 4 projects
    projects = [
        ("student-python", "/home/jovyan/work/industrial-analytics", "industrial-analytics"),
        ("student-java", "/home/jovyan/work/mes-system", "mes-system"),
        ("student-go", "/home/jovyan/work/industrial-gateway", "industrial-gateway"),
        ("student-rust", "/home/jovyan/work/security-audit", "security-audit"),
    ]

    print("=" * 70)
    print("代码评分系统 - 评分报告")
    print("=" * 70)

    for student_id, project_dir, project_name in projects:
        if os.path.exists(project_dir):
            print(f"\n评分: {student_id} - {project_name}")
            result = grader.grade_project(student_id, project_dir, project_name)
            print(f"  等级: {result.overall_grade}")
            print(f"  PEP8: {result.pep8_score}%")
            print(f"  测试通过率: {result.test_pass_rate}%")
            print(f"  查重率: {result.plagiarism_score}%")
            print(f"  AI率: {result.ai_detection_score}%")
            print(f"  反馈: {result.report.get('feedback', [])}")
        else:
            print(f"\n跳过: {student_id} - {project_name} (目录不存在)")

    # Generate summary report
    summary = grader.generate_summary_report()
    report_path = "/home/jovyan/work/grading_report.json"
    with open(report_path, 'w') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("评分汇总")
    print("=" * 70)
    print(f"总学生数: {summary['total_students']}")
    print(f"等级分布: {summary['grade_distribution']}")
    if summary.get("average_scores"):
        print(f"平均分:")
        for k, v in summary["average_scores"].items():
            print(f"  {k}: {v}")
    print(f"\n详细报告已保存到: {report_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
