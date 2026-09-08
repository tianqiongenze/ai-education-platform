# Industrial IoT Projects — GitHub Push Instructions

Four repositories were prepared on the master node (root@10.167.2.175),
each with a clean git history on branch `main`, a detailed README.md, a
language-appropriate .gitignore, and build artifacts removed. Each is saved
as a **git bundle** that can be pushed straight to GitHub.

## Why bundles and not a live push?

GitHub was reachable from the master node (HTTP 200), but the master node
has NO GitHub credentials: no `gh` CLI, no token in env, no `~/.gitconfig`,
no `~/.netrc`, no gh config. Creating repos via the GitHub API requires a
Personal Access Token, and pushing over HTTPS requires credentials. None
were available, so per the task's fallback path the repos were fully
prepared locally as bundles.

## The four repos (remote URLs use placeholder org `industrial-iot`)

| # | Project | Language | Bundle | Remote URL (edit owner as needed) |
|---|---------|----------|--------|----------------------------------------|
| 1 | MES System | Java 17 + Spring Boot | mes-system.bundle | https://github.com/industrial-iot/mes-system.git |
| 2 | Industrial Analytics | Python 3.11 + FastAPI | industrial-analytics.bundle | https://github.com/industrial-iot/industrial-analytics.git |
| 3 | Industrial Gateway | Go 1.21 + Gin | industrial-gateway.bundle | https://github.com/industrial-iot/industrial-gateway.git |
| 4 | Security Audit | Rust + Actix-Web | security-audit.bundle | https://github.com/industrial-iot/security-audit.git |

## Option A — Push from the master node (needs a GitHub PAT, repo scope)

1) Set up auth (one-time). GitHub no longer accepts account passwords for git
   over HTTPS, so you need a Personal Access Token
   (Settings -> Developer settings -> Personal access tokens -> repo scope).

   # cache the token for the session
   git config --global credential.helper store
   # then push once and enter username + PAT when prompted

   # OR provide the token inline (substitute YOUR_TOKEN and YOUR_GH_USER):
   # export GH_TOKEN=ghp_xxx
   # git remote set-url origin https://YOUR_GH_USER:GH_TOKEN@github.com/industrial-iot/mes-system.git

2) Create the 4 empty repos on GitHub (API, no local clone):
   curl -H "Authorization: token $GH_TOKEN" https://api.github.com/user/repos -d '{"name":"mes-system","private":true}'
   curl -H "Authorization: token $GH_TOKEN" https://api.github.com/user/repos -d '{"name":"industrial-analytics","private":true}'
   curl -H "Authorization: token $GH_TOKEN" https://api.github.com/user/repos -d '{"name":"industrial-gateway","private":true}'
   curl -H "Authorization: token $GH_TOKEN" https://api.github.com/user/repos -d '{"name":"security-audit","private":true}'
   (replace "user" with "orgs/ORG" in the path if using an org, and adjust the
   remote URLs below to match the chosen owner)

3) Push each repo (the working repos in /tmp/iot-projects already have
   'origin' set; if your owner differs, fix it first):
   for p in mes-system industrial-analytics industrial-gateway security-audit; do
     cd /tmp/iot-projects/$p
     # git remote set-url origin https://github.com/<OWNER>/$p.git
     git push -u origin main
   done

## Option B — Take the bundles off-box and push from a machine with GitHub auth

Copy /tmp/iot-projects/*.bundle to any host that has GitHub credentials, then:
   for p in mes-system industrial-analytics industrial-gateway security-audit; do
     git clone $p.bundle $p              # restores full repo + history
     cd $p
     git remote set-url origin https://github.com/<OWNER>/$p.git
     git push -u origin main
   done

## Verifying a push succeeded
   git ls-remote https://github.com/industrial-iot/mes-system.git        # shows refs/heads/main

## Layout on the master node
   /tmp/iot-projects/
   ├── mes-system/                 # full working repo (main branch)
   ├── industrial-analytics/       # full working repo (main branch)
   ├── industrial-gateway/         # full working repo (main branch)
   ├── security-audit/            # full working repo (main branch)
   ├── mes-system.bundle          # self-contained git bundle (clone/push source)
   ├── industrial-analytics.bundle
   ├── industrial-gateway.bundle
   ├── security-audit.bundle
   └── industrial-iot-repos.tar.gz # this dir minus the big working trees, for off-box transfer
