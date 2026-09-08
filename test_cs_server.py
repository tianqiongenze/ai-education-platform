from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--ignore-certificate-errors"])
    context = browser.new_context(ignore_https_errors=True, viewport={"width": 1280, "height": 800})
    page = context.new_page()

    print("=== Code-Server Full Test (from server with hosts) ===")
    page.goto("https://code-server.ai-platform.local:31825/", timeout=30000, wait_until="networkidle")
    time.sleep(5)
    print(f"1. Title: {page.title()}")
    print(f"   URL: {page.url}")

    pwd = page.query_selector("input[type=password]")
    print(f"2. Password: {'found' if pwd else 'not found'}")

    if pwd:
        pwd.fill("Dify@2026")
        time.sleep(1)
        btn = page.query_selector("input[type=submit]")
        if btn:
            btn.click()
        time.sleep(15)
        print(f"3. Login: {page.title()}")
        page.screenshot(path="/tmp/cs_login.png")

        ws_err = page.query_selector("text=WebSocket close") or page.query_selector("text=An unexpected error")
        print(f"4. WS error: {'YES' if ws_err else 'NO'}")

        editor = page.query_selector(".monaco-editor")
        print(f"5. Editor: {'LOADED' if editor else 'NOT LOADED'}")

        if editor and not ws_err:
            print("6. Creating Python IIoT project...")
            page.keyboard.press("Control+Shift+P")
            time.sleep(1)
            page.keyboard.type("New File")
            time.sleep(1)
            page.keyboard.press("Enter")
            time.sleep(1)
            page.keyboard.type("iiot.py")
            page.keyboard.press("Enter")
            time.sleep(2)

            lines = [
                "class Sensor:",
                "    def __init__(self, name, val, unit):",
                "        self.name = name; self.val = val; self.unit = unit",
                "    def check(self, lo, hi):",
                '        return "OK" if lo <= self.val <= hi else "ALERT"',
                'sensors = [Sensor("Temp", 75.5, "C"), Sensor("Press", 2.1, "MPa")]',
                "for s in sensors:",
                '    print(f"{s.name}: {s.val}{s.unit} [{s.check(0,100)}]")',
            ]
            for line in lines:
                page.keyboard.type(line)
                page.keyboard.press("Enter")
                time.sleep(0.05)
            page.keyboard.press("Control+S")
            time.sleep(1)
            page.screenshot(path="/tmp/cs_code.png")
            print("   Code written")

            print("7. Opening terminal...")
            page.keyboard.press("Control+Shift+P")
            time.sleep(1)
            page.keyboard.type("Toggle Terminal")
            time.sleep(1)
            page.keyboard.press("Enter")
            time.sleep(3)

            print("8. Running code...")
            page.keyboard.type("python3 iiot.py")
            page.keyboard.press("Enter")
            time.sleep(5)
            page.screenshot(path="/tmp/cs_run.png")

            body = page.inner_text("body")
            ok = "Temp" in body and "OK" in body
            print(f"9. Execution: {'PASS' if ok else 'CHECK'}")

            print("10. AI test...")
            page.keyboard.press("Escape")
            time.sleep(1)
            page.keyboard.press("Control+Shift+P")
            time.sleep(1)
            page.keyboard.type("Continue")
            time.sleep(2)
            btext = page.inner_text("body")
            print(f"   Continue.dev: {'YES' if 'Continue' in btext else 'NO'}")
            page.screenshot(path="/tmp/cs_ai.png")

        print("11. DONE")
    else:
        print("2. No password field found")

    browser.close()
