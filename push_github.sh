#!/bin/bash
# Push all 4 projects to GitHub
TOKEN="REDACTED_TOKEN"
USER="tianqiongenze"

push_project() {
    local pod=$1
    local project=$2
    local dir=$3

    echo "=== Pushing $project from $pod ==="
    kubectl exec -n jupyterhub $pod -- bash -c "
        cd $dir
        # Set remote with token auth (URL-encoded)
        git remote remove origin 2>/dev/null || true
        git remote add origin https://$USER:$TOKEN@github.com/$USER/$project.git
        # Push
        git push -u origin master 2>&1 || git push -u origin main 2>&1
        # Clean up token from remote URL
        git remote set-url origin https://github.com/$USER/$project.git
        echo 'Push complete for $project'
    "
    echo ""
}

push_project jupyter-student-python "industrial-analytics" "/home/jovyan/work/industrial-analytics"
push_project jupyter-student-java "mes-system" "/home/jovyan/work/mes-system"
push_project jupyter-student-go "industrial-gateway" "/home/jovyan/work/industrial-gateway"
push_project jupyter-student-rust "security-audit" "/home/jovyan/work/security-audit"

echo "=== All projects pushed to GitHub ==="
