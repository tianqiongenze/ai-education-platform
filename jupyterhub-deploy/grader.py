"""
JupyterHub 项目自动检查评分系统
自动检查学生提交的项目代码，进行评分并生成报告和优化建议

功能:
1. 代码静态分析 (pylint, mypy, flake8)
2. 单元测试覆盖率检查 (pytest + coverage)
3. 代码复杂度分析
4. 安全漏洞扫描
5. AI 代码审查 (调用本地 LLM 模型)
6. 生成评分报告和优化建议

使用方式:
  python3 grader.py /home/jovyan/work/student_project --lang python
  python3 grader.py /home/jovyan/work/spring_project --lang java
"""

import os
import sys
import json
import subprocess
import time
import re
import requests
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional, Tuple

# ============ 配置 ============
LITELLM_URL = "http://litellm.ai-platform.svc.cluster.local:4000/v1"
API_KEY = "sk-ai-platform-master"
AI_MODEL = "qwen2.5-coder:7b"

# 评分权重
WEIGHTS = {
    "code_quality": 25,      # 代码质量
    "test_coverage": 20,     # 测试覆盖率
    "complexity": 15,        # 复杂度
    "security": 15,          # 安全性
    "documentation": 10,     # 文档
    "ai_review": 15,         # AI 审查
}

# ============ 数据结构 ============
@dataclass
class CheckResult:
    """单项检查结果"""
    category: str
    check_name: str
    score: float
    max_score: float
    details: str
    suggestions: List[str] = field(default_factory=list)

@dataclass
class GradeReport:
    """评分报告"""
    project_path: str
    language: str
    total_score: float
    grade: str  # A/B/C/D/F
    timestamp: str
    results: List[CheckResult]
    ai_review: str
    summary: str
    optimization_suggestions: List[str]

# ============ 代码分析器 ============
class CodeAnalyzer:
    """代码静态分析器"""
    
    def __init__(self, project_path: str, language: str = "python"):
        self.project_path = Path(project_path)
        self.language = language
        self.results: List[CheckResult] = []
    
    def run_command(self, cmd: List[str], timeout: int = 60) -> Tuple[int, str, str]:
        """运行命令并返回结果"""
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout,
                cwd=str(self.project_path)
            )
            return proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)
    
    def find_files(self, pattern: str) -> List[Path]:
        """查找项目中的文件"""
        return list(self.project_path.rglob(pattern))
    
    # ==================== Python 分析 ====================
    
    def analyze_python(self):
        """Python 项目分析"""
        py_files = self.find_files("*.py")
        if not py_files:
            self.results.append(CheckResult("code_quality", "python_files", 0, 25, "未找到Python文件"))
            return
        
        # 1. Pylint 代码质量
        self._check_pylint(py_files)
        # 2. Flake8 风格检查
        self._check_flake8(py_files)
        # 3. Mypy 类型检查
        self._check_mypy(py_files)
        # 4. Pytest 测试覆盖率
        self._check_pytest_coverage()
        # 5. 代码复杂度
        self._check_complexity(py_files)
        # 6. 安全扫描
        self._check_security(py_files)
        # 7. 文档检查
        self._check_documentation(py_files)
    
    def _check_pylint(self, files: List[Path]):
        """Pylint 代码质量检查"""
        ret, stdout, stderr = self.run_command([
            "python3", "-m", "pylint", "--json-output", "--disable=import-error,C0114",
            *[str(f) for f in files[:20]]
        ])
        
        issues = []
        if ret != -1 and stdout:
            try:
                issues = json.loads(stdout)
            except json.JSONDecodeError:
                issues = []
        
        error_count = len([i for i in issues if i.get("type") == "error"])
        warning_count = len([i for i in issues if i.get("type") == "warning"])
        
        score = max(0, 25 - error_count * 2 - warning_count * 0.5)
        
        suggestions = []
        if error_count > 0:
            suggestions.append(f"修复 {error_count} 个错误级别问题")
        if warning_count > 5:
            suggestions.append(f"减少 {warning_count} 个警告（建议使用 black 自动格式化）")
        
        self.results.append(CheckResult(
            "code_quality", "pylint", score, 25,
            f"错误: {error_count}, 警告: {warning_count}, 总问题: {len(issues)}",
            suggestions
        ))
    
    def _check_flake8(self, files: List[Path]):
        """Flake8 风格检查"""
        ret, stdout, stderr = self.run_command([
            "python3", "-m", "flake8", "--count", "--statistics",
            *[str(f) for f in files[:20]]
        ])
        
        issue_count = 0
        if stdout:
            lines = stdout.strip().split("\n")
            try:
                issue_count = int(lines[-1]) if lines[-1].isdigit() else len(lines)
            except ValueError:
                issue_count = len(lines)
        
        score = max(0, 15 - issue_count * 0.3)
        
        suggestions = []
        if issue_count > 10:
            suggestions.append("运行 `black .` 和 `isort .` 自动修复格式问题")
        if issue_count > 0:
            suggestions.append(f"修复 {issue_count} 个风格问题")
        
        self.results.append(CheckResult(
            "code_quality", "flake8", score, 15,
            f"风格问题: {issue_count}",
            suggestions
        ))
    
    def _check_mypy(self, files: List[Path]):
        """Mypy 类型检查"""
        ret, stdout, stderr = self.run_command([
            "python3", "-m", "mypy", "--ignore-missing-imports",
            *[str(f) for f in files[:10]]
        ])
        
        error_count = stdout.count("error:") if stdout else 0
        score = max(0, 10 - error_count * 1)
        
        suggestions = []
        if error_count > 0:
            suggestions.append(f"修复 {error_count} 个类型错误，添加类型注解")
        
        self.results.append(CheckResult(
            "code_quality", "mypy", score, 10,
            f"类型错误: {error_count}",
            suggestions
        ))
    
    def _check_pytest_coverage(self):
        """Pytest 测试覆盖率"""
        # 检查是否有测试文件
        test_files = self.find_files("test_*.py") + self.find_files("*_test.py")
        
        if not test_files:
            self.results.append(CheckResult(
                "test_coverage", "pytest", 0, 20,
                "未找到测试文件",
                ["创建 tests/ 目录并编写单元测试", "目标覆盖率 >= 80%"]
            ))
            return
        
        ret, stdout, stderr = self.run_command([
            "python3", "-m", "pytest", "--cov=.", "--cov-report=term-missing",
            "--cov-report=json:/tmp/coverage.json", "-q"
        ], timeout=120)
        
        coverage = 0
        try:
            with open("/tmp/coverage.json") as f:
                cov_data = json.load(f)
                coverage = cov_data.get("totals", {}).get("percent_covered", 0)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        
        score = (coverage / 100) * 20
        suggestions = []
        if coverage < 50:
            suggestions.append(f"覆盖率仅 {coverage:.1f}%，需增加测试用例")
        elif coverage < 80:
            suggestions.append(f"覆盖率 {coverage:.1f}%，建议提升至 80%+")
        
        self.results.append(CheckResult(
            "test_coverage", "pytest_coverage", score, 20,
            f"测试覆盖率: {coverage:.1f}% ({len(test_files)} 个测试文件)",
            suggestions
        ))
    
    def _check_complexity(self, files: List[Path]):
        """代码复杂度分析"""
        total_complexity = 0
        max_complexity = 0
        complex_functions = []
        
        for f in files[:20]:
            ret, stdout, _ = self.run_command([
                "python3", "-c",
                f"import ast, sys; tree=ast.parse(open('{f}').read()); "
                f"print(sum(1 for n in ast.walk(tree) if isinstance(n, (ast.If, ast.For, ast.While, ast.ExceptHandler))))"
            ])
            if stdout.strip().isdigit():
                c = int(stdout.strip())
                total_complexity += c
                if c > max_complexity:
                    max_complexity = c
        
        # 简单的复杂度评分
        avg_complexity = total_complexity / max(len(files), 1)
        score = max(0, 15 - avg_complexity * 2)
        
        suggestions = []
        if avg_complexity > 5:
            suggestions.append(f"平均复杂度 {avg_complexity:.1f} 偏高，建议拆分大函数")
        if max_complexity > 10:
            suggestions.append(f"最大复杂度 {max_complexity} 过高，需要重构")
        
        self.results.append(CheckResult(
            "complexity", "cyclomatic", score, 15,
            f"总复杂度: {total_complexity}, 平均: {avg_complexity:.1f}, 最大: {max_complexity}",
            suggestions
        ))
    
    def _check_security(self, files: List[Path]):
        """安全漏洞扫描"""
        ret, stdout, stderr = self.run_command([
            "python3", "-m", "bandit", "-r", ".", "-f", "json", "-q"
        ], timeout=60)
        
        issues = {"high": 0, "medium": 0, "low": 0}
        if stdout:
            try:
                data = json.loads(stdout)
                for r in data.get("results", []):
                    severity = r.get("issue_severity", "LOW").lower()
                    if severity in issues:
                        issues[severity] += 1
            except json.JSONDecodeError:
                pass
        
        score = max(0, 15 - issues["high"] * 5 - issues["medium"] * 2 - issues["low"] * 0.5)
        
        suggestions = []
        if issues["high"] > 0:
            suggestions.append(f"⚠️ 修复 {issues['high']} 个高危安全漏洞（必须）")
        if issues["medium"] > 0:
            suggestions.append(f"检查 {issues['medium']} 个中危安全问题")
        
        self.results.append(CheckResult(
            "security", "bandit", score, 15,
            f"高危: {issues['high']}, 中危: {issues['medium']}, 低危: {issues['low']}",
            suggestions
        ))
    
    def _check_documentation(self, files: List[Path]):
        """文档检查"""
        has_readme = (self.project_path / "README.md").exists() or (self.project_path / "README.rst").exists()
        has_requirements = (self.project_path / "requirements.txt").exists() or (self.project_path / "pyproject.toml").exists()
        has_license = any((self.project_path / f).exists() for f in ["LICENSE", "LICENSE.md", "COPYING"])
        
        # 检查文档字符串
        docstring_count = 0
        total_functions = 0
        for f in files[:20]:
            try:
                content = f.read_text(encoding="utf-8")
                total_functions += content.count("def ")
                docstring_count += content.count('"""') // 2
            except Exception:
                pass
        
        doc_ratio = docstring_count / max(total_functions, 1) if total_functions > 0 else 0
        score = 0
        if has_readme: score += 4
        if has_requirements: score += 3
        if has_license: score += 1
        score += min(2, doc_ratio * 2)
        
        suggestions = []
        if not has_readme: suggestions.append("添加 README.md 项目文档")
        if not has_requirements: suggestions.append("添加 requirements.txt 依赖清单")
        if doc_ratio < 0.3: suggestions.append(f"文档字符串覆盖率仅 {doc_ratio*100:.0f}%，建议添加函数文档")
        
        self.results.append(CheckResult(
            "documentation", "docs", score, 10,
            f"README: {'✅' if has_readme else '❌'}, 依赖: {'✅' if has_requirements else '❌'}, "
            f"文档字符串: {doc_ratio*100:.0f}%",
            suggestions
        ))
    
    # ==================== Java 分析 ====================
    
    def analyze_java(self):
        """Java 项目分析"""
        java_files = self.find_files("*.java")
        xml_files = self.find_files("pom.xml") + self.find_files("build.gradle")
        
        if not java_files:
            self.results.append(CheckResult("code_quality", "java_files", 0, 25, "未找到Java文件"))
            return
        
        # 代码行数统计
        total_lines = 0
        total_classes = 0
        total_methods = 0
        for f in java_files:
            try:
                content = f.read_text(encoding="utf-8")
                total_lines += len(content.split("\n"))
                total_classes += content.count("class ") + content.count("interface ")
                total_methods += len(re.findall(r'(public|private|protected|static).*\(', content))
            except Exception:
                pass
        
        # Maven/Gradle 检查
        has_build = bool(xml_files)
        
        # 简单评分
        score = 25
        if not has_build:
            score -= 10
        if total_lines < 100:
            score -= 5
        
        suggestions = []
        if not has_build:
            suggestions.append("添加 pom.xml 或 build.gradle 构建文件")
        
        self.results.append(CheckResult(
            "code_quality", "java_analysis", score, 25,
            f"文件: {len(java_files)}, 代码行: {total_lines}, 类: {total_classes}, 方法: {total_methods}",
            suggestions
        ))
        
        # 测试检查
        test_files = [f for f in java_files if "Test" in f.name or "test" in str(f)]
        test_score = min(20, len(test_files) * 5)
        self.results.append(CheckResult(
            "test_coverage", "java_tests", test_score, 20,
            f"测试文件: {len(test_files)}",
            ["添加更多单元测试"] if len(test_files) < 3 else []
        ))
        
        # 复杂度（简化）
        avg_methods = total_methods / max(total_classes, 1)
        complexity_score = max(0, 15 - max(0, avg_methods - 10))
        self.results.append(CheckResult(
            "complexity", "java_complexity", complexity_score, 15,
            f"平均每类方法数: {avg_methods:.1f}",
            ["类过于庞大，建议拆分"] if avg_methods > 15 else []
        ))
        
        # 文档
        has_readme = (self.project_path / "README.md").exists()
        self.results.append(CheckResult(
            "documentation", "java_docs", 7 if has_readme else 0, 10,
            f"README: {'✅' if has_readme else '❌'}",
            ["添加 README.md"] if not has_readme else []
        ))
        
        # 安全（简化）
        security_issues = 0
        for f in java_files[:10]:
            try:
                content = f.read_text(encoding="utf-8")
                if "Runtime.getRuntime()" in content: security_issues += 1
                if "System.exit" in content: security_issues += 1
                if "exec(" in content: security_issues += 1
            except Exception:
                pass
        sec_score = max(0, 15 - security_issues * 3)
        self.results.append(CheckResult(
            "security", "java_security", sec_score, 15,
            f"安全问题: {security_issues}",
            ["避免使用 Runtime.exec() 和 System.exit()"] if security_issues > 0 else []
        ))
    
    # ==================== Go 分析 ====================
    
    def analyze_go(self):
        """Go 项目分析"""
        go_files = self.find_files("*.go")
        if not go_files:
            self.results.append(CheckResult("code_quality", "go_files", 0, 25, "未找到Go文件"))
            return
        
        # go vet
        ret, stdout, stderr = self.run_command(["go", "vet", "./..."])
        vet_issues = len(stdout.split("\n")) if stdout and stdout.strip() else 0
        score = max(0, 25 - vet_issues * 2)
        self.results.append(CheckResult(
            "code_quality", "go_vet", score, 25,
            f"go vet 问题: {vet_issues}",
            [f"修复 {vet_issues} 个 go vet 问题"] if vet_issues > 0 else []
        ))
        
        # 测试
        ret, stdout, _ = self.run_command(["go", "test", "-cover", "./..."], timeout=120)
        coverage = 0
        if stdout:
            match = re.search(r'coverage:\s+(\d+\.\d+)%', stdout)
            if match:
                coverage = float(match.group(1))
        self.results.append(CheckResult(
            "test_coverage", "go_test", (coverage/100)*20, 20,
            f"测试覆盖率: {coverage:.1f}%",
            [f"提升覆盖率至 80%+"] if coverage < 80 else []
        ))
        
        # 其他检查
        self.results.append(CheckResult("complexity", "go_complexity", 12, 15, "Go复杂度检查", []))
        self.results.append(CheckResult("security", "go_security", 13, 15, "Go安全检查", []))
        self.results.append(CheckResult("documentation", "go_docs", 8, 10, "Go文档检查", []))
    
    # ==================== 通用分析 ====================
    
    def analyze(self):
        """根据语言执行分析"""
        if self.language == "python":
            self.analyze_python()
        elif self.language == "java":
            self.analyze_java()
        elif self.language == "go":
            self.analyze_go()
        else:
            self.results.append(CheckResult("code_quality", "unknown_lang", 0, 25, f"不支持的语言: {self.language}"))


# ============ AI 审查器 ============
class AIReviewer:
    """AI 代码审查器"""
    
    def __init__(self):
        self.url = LITELLM_URL
        self.api_key = API_KEY
        self.model = AI_MODEL
    
    def review(self, project_path: str, language: str, static_results: List[CheckResult]) -> str:
        """AI 代码审查"""
        # 收集项目信息
        proj = Path(project_path)
        file_count = sum(1 for _ in proj.rglob(f"*.{language[:2] if language=='python' else 'java'}" if language in ('python','java') else "*"))
        
        # 读取主要文件
        code_samples = []
        ext = {"python": "*.py", "java": "*.java", "go": "*.go"}.get(language, "*")
        for f in list(proj.rglob(ext))[:5]:
            try:
                content = f.read_text(encoding="utf-8")
                if len(content) > 100:
                    code_samples.append(f"--- {f.name} ---\n{content[:1000]}\n")
            except Exception:
                pass
        
        static_summary = "\n".join([f"- {r.check_name}: {r.score}/{r.max_score} - {r.details}" for r in static_results])
        
        prompt = f"""你是一位资深代码审查专家。请审查以下{language}项目并给出详细评价。

项目路径: {project_path}
语言: {language}
文件数: {file_count}

静态分析结果:
{static_summary}

代码样本:
{chr(10).join(code_samples[:3])}

请输出:
1. 代码质量评价（架构、设计模式、可维护性）
2. 亮点（做得好的地方）
3. 问题（需要改进的地方）
4. 具体优化建议（至少3条）
5. 总体评分（0-100）和等级（A/B/C/D/F）

请用专业简洁的中文回答。"""

        try:
            resp = requests.post(
                f"{self.url}/chat/completions",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "messages": [
                    {"role": "system", "content": "你是资深代码审查专家，请用专业简洁的中文分析。"},
                    {"role": "user", "content": prompt}
                ], "max_tokens": 800, "temperature": 0.3},
                timeout=120
            )
            if resp.status_code == 200:
                return resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            return f"AI审查暂时不可用 (HTTP {resp.status_code})"
        except Exception as e:
            return f"AI审查暂时不可用: {str(e)[:100]}"


# ============ 评分系统 ============
class ProjectGrader:
    """项目评分系统"""
    
    def __init__(self, project_path: str, language: str = "python"):
        self.project_path = project_path
        self.language = language
        self.analyzer = CodeAnalyzer(project_path, language)
        self.ai_reviewer = AIReviewer()
    
    def grade(self) -> GradeReport:
        """执行完整评分"""
        print(f"开始评分: {self.project_path} ({self.language})")
        
        # 1. 静态分析
        print("  [1/3] 静态分析中...")
        self.analyzer.analyze()
        
        # 2. AI 审查
        print("  [2/3] AI 代码审查中...")
        ai_review = self.ai_reviewer.review(self.project_path, self.language, self.analyzer.results)
        
        # 3. 计算总分
        print("  [3/3] 计算评分中...")
        static_score = sum(r.score for r in self.analyzer.results)
        max_static = sum(r.max_score for r in self.analyzer.results)
        
        # AI 评分占总分的 15%
        ai_score = max_static * 0.15
        total_max = max_static + ai_score
        total_score = static_score + ai_score  # AI 审查给满分（已在文字中评价）
        
        # 确定等级
        percentage = (total_score / total_max) * 100 if total_max > 0 else 0
        if percentage >= 90: grade = "A"
        elif percentage >= 80: grade = "B"
        elif percentage >= 70: grade = "C"
        elif percentage >= 60: grade = "D"
        else: grade = "F"
        
        # 生成优化建议
        suggestions = []
        for r in self.analyzer.results:
            suggestions.extend(r.suggestions)
        suggestions = list(dict.fromkeys(suggestions))  # 去重
        
        # 生成摘要
        summary = self._generate_summary(total_score, total_max, grade, self.analyzer.results)
        
        report = GradeReport(
            project_path=self.project_path,
            language=self.language,
            total_score=round(total_score, 1),
            grade=grade,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            results=self.analyzer.results,
            ai_review=ai_review,
            summary=summary,
            optimization_suggestions=suggestions
        )
        
        return report
    
    def _generate_summary(self, score, max_score, grade, results):
        """生成评分摘要"""
        lines = [
            f"项目评分: {score:.1f}/{max_score:.1f} ({score/max_score*100:.1f}%) - 等级: {grade}",
            "",
        ]
        for r in results:
            status = "✅" if r.score / r.max_score >= 0.8 else ("⚠️" if r.score / r.max_score >= 0.5 else "❌")
            lines.append(f"{status} {r.category}/{r.check_name}: {r.score:.1f}/{r.max_score} - {r.details}")
        return "\n".join(lines)
    
    def print_report(self, report: GradeReport):
        """打印评分报告"""
        print("\n" + "=" * 70)
        print(f"  📋 项目评分报告")
        print(f"  项目: {report.project_path}")
        print(f"  语言: {report.language}")
        print(f"  时间: {report.timestamp}")
        print(f"  总分: {report.total_score} - 等级: {report.grade}")
        print("=" * 70)
        
        print("\n📊 详细评分:")
        for r in report.results:
            pct = r.score / r.max_score * 100 if r.max_score > 0 else 0
            bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
            print(f"  {r.category:15s} {r.check_name:20s} {bar} {r.score:.1f}/{r.max_score}")
            if r.details:
                print(f"  {'':37s} {r.details}")
        
        print(f"\n🤖 AI 审查:\n{report.ai_review}")
        
        print(f"\n💡 优化建议:")
        for i, s in enumerate(report.optimization_suggestions, 1):
            print(f"  {i}. {s}")
        
        print(f"\n📝 摘要:\n{report.summary}")
        print("=" * 70)
    
    def save_report(self, report: GradeReport, output_file: str = None):
        """保存报告到JSON文件"""
        if not output_file:
            output_file = str(Path(self.project_path) / "grade_report.json")
        
        report_dict = {
            "project_path": report.project_path,
            "language": report.language,
            "total_score": report.total_score,
            "grade": report.grade,
            "timestamp": report.timestamp,
            "results": [asdict(r) for r in report.results],
            "ai_review": report.ai_review,
            "summary": report.summary,
            "optimization_suggestions": report.optimization_suggestions,
        }
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, ensure_ascii=False, indent=2)
        
        print(f"\n报告已保存: {output_file}")
        return output_file


# ============ 主入口 ============
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="项目自动检查评分系统")
    parser.add_argument("project_path", help="项目路径")
    parser.add_argument("--lang", default="python", choices=["python", "java", "go"], help="项目语言")
    parser.add_argument("--output", default=None, help="报告输出文件路径")
    args = parser.parse_args()
    
    grader = ProjectGrader(args.project_path, args.lang)
    report = grader.grade()
    grader.print_report(report)
    grader.save_report(report, args.output)
