#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Publish all upgraded workflows (deep server-side validation + go live)."""
import requests, base64, json, time

BASE = "http://localhost:5001/console/api"

APPS = [
    "cbd7fa71-d8d1-45b5-bdf7-2c56d575669e",
    "1471e523-fe83-41fe-a2a8-9d56e8800de1",
    "2307bf62-6cd4-4599-a046-887c57e95387",
    "4e63c4d7-baf7-41b1-b295-c4565f72877e",
    "15b2a9b9-2823-4d55-8c10-30ff760e7382",
    "2dd72f64-61b6-46e8-8841-8300df3d921a",
    "6fe85559-7f51-4849-a3d3-3c596853864a",
    "9e8d3c60-d35c-4cc4-aec6-278e5214ef0b",
    "e3291494-d3d8-4933-a852-eb605bc8bf83",
]


def get_session(retries=5):
    for i in range(retries):
        s = requests.Session()
        try:
            r = s.post(BASE + "/login", json={
                "email": "myuwei@126.com",
                "password": base64.b64encode(b"Difyai123456").decode(),
                "language": "zh-Hans", "remember_me": True,
            }, timeout=30)
            if r.status_code == 200:
                s.headers["X-CSRF-Token"] = s.cookies.get("csrf_token", "")
                return s
        except Exception:
            pass
        time.sleep(3)
    raise Exception("login failed after retries")


def req(s, method, path, body=None, retries=4):
    for i in range(retries):
        try:
            if method == "GET":
                r = s.get(BASE + path, timeout=60)
            else:
                r = s.post(BASE + path, data=json.dumps(body).encode("utf-8"),
                            headers={"Content-Type": "application/json"}, timeout=60)
            if r.status_code == 200:
                return r.status_code, r.text
            # re-login on auth/csrf issues
            if r.status_code in (401, 403):
                s2 = get_session()
                s.headers.update(s2.headers)
                s.cookies.update(s2.cookies)
                continue
            return r.status_code, r.text
        except Exception as e:
            time.sleep(3)
    return 0, "request failed after retries"


def main():
    s = get_session()
    for aid in APPS:
        sc, body = req(s, "POST", f"/apps/{aid}/workflows/publish", {})
        try:
            rj = json.loads(body)
        except Exception:
            rj = {"raw": body[:200]}
        ok = sc == 200 and rj.get("result") == "success"
        print(f"{aid}  PUBLISH {'OK' if ok else 'FAIL'}  status={sc}  {body[:200]}")
        time.sleep(1)


if __name__ == "__main__":
    main()
