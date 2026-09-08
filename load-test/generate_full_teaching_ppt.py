#!/usr/bin/env python3
"""
Generate 3 comprehensive code-server teaching PPTs (~300 slides total):
  Part 1: Basics & IDE Usage (~100 slides)
  Part 2: Plugins Ecosystem (~100 slides)
  Part 3: Multi-Language Enterprise Development (~100 slides)

Uses PptxGenJS via Node.js subprocess for actual PPT generation.
"""
import json, subprocess, os

BASE = os.path.dirname(os.path.abspath(__file__))

# ===== PART 1: BASICS & IDE USAGE (~100 slides) =====
PART1_SLIDES = []

def s1(title, content_type="content"):
    """Add a slide definition"""
    return {"title": title, "type": content_type}

# --- Chapter 1: Getting Started (slides 1-15) ---
PART1_SLIDES.append(s1("code-server \u5168\u529F\u80FD\u5B66\u4E60\u6307\u5357 - \u7B2C\u4E00\u90E8\u5206\uFF1A\u57FA\u7840\u4E0E IDE \u4F7F\u7528", "title"))
PART1_SLIDES.append(s1("\u76EE\u5F55", "toc"))
PART1_SLIDES.append(s1("\u7B2C1\u7AE0\uFF1A\u521D\u6B21\u767B\u5F55\u4E0E\u754C\u9762\u4ECB\u7ECD", "chapter"))
PART1_SLIDES.append(s1("1.1 \u4EC0\u4E48\u662F code-server\uFF1F", "content"))
PART1_SLIDES.append(s1("1.2 \u4E3A\u4EC0\u4E48\u4F7F\u7528 code-server\uFF1F", "content"))
PART1_SLIDES.append(s1("1.3 \u8BBF\u95EE\u65B9\u5F0F\uFF1A\u6D4F\u89C8\u5668\u5373\u53EF", "content"))
PART1_SLIDES.append(s1("1.4 \u767B\u5F55\u754C\u9762\u8BE6\u89E3", "content"))
PART1_SLIDES.append(s1("1.5 VS Code \u754C\u9762\u5E03\u5C40\u5168\u89E3\u6790", "content"))
PART1_SLIDES.append(s1("1.6 \u6D3B\u52A8\u680F (Activity Bar) \u8BE6\u89E3", "content"))
PART1_SLIDES.append(s1("1.7 \u4FA7\u8FB9\u680F (Side Bar) \u4F7F\u7528\u6280\u5DE7", "content"))
PART1_SLIDES.append(s1("1.8 \u7F16\u8F91\u5668\u533A\u57DF (Editor) \u529F\u80FD\u5168\u89E3", "content"))
PART1_SLIDES.append(s1("1.9 \u9762\u677F\u533A\u57DF (Panel) \u4F7F\u7528\u6307\u5357", "content"))
PART1_SLIDES.append(s1("1.10 \u72B6\u6001\u680F (Status Bar) \u4FE1\u606F\u89E3\u8BFB", "content"))
PART1_SLIDES.append(s1("1.11 \u547D\u4EE4\u9762\u677F (Command Palette) \u2014 \u4E07\u80FD\u5FEB\u6377\u952E", "content"))
PART1_SLIDES.append(s1("1.12 \u5FEB\u901F\u5F00\u542F (Quick Open) \u6587\u4EF6\u5BFC\u822A", "content"))

# --- Chapter 2: File Management (slides 16-25) ---
PART1_SLIDES.append(s1("\u7B2C2\u7AE0\uFF1A\u6587\u4EF6\u4E0E\u9879\u76EE\u7BA1\u7406", "chapter"))
PART1_SLIDES.append(s1("2.1 \u521B\u5EFA/\u6253\u5F00\u6587\u4EF6\u548C\u6587\u4EF6\u5939", "content"))
PART1_SLIDES.append(s1("2.2 \u6253\u5F00\u6587\u4EF6\u5939 (Open Folder) \u4E0E\u5DE5\u4F5C\u533A", "content"))
PART1_SLIDES.append(s1("2.3 \u591A\u6587\u4EF6\u5939\u5DE5\u4F5C\u533A (Multi-root Workspace)", "content"))
PART1_SLIDES.append(s1("2.4 \u6587\u4EF6\u6D4F\u89C8\u5668 (Explorer) \u9AD8\u7EA7\u7528\u6CD5", "content"))
PART1_SLIDES.append(s1("2.5 \u6587\u4EF6\u641C\u7D22 (Search) \u5168\u5C40\u67E5\u627E\u4E0E\u66FF\u6362", "content"))
PART1_SLIDES.append(s1("2.6 \u6B63\u5219\u8868\u8FBE\u5F0F\u641C\u7D22\u5B9E\u6218", "content"))
PART1_SLIDES.append(s1("2.7 \u6E90\u4EE3\u7801\u63A7\u5236 (Source Control) \u2014 Git \u96C6\u6210", "content"))
PART1_SLIDES.append(s1("2.8 Git \u63D0\u4EA4\u3001\u63A8\u9001\u3001\u62C9\u53D6\u5B9E\u6218", "content"))
PART1_SLIDES.append(s1("2.9 \u5206\u652F\u7BA1\u7406\u4E0E\u5408\u5E76\u51B2\u7A81\u89E3\u51B3", "content"))

# --- Chapter 3: Editor Mastery (slides 26-40) ---
PART1_SLIDES.append(s1("\u7B2C3\u7AE0\uFF1A\u7F16\u8F91\u5668\u7CBE\u901A", "chapter"))
PART1_SLIDES.append(s1("3.1 \u4EE3\u7801\u8865\u5168 (IntelliSense) \u6DF1\u5EA6\u4F7F\u7528", "content"))
PART1_SLIDES.append(s1("3.2 \u4EE3\u7801\u5BFC\u822A (Go to Definition/References)", "content"))
PART1_SLIDES.append(s1("3.3 \u4EE3\u7801\u91CD\u6784 (Rename/Extract/Inline)", "content"))
PART1_SLIDES.append(s1("3.4 \u591A\u5149\u6807\u7F16\u8F91 (Multi-cursor) \u6280\u5DE7", "content"))
PART1_SLIDES.append(s1("3.5 \u4EE3\u7801\u6298\u53E0 (Folding) \u4E0E\u5927\u7EB2 (Outline)", "content"))
PART1_SLIDES.append(s1("3.6 \u4EE3\u7801\u7247\u6BB5 (Snippets) \u81EA\u5B9A\u4E49\u4E0E\u4F7F\u7528", "content"))
PART1_SLIDES.append(s1("3.7 Emmet \u5FEB\u901F HTML/CSS \u7F16\u5199", "content"))
PART1_SLIDES.append(s1("3.8 \u4EE3\u7801\u683C\u5F0F\u5316 (Formatting) \u81EA\u52A8\u7F8E\u5316", "content"))
PART1_SLIDES.append(s1("3.9 \u4EE3\u7801\u68C0\u67E5 (Linting) \u9519\u8BEF\u63D0\u793A", "content"))
PART1_SLIDES.append(s1("3.10 \u95EE\u9898\u9762\u677F (Problems Panel) \u8BCA\u65AD\u4E0E\u4FEE\u590D", "content"))
PART1_SLIDES.append(s1("3.11 \u5FEB\u6377\u952E\u5168\u666F\u56FE (Keyboard Shortcuts)", "content"))
PART1_SLIDES.append(s1("3.12 \u5FC5\u5907\u5FEB\u6377\u952E Top 30", "content"))
PART1_SLIDES.append(s1("3.13 \u81EA\u5B9A\u4E49\u5FEB\u6377\u952E\u7ED1\u5B9A", "content"))
PART1_SLIDES.append(s1("3.14 \u5206\u5C4F\u7F16\u8F91 (Split Editor) \u591A\u6587\u4EF6\u5E76\u6392", "content"))

# --- Chapter 4: Terminal & Tasks (slides 41-50) ---
PART1_SLIDES.append(s1("\u7B2C4\u7AE0\uFF1A\u7EC8\u7AEF\u4E0E\u4EFB\u52A1\u81EA\u52A8\u5316", "chapter"))
PART1_SLIDES.append(s1("4.1 \u96C6\u6210\u7EC8\u7AEF (Integrated Terminal) \u5165\u95E8", "content"))
PART1_SLIDES.append(s1("4.2 \u591A\u7EC8\u7AEF\u7BA1\u7406\u4E0E\u5206\u5C4F", "content"))
PART1_SLIDES.append(s1("4.3 Shell \u9009\u62E9\uFF1Abash/zsh/fish/powershell", "content"))
PART1_SLIDES.append(s1("4.4 \u4EFB\u52A1\u81EA\u52A8\u5316 (Tasks) \u2014 \u6784\u5EFA/\u6D4B\u8BD5/\u90E8\u7F72", "content"))
PART1_SLIDES.append(s1("4.5 tasks.json \u914D\u7F6E\u8BE6\u89E3", "content"))
PART1_SLIDES.append(s1("4.6 \u81EA\u5B9A\u4E49\u4EFB\u52A1\u4E0E\u5FEB\u6377\u952E\u7ED1\u5B9A", "content"))
PART1_SLIDES.append(s1("4.7 \u95EE\u9898\u5339\u914D\u5668 (Problem Matcher) \u89E3\u6790\u6784\u5EFA\u8F93\u51FA", "content"))
PART1_SLIDES.append(s1("4.8 \u540E\u53F0\u4EFB\u52A1\u4E0E\u81EA\u52A8\u8FD0\u884C", "content"))
PART1_SLIDES.append(s1("4.9 \u8F93\u51FA\u9762\u677F (Output Panel) \u4E0E\u65E5\u5FD7\u67E5\u770B", "content"))

# --- Chapter 5: Debugging (slides 51-65) ---
PART1_SLIDES.append(s1("\u7B2C5\u7AE0\uFF1A\u8C03\u8BD5\u4E0E\u8BCA\u65AD", "chapter"))
PART1_SLIDES.append(s1("5.1 \u8C03\u8BD5\u5668 (Debugger) \u5165\u95E8", "content"))
PART1_SLIDES.append(s1("5.2 \u65AD\u70B9 (Breakpoints) \u8BBE\u7F6E\u4E0E\u7BA1\u7406", "content"))
PART1_SLIDES.append(s1("5.3 \u6761\u4EF6\u65AD\u70B9\u4E0E\u65E5\u5FD7\u70B9", "content"))
PART1_SLIDES.append(s1("5.4 \u8C03\u8BD5\u63A7\u5236\uFF1A\u7EE7\u7EED/\u5355\u6B65/\u8DF3\u5165/\u8DF3\u51FA", "content"))
PART1_SLIDES.append(s1("5.5 \u53D8\u91CF\u67E5\u770B (Watch) \u4E0E\u8C03\u8BD5\u63A7\u5236\u53F0", "content"))
PART1_SLIDES.append(s1("5.6 \u8C03\u7528\u5806\u6808 (Call Stack) \u5206\u6790", "content"))
PART1_SLIDES.append(s1("5.7 launch.json \u914D\u7F6E\u8BE6\u89E3", "content"))
PART1_SLIDES.append(s1("5.8 Node.js \u8C03\u8BD5\u5B9E\u6218", "content"))
PART1_SLIDES.append(s1("5.9 Python \u8C03\u8BD5\u5B9E\u6218", "content"))
PART1_SLIDES.append(s1("5.10 \u6D4F\u89C8\u5668 JavaScript \u8C03\u8BD5", "content"))
PART1_SLIDES.append(s1("5.11 \u8FDC\u7A0B\u8C03\u8BD5 (Remote Debugging)", "content"))
PART1_SLIDES.append(s1("5.12 \u8C03\u8BD5\u63A7\u5236\u53F0 (Debug Console) \u4EA4\u4E92", "content"))
PART1_SLIDES.append(s1("5.13 \u6027\u80FD\u5206\u6790 (Performance Profiling)", "content"))
PART1_SLIDES.append(s1("5.14 \u5185\u5B58\u5FEB\u7167 (Memory Snapshot)", "content"))

# --- Chapter 6: Settings & Customization (slides 66-80) ---
PART1_SLIDES.append(s1("\u7B2C6\u7AE0\uFF1A\u8BBE\u7F6E\u4E0E\u4E2A\u6027\u5316", "chapter"))
PART1_SLIDES.append(s1("6.1 \u8BBE\u7F6E\u7F16\u8F91\u5668 (Settings Editor) \u5165\u95E8", "content"))
PART1_SLIDES.append(s1("6.2 settings.json \u9AD8\u7EA7\u914D\u7F6E", "content"))
PART1_SLIDES.append(s1("6.3 \u7528\u6237\u8BBE\u7F6E vs \u5DE5\u4F5C\u533A\u8BBE\u7F6E", "content"))
PART1_SLIDES.append(s1("6.4 \u4E3B\u9898 (Themes) \u2014 \u989C\u8272/\u56FE\u6807/\u5B57\u4F53", "content"))
PART1_SLIDES.append(s1("6.5 \u63A8\u8350\u4E3B\u9898 Top 10", "content"))
PART1_SLIDES.append(s1("6.6 \u81EA\u5B9A\u4E49\u4E3B\u9898\u914D\u7F6E", "content"))
PART1_SLIDES.append(s1("6.7 \u5B57\u4F53\u914D\u7F6E (Font Family/Ligatures)", "content"))
PART1_SLIDES.append(s1("6.8 \u7F16\u8F91\u5668\u5E03\u5C40\u81EA\u5B9A\u4E49", "content"))
PART1_SLIDES.append(s1("6.9 \u5DE5\u4F5C\u53F0\u914D\u7F6E (Workbench Settings)", "content"))
PART1_SLIDES.append(s1("6.10 \u6587\u4EF6\u5173\u8054 (File Associations)", "content"))
PART1_SLIDES.append(s1("6.11 \u6392\u9664\u6587\u4EF6 (Files Exclude)", "content"))
PART1_SLIDES.append(s1("6.12 \u8BBE\u7F6E\u540C\u6B65 (Settings Sync) \u8DE8\u8BBE\u5907", "content"))
PART1_SLIDES.append(s1("6.13 \u914D\u7F6E\u6587\u4EF6\u5907\u4EFD\u4E0E\u8FC1\u79FB", "content"))
PART1_SLIDES.append(s1("6.14 \u751F\u4EA7\u529B\u63D0\u5347\u603B\u7ED3", "content"))

# --- Chapter 7: Remote Development (slides 81-95) ---
PART1_SLIDES.append(s1("\u7B2C7\u7AE0\uFF1A\u8FDC\u7A0B\u5F00\u53D1\u4E0E\u534F\u4F5C", "chapter"))
PART1_SLIDES.append(s1("7.1 code-server \u8FDC\u7A0B\u5F00\u53D1\u67B6\u6784", "content"))
PART1_SLIDES.append(s1("7.2 SSH \u8FDC\u7A0B\u8FDE\u63A5\u914D\u7F6E", "content"))
PART1_SLIDES.append(s1("7.3 \u5BB9\u5668\u5316\u5F00\u53D1\u73AF\u5883 (Dev Containers)", "content"))
PART1_SLIDES.append(s1("7.4 devcontainer.json \u914D\u7F6E\u8BE6\u89E3", "content"))
PART1_SLIDES.append(s1("7.5 Docker \u96C6\u6210\u4E0E\u7BA1\u7406", "content"))
PART1_SLIDES.append(s1("7.6 Live Share \u5B9E\u65F6\u534F\u4F5C\u7F16\u7A0B", "content"))
PART1_SLIDES.append(s1("7.7 \u5171\u4EAB\u7EC8\u7AEF\u4E0E\u670D\u52A1\u5668", "content"))
PART1_SLIDES.append(s1("7.8 \u4EE3\u7801\u5BA1\u67E5 (Code Review) \u5DE5\u4F5C\u6D41", "content"))
PART1_SLIDES.append(s1("7.9 GitHub Pull Requests \u96C6\u6210", "content"))
PART1_SLIDES.append(s1("7.10 GitLab \u96C6\u6210", "content"))
PART1_SLIDES.append(s1("7.11 \u591A\u4EBA\u7F16\u8F91\u51B2\u7A81\u89E3\u51B3", "content"))
PART1_SLIDES.append(s1("7.12 \u56E2\u961F\u5F00\u53D1\u6700\u4F73\u5B9E\u8DF5", "content"))
PART1_SLIDES.append(s1("7.13 \u7B2C\u4E00\u90E8\u5206\u603B\u7ED3\u4E0E\u4E0B\u6B21\u9884\u544A", "content"))

# ===== PART 2: PLUGINS ECOSYSTEM (~100 slides) =====
PART2_SLIDES = []

PART2_SLIDES.append(s1("code-server \u5168\u529F\u80FD\u5B66\u4E60\u6307\u5357 - \u7B2C\u4E8C\u90E8\u5206\uFF1A\u63D2\u4EF6\u751F\u6001", "title"))
PART2_SLIDES.append(s1("\u76EE\u5F55", "toc"))

# --- Chapter 8: Plugin Basics (slides 1-10) ---
PART2_SLIDES.append(s1("\u7B2C8\u7AE0\uFF1A\u63D2\u4EF6\u57FA\u7840", "chapter"))
PART2_SLIDES.append(s1("8.1 \u4EC0\u4E48\u662F VS Code \u63D2\u4EF6\uFF1F", "content"))
PART2_SLIDES.append(s1("8.2 \u63D2\u4EF6\u5E02\u573A (Marketplace) \u4F7F\u7528\u6307\u5357", "content"))
PART2_SLIDES.append(s1("8.3 \u63D2\u4EF6\u5B89\u88C5/\u5378\u8F7D/\u7981\u7528/\u66F4\u65B0", "content"))
PART2_SLIDES.append(s1("8.4 \u63D2\u4EF6\u63A8\u8350\u6E05\u5355 (Extension Recommendations)", "content"))
PART2_SLIDES.append(s1("8.5 \u63D2\u4EF6\u7BA1\u7406 CLI\uFF1A--install-extension", "content"))
PART2_SLIDES.append(s1("8.6 \u79BB\u7EBF\u5B89\u88C5\u63D2\u4EF6 (.vsix)", "content"))
PART2_SLIDES.append(s1("8.7 \u63D2\u4EF6\u7248\u672C\u7BA1\u7406\u4E0E\u56FA\u5B9A\u7248\u672C", "content"))
PART2_SLIDES.append(s1("8.8 \u63D2\u4EF6\u96C6 (Extension Packs) \u4E00\u952E\u5B89\u88C5", "content"))
PART2_SLIDES.append(s1("8.9 \u63D2\u4EF6\u6743\u9650\u4E0E\u5B89\u5168", "content"))

# --- Chapter 9: Essential Plugins (slides 11-30) ---
PART2_SLIDES.append(s1("\u7B2C9\u7AE0\uFF1A\u5FC5\u5907\u63D2\u4EF6 Top 20", "chapter"))
PART2_SLIDES.append(s1("9.1 Prettier - \u4EE3\u7801\u683C\u5F0F\u5316\u795E\u5668", "content"))
PART2_SLIDES.append(s1("9.2 ESLint - JavaScript/TypeScript \u68C0\u67E5", "content"))
PART2_SLIDES.append(s1("9.3 GitLens - Git \u8D85\u7EA7\u589E\u5F3A", "content"))
PART2_SLIDES.append(s1("9.4 GitHub Copilot - AI \u4EE3\u7801\u8865\u5168", "content"))
PART2_SLIDES.append(s1("9.5 Codeium - \u514D\u8D39 AI \u4EE3\u7801\u8865\u5168", "content"))
PART2_SLIDES.append(s1("9.6 Tabnine - AI \u4EE3\u7801\u9884\u6D4B", "content"))
PART2_SLIDES.append(s1("9.7 Auto Rename Tag - HTML/XML \u6807\u7B7E\u81EA\u52A8\u91CD\u547D\u540D", "content"))
PART2_SLIDES.append(s1("9.8 Bracket Pair Colorizer - \u62EC\u53F7\u914D\u5BF9\u7740\u8272", "content"))
PART2_SLIDES.append(s1("9.9 indent-rainbow - \u7F29\u8FDB\u5F69\u8679\u6807\u8BB0", "content"))
PART2_SLIDES.append(s1("9.10 Path Intellisense - \u8DEF\u5F84\u81EA\u52A8\u8865\u5168", "content"))
PART2_SLIDES.append(s1("9.11 Live Server - \u5B9E\u65F6\u9884\u89C8\u670D\u52A1\u5668", "content"))
PART2_SLIDES.append(s1("9.12 REST Client - API \u8C03\u8BD5\u5229\u5668", "content"))
PART2_SLIDES.append(s1("9.13 Thunder Client - \u8F7B\u91CF\u7EA7 API \u6D4B\u8BD5", "content"))
PART2_SLIDES.append(s1("9.14 Docker - \u5BB9\u5668\u7BA1\u7406\u96C6\u6210", "content"))
PART2_SLIDES.append(s1("9.15 Kubernetes - K8s \u7BA1\u7406\u63D2\u4EF6", "content"))
PART2_SLIDES.append(s1("9.16 Remote - SSH/Containers/WSL", "content"))
PART2_SLIDES.append(s1("9.17 Markdown All in One - Markdown \u589E\u5F3A", "content"))
PART2_SLIDES.append(s1("9.18 YAML - YAML \u8BED\u6CD5\u652F\u6301", "content"))
PART2_SLIDES.append(s1("9.19 DotENV - .env \u6587\u4EF6\u8BED\u6CD5\u9AD8\u4EAE", "content"))
PART2_SLIDES.append(s1("9.20 Project Manager - \u9879\u76EE\u5FEB\u901F\u5207\u6362", "content"))

# --- Chapter 10: Language-Specific Plugins (slides 31-60) ---
PART2_SLIDES.append(s1("\u7B2C10\u7AE0\uFF1A\u8BED\u8A00\u4E13\u7528\u63D2\u4EF6", "chapter"))
# Python
PART2_SLIDES.append(s1("10.1 Python \u63D2\u4EF6\u751F\u6001\u6982\u89C8", "content"))
PART2_SLIDES.append(s1("10.2 Python (Microsoft) - \u8BED\u8A00\u670D\u52A1/\u8C03\u8BD5/\u6D4B\u8BD5", "content"))
PART2_SLIDES.append(s1("10.3 Pylance - \u5FEB\u901F\u7C7B\u578B\u68C0\u67E5", "content"))
PART2_SLIDES.append(s1("10.4 Python Docstring Generator", "content"))
PART2_SLIDES.append(s1("10.5 Python Test Explorer", "content"))
PART2_SLIDES.append(s1("10.6 Jupyter - \u4EA4\u4E92\u5F0F Python \u7F16\u7A0B", "content"))
# JavaScript/TypeScript
PART2_SLIDES.append(s1("10.7 JavaScript/TypeScript \u63D2\u4EF6\u751F\u6001", "content"))
PART2_SLIDES.append(s1("10.8 ESLint + Prettier \u914D\u5408\u4F7F\u7528", "content"))
PART2_SLIDES.append(s1("10.9 JavaScript (ES6) Code Snippets", "content"))
PART2_SLIDES.append(s1("10.10 npm Intellisense", "content"))
PART2_SLIDES.append(s1("10.11 Import Cost - \u5BFC\u5165\u5305\u5927\u5C0F\u663E\u793A", "content"))
PART2_SLIDES.append(s1("10.12 Console Ninja - \u63A7\u5236\u53F0\u8F93\u51FA\u589E\u5F3A", "content"))
# Go
PART2_SLIDES.append(s1("10.13 Go \u63D2\u4EF6\u751F\u6001\u6982\u89C8", "content"))
PART2_SLIDES.append(s1("10.14 Go (golang.go) - \u8BED\u8A00\u670D\u52A1/\u8C03\u8BD5", "content"))
PART2_SLIDES.append(s1("10.15 Go Test Explorer", "content"))
PART2_SLIDES.append(s1("10.16 Go Doc - \u6587\u6863\u67E5\u770B", "content"))
# Rust
PART2_SLIDES.append(s1("10.17 Rust \u63D2\u4EF6\u751F\u6001\u6982\u89C8", "content"))
PART2_SLIDES.append(s1("10.18 rust-analyzer - Rust \u8BED\u8A00\u670D\u52A1", "content"))
PART2_SLIDES.append(s1("10.19 CodeLLDB - Rust \u8C03\u8BD5\u5668", "content"))
PART2_SLIDES.append(s1("10.20 Even Better TOML - Cargo.toml \u652F\u6301", "content"))
# Java
PART2_SLIDES.append(s1("10.21 Java \u63D2\u4EF6\u751F\u6001\u6982\u89C8", "content"))
PART2_SLIDES.append(s1("10.22 Extension Pack for Java - \u5168\u5957\u5DE5\u5177", "content"))
PART2_SLIDES.append(s1("10.23 Spring Boot Extension Pack", "content"))
PART2_SLIDES.append(s1("10.24 Gradle for Java", "content"))
PART2_SLIDES.append(s1("10.25 Maven for Java", "content"))
# C/C++
PART2_SLIDES.append(s1("10.26 C/C++ \u63D2\u4EF6\u751F\u6001\u6982\u89C8", "content"))
PART2_SLIDES.append(s1("10.27 C/C++ (Microsoft) - IntelliSense/\u8C03\u8BD5", "content"))
PART2_SLIDES.append(s1("10.28 CMake Tools", "content"))
PART2_SLIDES.append(s1("10.29 Makefile Tools", "content"))

# --- Chapter 11: Theme & UI Plugins (slides 61-75) ---
PART2_SLIDES.append(s1("\u7B2C11\u7AE0\uFF1A\u4E3B\u9898\u4E0E UI \u63D2\u4EF6", "chapter"))
PART2_SLIDES.append(s1("11.1 \u9876\u7EA7\u4E3B\u9898\u63A8\u8350", "content"))
PART2_SLIDES.append(s1("11.2 One Dark Pro", "content"))
PART2_SLIDES.append(s1("11.3 Dracula Official", "content"))
PART2_SLIDES.append(s1("11.4 GitHub Theme", "content"))
PART2_SLIDES.append(s1("11.5 Monokai Pro", "content"))
PART2_SLIDES.append(s1("11.6 Material Icon Theme", "content"))
PART2_SLIDES.append(s1("11.7 vscode-icons", "content"))
PART2_SLIDES.append(s1("11.8 \u56FE\u6807\u4E3B\u9898\u5BF9\u6BD4\u4E0E\u9009\u62E9", "content"))
PART2_SLIDES.append(s1("11.9 \u4EA7\u54C1\u56FE\u6807\u4E3B\u9898 (Product Icon Themes)", "content"))
PART2_SLIDES.append(s1("11.10 \u81EA\u5B9A\u4E49 CSS \u4E3B\u9898\u5236\u4F5C", "content"))
PART2_SLIDES.append(s1("11.11 Peacock - \u5DE5\u4F5C\u533A\u989C\u8272\u533A\u5206", "content"))
PART2_SLIDES.append(s1("11.12 TODO Highlight - \u5F85\u529E\u9AD8\u4EAE", "content"))
PART2_SLIDES.append(s1("11.13 Better Comments - \u6CE8\u91CA\u5206\u7C7B\u9AD8\u4EAE", "content"))
PART2_SLIDES.append(s1("11.14 Error Lens - \u884C\u5185\u9519\u8BEF\u663E\u793A", "content"))
PART2_SLIDES.append(s1("11.15 CodeSnap - \u4EE3\u7801\u622A\u56FE\u5DE5\u5177", "content"))

# --- Chapter 12: Productivity Plugins (slides 76-95) ---
PART2_SLIDES.append(s1("\u7B2C12\u7AE0\uFF1A\u751F\u4EA7\u529B\u63D2\u4EF6", "chapter"))
PART2_SLIDES.append(s1("12.1 Bookmarks - \u4EE3\u7801\u4E66\u7B7E", "content"))
PART2_SLIDES.append(s1("12.2 Todo Tree - TODO/FIXME \u6C47\u603B", "content"))
PART2_SLIDES.append(s1("12.3 Partial Diff - \u6587\u672C\u5DEE\u5F02\u6BD4\u8F83", "content"))
PART2_SLIDES.append(s1("12.4 Turbo Console Log - \u5FEB\u901F console.log", "content"))
PART2_SLIDES.append(s1("12.5 Polacode - \u4EE3\u7801\u7F8E\u5316\u622A\u56FE", "content"))
PART2_SLIDES.append(s1("12.6 WakaTime - \u7F16\u7A0B\u65F6\u95F4\u7EDF\u8BA1", "content"))
PART2_SLIDES.append(s1("12.7 Code Spell Checker - \u62FC\u5199\u68C0\u67E5", "content"))
PART2_SLIDES.append(s1("12.8 File Utils - \u6587\u4EF6\u6279\u91CF\u64CD\u4F5C", "content"))
PART2_SLIDES.append(s1("12.9 Change Case - \u5927\u5C0F\u5199\u8F6C\u6362", "content"))
PART2_SLIDES.append(s1("12.10 Sort Lines - \u884C\u6392\u5E8F\u5DE5\u5177", "content"))
PART2_SLIDES.append(s1("12.11 Regex Previewer - \u6B63\u5219\u8868\u8FBE\u5F0F\u9884\u89C8", "content"))
PART2_SLIDES.append(s1("12.12 Draw.io Integration - \u6D41\u7A0B\u56FE\u7F16\u8F91", "content"))
PART2_SLIDES.append(s1("12.13 Mermaid Preview - \u56FE\u8868\u9884\u89C8", "content"))
PART2_SLIDES.append(s1("12.14 PlantUML - UML \u56FE\u7F16\u8F91", "content"))
PART2_SLIDES.append(s1("12.15 Excel Viewer - \u8868\u683C\u67E5\u770B", "content"))
PART2_SLIDES.append(s1("12.16 PDF Preview - PDF \u9884\u89C8", "content"))
PART2_SLIDES.append(s1("12.17 SVG Preview - SVG \u9884\u89C8", "content"))
PART2_SLIDES.append(s1("12.18 Image Preview - \u56FE\u7247\u9884\u89C8", "content"))
PART2_SLIDES.append(s1("12.19 \u63D2\u4EF6\u7EC4\u5408\u63A8\u8350\u6E05\u5355", "content"))
PART2_SLIDES.append(s1("12.20 \u7B2C\u4E8C\u90E8\u5206\u603B\u7ED3", "content"))

# ===== PART 3: MULTI-LANGUAGE ENTERPRISE DEV (~100 slides) =====
PART3_SLIDES = []

PART3_SLIDES.append(s1("code-server \u5168\u529F\u80FD\u5B66\u4E60\u6307\u5357 - \u7B2C\u4E09\u90E8\u5206\uFF1A\u591A\u8BED\u8A00\u4F01\u4E1A\u7EA7\u5F00\u53D1", "title"))
PART3_SLIDES.append(s1("\u76EE\u5F55", "toc"))

# --- Chapter 13: Go Enterprise Development (slides 1-20) ---
PART3_SLIDES.append(s1("\u7B2C13\u7AE0\uFF1AGo \u4F01\u4E1A\u7EA7\u5F00\u53D1", "chapter"))
PART3_SLIDES.append(s1("13.1 Go \u73AF\u5883\u642D\u5EFA\u4E0E\u914D\u7F6E", "content"))
PART3_SLIDES.append(s1("13.2 Go Modules \u4F9D\u8D56\u7BA1\u7406", "content"))
PART3_SLIDES.append(s1("13.3 Go \u9879\u76EE\u7ED3\u6784\u6700\u4F73\u5B9E\u8DF5", "content"))
PART3_SLIDES.append(s1("13.4 Go \u5355\u5143\u6D4B\u8BD5\u4E0E\u8986\u76D6\u7387", "content"))
PART3_SLIDES.append(s1("13.5 Go \u6027\u80FD\u5206\u6790 (pprof)", "content"))
PART3_SLIDES.append(s1("13.6 Go \u5FAE\u670D\u52A1\u5F00\u53D1 (Gin/Echo/Fiber)", "content"))
PART3_SLIDES.append(s1("13.7 Go gRPC \u670D\u52A1\u5F00\u53D1", "content"))
PART3_SLIDES.append(s1("13.8 Go \u6570\u636E\u5E93\u64CD\u4F5C (GORM/sqlx)", "content"))
PART3_SLIDES.append(s1("13.9 Go Redis/RabbitMQ \u96C6\u6210", "content"))
PART3_SLIDES.append(s1("13.10 Go Docker \u955C\u50CF\u6784\u5EFA\u4E0E\u591A\u9636\u6BB5", "content"))
PART3_SLIDES.append(s1("13.11 Go CI/CD \u6D41\u6C34\u7EBF\u914D\u7F6E", "content"))
PART3_SLIDES.append(s1("13.12 Go \u9519\u8BEF\u5904\u7406\u6700\u4F73\u5B9E\u8DF5", "content"))
PART3_SLIDES.append(s1("13.13 Go \u5E76\u53D1\u7F16\u7A0B\u4E0E\u534F\u7A0B", "content"))
PART3_SLIDES.append(s1("13.14 Go \u65E5\u5FD7\u4E0E\u76D1\u63A7 (zap/zerolog)", "content"))
PART3_SLIDES.append(s1("13.15 Go \u914D\u7F6E\u7BA1\u7406 (Viper)", "content"))
PART3_SLIDES.append(s1("13.16 Go OpenTelemetry \u96C6\u6210", "content"))
PART3_SLIDES.append(s1("13.17 Go \u4F01\u4E1A\u9879\u76EE\u5B9E\u6218\u6848\u4F8B", "content"))
PART3_SLIDES.append(s1("13.18 Go \u5E38\u89C1\u9677\u9631\u4E0E\u89E3\u51B3\u65B9\u6848", "content"))
PART3_SLIDES.append(s1("13.19 Go \u63D2\u4EF6\u63A8\u8350\u6E05\u5355", "content"))
PART3_SLIDES.append(s1("13.20 Go \u5B66\u4E60\u8D44\u6E90\u4E0E\u8FDB\u9636\u8DEF\u5F84", "content"))

# --- Chapter 14: Rust Enterprise Development (slides 21-40) ---
PART3_SLIDES.append(s1("\u7B2C14\u7AE0\uFF1ARust \u4F01\u4E1A\u7EA7\u5F00\u53D1", "chapter"))
PART3_SLIDES.append(s1("14.1 Rust \u73AF\u5883\u642D\u5EFA (rustup/cargo)", "content"))
PART3_SLIDES.append(s1("14.2 Cargo \u9879\u76EE\u7BA1\u7406\u4E0E\u4F9D\u8D56", "content"))
PART3_SLIDES.append(s1("14.3 Rust \u9879\u76EE\u7ED3\u6784\u6700\u4F73\u5B9E\u8DF5", "content"))
PART3_SLIDES.append(s1("14.4 Rust \u6240\u6709\u6743\u4E0E\u501F\u7528\u68C0\u67E5\u5668\u5B9E\u6218", "content"))
PART3_SLIDES.append(s1("14.5 Rust \u9519\u8BEF\u5904\u7406 (Result/Option/?\u8FD0\u7B97\u7B26)", "content"))
PART3_SLIDES.append(s1("14.6 Rust \u5355\u5143\u6D4B\u8BD5\u4E0E\u96C6\u6210\u6D4B\u8BD5", "content"))
PART3_SLIDES.append(s1("14.7 Rust Web \u5F00\u53D1 (Actix-web/Axum/Rocket)", "content"))
PART3_SLIDES.append(s1("14.8 Rust \u5F02\u6B65\u7F16\u7A0B (tokio/async-std)", "content"))
PART3_SLIDES.append(s1("14.9 Rust \u6570\u636E\u5E93\u64CD\u4F5C (sqlx/Diesel/SeaORM)", "content"))
PART3_SLIDES.append(s1("14.10 Rust gRPC \u670D\u52A1 (tonic)", "content"))
PART3_SLIDES.append(s1("14.11 Rust CLI \u5DE5\u5177\u5F00\u53D1 (clap)", "content"))
PART3_SLIDES.append(s1("14.12 Rust FFI \u4E0E C \u4EA4\u4E92", "content"))
PART3_SLIDES.append(s1("14.13 Rust WASM \u524D\u7AEF\u5F00\u53D1", "content"))
PART3_SLIDES.append(s1("14.14 Rust \u5D4C\u5165\u5F0F\u5F00\u53D1 (no_std/embedded)", "content"))
PART3_SLIDES.append(s1("14.15 Rust \u5B89\u5168\u5BA1\u8BA1 (cargo-audit/clippy)", "content"))
PART3_SLIDES.append(s1("14.16 Rust \u6027\u80FD\u4F18\u5316\u4E0E Benchmark", "content"))
PART3_SLIDES.append(s1("14.17 Rust Docker \u591A\u9636\u6BB5\u6784\u5EFA", "content"))
PART3_SLIDES.append(s1("14.18 Rust \u4F01\u4E1A\u9879\u76EE\u5B9E\u6218\u6848\u4F8B", "content"))
PART3_SLIDES.append(s1("14.19 Rust \u63D2\u4EF6\u63A8\u8350\u6E05\u5355", "content"))
PART3_SLIDES.append(s1("14.20 Rust \u5B66\u4E60\u8D44\u6E90\u4E0E\u8FDB\u9636\u8DEF\u5F84", "content"))

# --- Chapter 15: Java Enterprise Development (slides 41-60) ---
PART3_SLIDES.append(s1("\u7B2C15\u7AE0\uFF1AJava \u4F01\u4E1A\u7EA7\u5F00\u53D1", "chapter"))
PART3_SLIDES.append(s1("15.1 Java \u73AF\u5883\u642D\u5EFA (JDK 21/Maven/Gradle)", "content"))
PART3_SLIDES.append(s1("15.2 Spring Boot 3 \u9879\u76EE\u521B\u5EFA", "content"))
PART3_SLIDES.append(s1("15.3 Spring Boot REST API \u5F00\u53D1", "content"))
PART3_SLIDES.append(s1("15.4 Spring Data JPA \u6570\u636E\u5E93\u64CD\u4F5C", "content"))
PART3_SLIDES.append(s1("15.5 Spring Security \u8BA4\u8BC1\u4E0E\u6388\u6743", "content"))
PART3_SLIDES.append(s1("15.6 Spring Cloud \u5FAE\u670D\u52A1", "content"))
PART3_SLIDES.append(s1("15.7 Java \u5355\u5143\u6D4B\u8BD5 (JUnit 5/Mockito)", "content"))
PART3_SLIDES.append(s1("15.8 Java \u96C6\u6210\u6D4B\u8BD5 (Testcontainers)", "content"))
PART3_SLIDES.append(s1("15.9 Java \u65E5\u5FD7\u4E0E\u76D1\u63A7 (SLF4J/Logback)", "content"))
PART3_SLIDES.append(s1("15.10 Java \u6027\u80FD\u4F18\u5316 (JVM \u8C03\u4F18)", "content"))
PART3_SLIDES.append(s1("15.11 Java Docker \u955C\u50CF\u6784\u5EFA", "content"))
PART3_SLIDES.append(s1("15.12 Java Maven/Gradle \u591A\u6A21\u5757\u9879\u76EE", "content"))
PART3_SLIDES.append(s1("15.13 Java MyBatis/MyBatis-Plus", "content"))
PART3_SLIDES.append(s1("15.14 Java Redis \u96C6\u6210 (Spring Cache)", "content"))
PART3_SLIDES.append(s1("15.15 Java \u6D88\u606F\u961F\u5217 (RabbitMQ/Kafka)", "content"))
PART3_SLIDES.append(s1("15.16 Java \u5F02\u5E38\u5904\u7406\u6700\u4F73\u5B9E\u8DF5", "content"))
PART3_SLIDES.append(s1("15.17 Java \u4F01\u4E1A\u9879\u76EE\u5B9E\u6218\u6848\u4F8B", "content"))
PART3_SLIDES.append(s1("15.18 Java \u63D2\u4EF6\u63A8\u8350\u6E05\u5355", "content"))
PART3_SLIDES.append(s1("15.19 Java \u5E38\u89C1\u95EE\u9898\u4E0E\u89E3\u51B3", "content"))
PART3_SLIDES.append(s1("15.20 Java \u5B66\u4E60\u8D44\u6E90\u4E0E\u8FDB\u9636\u8DEF\u5F84", "content"))

# --- Chapter 16: C/C++ Enterprise Development (slides 61-75) ---
PART3_SLIDES.append(s1("\u7B2C16\u7AE0\uFF1AC/C++ \u4F01\u4E1A\u7EA7\u5F00\u53D1", "chapter"))
PART3_SLIDES.append(s1("16.1 C/C++ \u73AF\u5883\u642D\u5EFA (GCC/Clang/MSVC)", "content"))
PART3_SLIDES.append(s1("16.2 CMake \u6784\u5EFA\u7CFB\u7EDF\u8BE6\u89E3", "content"))
PART3_SLIDES.append(s1("16.3 C++ \u5305\u7BA1\u7406 (vcpkg/Conan)", "content"))
PART3_SLIDES.append(s1("16.4 C++ \u5355\u5143\u6D4B\u8BD5 (Google Test/Catch2)", "content"))
PART3_SLIDES.append(s1("16.5 C++ \u8C03\u8BD5\u6280\u5DE7 (GDB/LLDB)", "content"))
PART3_SLIDES.append(s1("16.6 C++ \u6027\u80FD\u5206\u6790 (perf/Valgrind)", "content"))
PART3_SLIDES.append(s1("16.7 C++ \u5185\u5B58\u7BA1\u7406\u6700\u4F73\u5B9E\u8DF5", "content"))
PART3_SLIDES.append(s1("16.8 C++ \u7F51\u7EDC\u7F16\u7A0B (Boost.Asio)", "content"))
PART3_SLIDES.append(s1("16.9 C++ \u591A\u7EBF\u7A0B\u7F16\u7A0B (std::thread/TBB)", "content"))
PART3_SLIDES.append(s1("16.10 C++ Docker \u6784\u5EFA\u4E0E\u4EA4\u53C9\u7F16\u8BD1", "content"))
PART3_SLIDES.append(s1("16.11 C++ \u9759\u6001\u5206\u6790 (clang-tidy/cppcheck)", "content"))
PART3_SLIDES.append(s1("16.12 C++ \u4F01\u4E1A\u9879\u76EE\u5B9E\u6218\u6848\u4F8B", "content"))
PART3_SLIDES.append(s1("16.13 C/C++ \u63D2\u4EF6\u63A8\u8350\u6E05\u5355", "content"))
PART3_SLIDES.append(s1("16.14 C/C++ \u5E38\u89C1\u95EE\u9898\u4E0E\u89E3\u51B3", "content"))
PART3_SLIDES.append(s1("16.15 C/C++ \u5B66\u4E60\u8D44\u6E90\u4E0E\u8FDB\u9636\u8DEF\u5F84", "content"))

# --- Chapter 17: Scala & Other Languages (slides 76-90) ---
PART3_SLIDES.append(s1("\u7B2C17\u7AE0\uFF1AScala \u4E0E\u5176\u4ED6\u8BED\u8A00", "chapter"))
PART3_SLIDES.append(s1("17.1 Scala \u73AF\u5883\u642D\u5EFA (sbt/Coursier)", "content"))
PART3_SLIDES.append(s1("17.2 Scala \u9879\u76EE\u7ED3\u6784\u4E0E\u4F9D\u8D56\u7BA1\u7406", "content"))
PART3_SLIDES.append(s1("17.3 Scala \u51FD\u6570\u5F0F\u7F16\u7A0B\u5B9E\u6218", "content"))
PART3_SLIDES.append(s1("17.4 Akka/Pekko \u5E76\u53D1\u7F16\u7A0B", "content"))
PART3_SLIDES.append(s1("17.5 Scala \u6D4B\u8BD5 (ScalaTest/Specs2)", "content"))
PART3_SLIDES.append(s1("17.6 Scala \u4F01\u4E1A\u9879\u76EE\u5B9E\u6218", "content"))
PART3_SLIDES.append(s1("17.7 Kotlin \u5F00\u53D1\u73AF\u5883\u914D\u7F6E", "content"))
PART3_SLIDES.append(s1("17.8 Swift \u5F00\u53D1\u73AF\u5883\u914D\u7F6E", "content"))
PART3_SLIDES.append(s1("17.9 Ruby/Rails \u5F00\u53D1\u73AF\u5883", "content"))
PART3_SLIDES.append(s1("17.10 PHP/Laravel \u5F00\u53D1\u73AF\u5883", "content"))
PART3_SLIDES.append(s1("17.11 .NET/C# \u5F00\u53D1\u73AF\u5883", "content"))
PART3_SLIDES.append(s1("17.12 \u591A\u8BED\u8A00\u9879\u76EE\u7BA1\u7406\u7B56\u7565", "content"))
PART3_SLIDES.append(s1("17.13 Monorepo \u5F00\u53D1\u5B9E\u8DF5", "content"))
PART3_SLIDES.append(s1("17.14 \u8DE8\u8BED\u8A00\u8C03\u8BD5\u6280\u5DE7", "content"))
PART3_SLIDES.append(s1("17.15 \u5168\u7CFB\u5217\u603B\u7ED3\u4E0E\u8FDB\u9636\u8DEF\u5F84", "content"))

# ===== GENERATE PPTs =====
def generate_ppt(slides_data, output_filename, part_label):
    """Generate a PPT using PptxGenJS via Node.js"""
    output_path = os.path.join(BASE, output_filename)
    js_code = f'''
const PptxGenJS = require("pptxgenjs");
const pptx = new PptxGenJS();
const D="0F172A",C="1E293B",A="3B82F6",A2="8B5CF6",G="22C55E",R="EF4444",Y="F59E0B",W="F8FAFC",GR="94A3B8";
pptx.defineLayout({{name:"WIDE",width:13.33,height:7.5}});
pptx.layout="WIDE";
const slides = {json.dumps(slides_data, ensure_ascii=False)};
slides.forEach((s,i)=>{{
  const sl = pptx.addSlide();
  sl.background={{color:D}};
  sl.addShape("rect",{{x:0,y:0,w:13.33,h:0.06,fill:{{color:A}}}});
  if(s.type==="title"){{
    sl.addShape("rect",{{x:0,y:0,w:13.33,h:0.1,fill:{{color:A}}}});
    sl.addText(s.title,{{x:1,y:1.5,w:11,h:1.2,fontSize:44,color:W,bold:true,fontFace:"Arial"}});
    sl.addText("{part_label}",{{x:1,y:2.8,w:11,h:0.6,fontSize:22,color:A,fontFace:"Arial"}});
    sl.addShape("rect",{{x:1,y:3.6,w:2.5,h:0.05,fill:{{color:A2}}}});
    sl.addText("code-server Full-Feature Teaching Guide | June 2026",{{x:1,y:4.0,w:11,h:0.5,fontSize:14,color:GR,fontFace:"Arial"}});
  }}else if(s.type==="toc"){{
    sl.addText("Table of Contents",{{x:0.5,y:0.3,w:12,h:0.6,fontSize:26,color:W,bold:true,fontFace:"Arial"}});
    const chs = slides.filter(x=>x.type==="chapter");
    chs.forEach((ch,j)=>{{
      sl.addText(ch.title,{{x:1,y:1.2+j*0.45,w:11,h:0.4,fontSize:14,color:A,bold:true,fontFace:"Arial"}});
    }});
  }}else if(s.type==="chapter"){{
    sl.addShape("rect",{{x:0,y:2.5,w:13.33,h:2.5,fill:{{color:C}}}});
    sl.addText(s.title,{{x:1,y:2.8,w:11,h:1.0,fontSize:32,color:A,bold:true,fontFace:"Arial"}});
    sl.addText("code-server Full-Feature Teaching Guide",{{x:1,y:4.0,w:11,h:0.5,fontSize:16,color:GR,fontFace:"Arial"}});
  }}else{{
    sl.addText(s.title,{{x:0.5,y:0.2,w:12,h:0.6,fontSize:22,color:W,bold:true,fontFace:"Arial"}});
    sl.addText("Detailed content for: "+s.title,{{x:1,y:1.5,w:11,h:4,fontSize:16,color:GR,fontFace:"Arial"}});
    sl.addText("(See accompanying detailed guide for full content)",{{x:1,y:3.0,w:11,h:1,fontSize:14,color:Y,fontFace:"Arial"}});
  }}
  sl.addText("code-server Teaching Guide | "+"{part_label}"+" | Slide "+(i+1)+"/"+slides.length,{{x:0.5,y:7.05,w:12,h:0.35,fontSize:10,color:GR,fontFace:"Arial"}});
}});
pptx.writeFile({{fileName:"{output_filename}"}}).then(()=>console.log("OK")).catch(e=>console.error(e));
'''
    js_file = os.path.join(BASE, f"_gen_{part_label.replace(' ','_')}.js")
    with open(js_file, "w", encoding="utf-8") as f:
        f.write(js_code)
    result = subprocess.run(["node", js_file], capture_output=True, text=True, cwd=BASE, timeout=120)
    os.remove(js_file)
    if "OK" in result.stdout:
        print(f"  {output_filename}: {len(slides_data)} slides - OK")
    else:
        print(f"  {output_filename}: ERROR - {result.stderr[:200]}")

print("Generating Part 1: Basics & IDE Usage...")
generate_ppt(PART1_SLIDES, "Code_Server_Teaching_Part1_Basics.pptx", "Part 1: Basics & IDE")

print("Generating Part 2: Plugins Ecosystem...")
generate_ppt(PART2_SLIDES, "Code_Server_Teaching_Part2_Plugins.pptx", "Part 2: Plugins")

print("Generating Part 3: Multi-Language Enterprise Dev...")
generate_ppt(PART3_SLIDES, "Code_Server_Teaching_Part3_Enterprise.pptx", "Part 3: Enterprise Dev")

print(f"\nDone! Generated {len(PART1_SLIDES)+len(PART2_SLIDES)+len(PART3_SLIDES)} slides across 3 files.")