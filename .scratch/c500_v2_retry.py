"""Retry failed slots from concurrent_500_v2_report.json: re-run base.worker on each wid,
WAVE-at-a-time, sessions NOT held (verify pass/fail only)."""
import os, sys, json, time, threading
os.environ.setdefault("STUDENT_PASS", "AutoTest2026!")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import concurrent_500_v2 as base

failed = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "failed_wids.txt")))
TOTAL = len(failed)
results = {}
hold = []
nwaves = (TOTAL + base.WAVE - 1) // base.WAVE
for wi in range(nwaves):
    batch = failed[wi * base.WAVE:(wi + 1) * base.WAVE]
    ths = []
    for wid in batch:
        t = threading.Thread(target=base.worker, args=(wid, results, hold))
        t.start(); time.sleep(0.2); ths.append(t)
    for t in ths: t.join()
    okn = sum(1 for x in results.values() if x and x.get("ok"))
    print("retry wave %d/%d, cumulative ok: %d/%d" % (wi+1, nwaves, okn, len(results)), flush=True)
ok = [x for x in results.values() if x and x.get("ok")]
print("=== RETRY RESULT: %d/%d PASS ===" % (len(ok), TOTAL))
json.dump({"retried": TOTAL, "passed": len(ok), "workers": list(results.values())},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "c500_v2_retry_report.json"), "w"),
          ensure_ascii=False, indent=1)
for browser, ctx, hub, wid in hold:
    try: hub.close()
    except Exception: pass
    try: browser.close()
    except Exception: pass
print("retry sessions released", flush=True)
