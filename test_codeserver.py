from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--ignore-certificate-errors"])
    context = browser.new_context(ignore_https_errors=True, viewport={"width": 1280, "height": 800})
    page = context.new_page()

    print("=== Code-Server Full Functional Test ===")

    # Login
    page.goto("https://10.167.2.175:31825/cs/", timeout=30000, wait_until="networkidle")
    time.sleep(5)
    page.fill("input[type=password]", "Dify@2026")
    time.sleep(1)
    btn = page.query_selector("input[type=submit]")
    if btn:
        btn.click()
    time.sleep(15)
    print(f"1. Login: {page.title()}")
    page.screenshot(path="D:/dify-install/screenshot_cs_full_1.png")

    # Trust folder - use keyboard to dismiss trust dialog
    # Press Tab then Enter to trust
    page.keyboard.press("Tab")
    time.sleep(0.5)
    page.keyboard.press("Enter")
    time.sleep(2)
    # If trust dialog still there, try clicking "Trust" button via JS
    page.evaluate("""() => {
        const btns = document.querySelectorAll('button');
        for (const b of btns) {
            if (b.textContent.includes('Trust')) b.click();
        }
    }""")
    time.sleep(3)
    print("2. Trust folder done")
    page.screenshot(path="D:/dify-install/screenshot_cs_full_2.png")

    # Check WS - no error expected
    ws_err = page.query_selector("text=WebSocket close")
    err_dialog = page.query_selector("text=An unexpected error")
    print(f"3. WebSocket error: {'Yes' if ws_err or err_dialog else 'No'}")

    # Check editor
    editor = page.query_selector(".monaco-editor")
    print(f"4. Editor loaded: {'Yes' if editor else 'No'}")

    # Check file explorer
    explorer = page.query_selector(".explorer")
    print(f"5. File explorer: {'Yes' if explorer else 'No'}")

    # Check terminal via command palette
    page.keyboard.press("Control+Shift+P")
    time.sleep(1)
    page.keyboard.type("Toggle Terminal")
    time.sleep(1)
    page.keyboard.press("Enter")
    time.sleep(3)
    terminal = page.query_selector(".terminal") or page.query_selector(".xterm") or page.query_selector("[class*=terminal]")
    print(f"6. Terminal: {'Yes' if terminal else 'No'}")
    page.screenshot(path="D:/dify-install/screenshot_cs_full_3.png")

    # Create Python file via command palette
    page.keyboard.press("Control+Shift+P")
    time.sleep(1)
    page.keyboard.type("New File")
    time.sleep(1)
    page.keyboard.press("Enter")
    time.sleep(1)
    page.keyboard.type("hello.py")
    page.keyboard.press("Enter")
    time.sleep(2)
    page.keyboard.type("print('Hello from Code-Server!')")
    time.sleep(1)
    page.keyboard.press("Control+S")
    time.sleep(1)
    page.screenshot(path="D:/dify-install/screenshot_cs_full_4.png")
    print("7. Created hello.py")

    # Run in terminal
    if terminal:
        page.keyboard.type("python3 hello.py")
        page.keyboard.press("Enter")
        time.sleep(5)
        page.screenshot(path="D:/dify-install/screenshot_cs_full_5.png")
        term_text = page.inner_text("body")
        has_output = "Hello from Code-Server" in term_text
        print(f"8. Python execution: {'PASS' if has_output else 'FAIL'}")
    else:
        print("8. Python execution: SKIP (no terminal)")

    # Check AI (Continue.dev)
    page.keyboard.press("Control+Shift+P")
    time.sleep(1)
    page.keyboard.type("Continue")
    time.sleep(2)
    page.screenshot(path="D:/dify-install/screenshot_cs_full_6.png")
    body_text = page.inner_text("body")
    has_continue = "Continue" in body_text
    has_explain = "Explain" in body_text or "explain" in body_text
    has_refactor = "Refactor" in body_text or "refactor" in body_text
    print(f"9. Continue.dev AI: {'Yes' if has_continue else 'No'}")
    print(f"   Explain: {'Yes' if has_explain else 'No'}")
    print(f"   Refactor: {'Yes' if has_refactor else 'No'}")

    # Check extensions
    page.keyboard.press("Escape")
    time.sleep(1)
    page.keyboard.press("Control+Shift+X")
    time.sleep(3)
    page.screenshot(path="D:/dify-install/screenshot_cs_full_7.png")
    ext_text = page.inner_text("body")
    for lang in ["Python", "Java", "Go", "Rust", "C++"]:
        print(f"10. {lang} extension: {'Yes' if lang in ext_text else 'No'}")

    browser.close()
    print("=== Test Complete ===")
