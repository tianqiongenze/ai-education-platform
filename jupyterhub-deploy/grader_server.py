"""
JupyterHub 项目评分 Web 服务
提供 Web 界面让学生提交项目并获取评分报告
运行在 JupyterHub Pod 中，端口 9999
"""
import os
import sys
import json
import subprocess
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# 导入评分系统
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grader import ProjectGrader

class GraderHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == "/" or parsed.path == "/grader":
            self.send_html(GRADER_PAGE)
        elif parsed.path == "/api/grade":
            params = parse_qs(parsed.query)
            project_path = params.get("path", [""])[0]
            language = params.get("lang", ["python"])[0]
            
            if not project_path or not os.path.exists(project_path):
                self.send_json({"error": "项目路径不存在"}, 400)
                return
            
            try:
                grader = ProjectGrader(project_path, language)
                report = grader.grade()
                self.send_json({
                    "total_score": report.total_score,
                    "grade": report.grade,
                    "timestamp": report.timestamp,
                    "results": [r.__dict__ for r in report.results],
                    "ai_review": report.ai_review,
                    "summary": report.summary,
                    "optimization_suggestions": report.optimization_suggestions,
                })
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/projects":
            # 列出 /home/jovyan/work 下的项目
            work_dir = Path("/home/jovyan/work")
            projects = []
            if work_dir.exists():
                for d in work_dir.iterdir():
                    if d.is_dir() and not d.name.startswith("."):
                        py_count = sum(1 for _ in d.rglob("*.py"))
                        java_count = sum(1 for _ in d.rglob("*.java"))
                        go_count = sum(1 for _ in d.rglob("*.go"))
                        if py_count + java_count + go_count > 0:
                            projects.append({
                                "name": d.name,
                                "path": str(d),
                                "python_files": py_count,
                                "java_files": java_count,
                                "go_files": go_count,
                            })
            self.send_json({"projects": projects})
        else:
            self.send_error(404)
    
    def send_html(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))
    
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    
    def log_message(self, format, *args):
        print(f"[{self.client_address[0]}] {format % args}")

GRADER_PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>项目评分系统</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:'Segoe UI',Arial,sans-serif; background:#0a1929; color:#e0e0e0; }
.header { background:linear-gradient(135deg,#0d2847,#1a3a5c); padding:20px; text-align:center; }
.header h1 { color:#fff; }
.container { max-width:900px; margin:20px auto; padding:20px; }
.card { background:#0d2847; border:1px solid #1e3a5f; border-radius:8px; padding:20px; margin-bottom:20px; }
.card h2 { color:#60a5fa; margin-bottom:15px; }
input,select,button { padding:10px; border-radius:4px; border:1px solid #1e3a5f; background:#1a1f2e; color:#fff; margin:5px; }
button { background:#2563eb; cursor:pointer; border:none; padding:10px 20px; }
button:hover { background:#1d4ed8; }
.result { background:#1a1f2e; padding:15px; border-radius:4px; margin-top:10px; white-space:pre-wrap; }
.score { font-size:48px; font-weight:bold; }
.grade-A { color:#00c896; } .grade-B { color:#60a5fa; } .grade-C { color:#ffb300; } .grade-D { color:#ff6b6b; } .grade-F { color:#ef4444; }
.bar { display:inline-block; height:12px; border-radius:6px; background:#2563eb; }
.bar-bg { display:inline-block; height:12px; width:100px; background:#1a1f2e; border-radius:6px; }
.project-list { list-style:none; }
.project-list li { padding:8px; border-bottom:1px solid #1e3a5f; cursor:pointer; }
.project-list li:hover { background:#1a1f2e; }
</style>
</head>
<body>
<div class="header"><h1>📋 项目自动评分系统</h1><p style="color:#60a5fa">代码分析 · 测试覆盖率 · 安全扫描 · AI 审查</p></div>
<div class="container">
  <div class="card">
    <h2>📂 选择项目</h2>
    <ul class="project-list" id="projects"></ul>
  </div>
  <div class="card">
    <h2>⚙️ 评分配置</h2>
    <input type="text" id="path" placeholder="项目路径 (/home/jovyan/work/myproject)" style="width:400px">
    <select id="lang"><option value="python">Python</option><option value="java">Java</option><option value="go">Go</option></select>
    <button onclick="grade()">开始评分</button>
  </div>
  <div class="card" id="result-card" style="display:none">
    <h2>📊 评分结果</h2>
    <div class="result" id="result"></div>
  </div>
</div>
<script>
async function loadProjects() {
  const r = await fetch('/api/projects');
  const data = await r.json();
  const el = document.getElementById('projects');
  if (data.projects.length === 0) {
    el.innerHTML = '<li>未找到项目，请在工作目录创建项目</li>';
  } else {
    el.innerHTML = data.projects.map(p =>
      `<li onclick="selectProject('${p.path}','${p.python_files>0?'python':p.java_files>0?'java':'go'}')">
        📁 ${p.name} (Python:${p.python_files} Java:${p.java_files} Go:${p.go_files})
      </li>`).join('');
  }
}
function selectProject(path, lang) {
  document.getElementById('path').value = path;
  document.getElementById('lang').value = lang;
}
async function grade() {
  const path = document.getElementById('path').value;
  const lang = document.getElementById('lang').value;
  if (!path) { alert('请输入项目路径'); return; }
  document.getElementById('result-card').style.display = 'block';
  document.getElementById('result').textContent = '⏳ 评分中... (可能需要1-2分钟)';
  try {
    const r = await fetch(`/api/grade?path=${encodeURIComponent(path)}&lang=${lang}`);
    const data = await r.json();
    if (data.error) {
      document.getElementById('result').textContent = '❌ 错误: ' + data.error;
      return;
    }
    let html = `<div class="score grade-${data.grade}">${data.total_score}分 - 等级${data.grade}</div><br>`;
    html += '<b>📊 详细评分:</b><br>';
    data.results.forEach(r => {
      const pct = r.max_score > 0 ? (r.score/r.max_score*100).toFixed(0) : 0;
      html += `${r.category}/${r.check_name}: <span class="bar-bg"><span class="bar" style="width:${pct}%"></span></span> ${r.score.toFixed(1)}/${r.max_score} - ${r.details}<br>`;
    });
    html += `<br><b>🤖 AI 审查:</b><br>${data.ai_review}<br>`;
    html += '<br><b>💡 优化建议:</b><br>';
    data.optimization_suggestions.forEach((s,i) => html += `${i+1}. ${s}<br>`);
    html += `<br><b>📝 摘要:</b><br>${data.summary}`;
    document.getElementById('result').innerHTML = html;
  } catch(e) {
    document.getElementById('result').textContent = '❌ 评分失败: ' + e;
  }
}
loadProjects();
</script>
</body>
</html>"""

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 9999), GraderHandler)
    print("项目评分系统运行在 http://localhost:9999")
    server.serve_forever()
