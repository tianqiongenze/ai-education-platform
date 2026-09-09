#!/bin/bash
# Fix MFE SPA routing: mount a proper Caddyfile via ConfigMap
set -x

cat > /tmp/mfe-Caddyfile <<'EOF'
:80 {
	log {
		output stdout
	}
	handle /learning* {
		root * /openedx/dist/learning
		uri strip_prefix /learning
		try_files {path} /index.html
		file_server
	}
	handle /authn* {
		root * /openedx/dist/authn
		uri strip_prefix /authn
		try_files {path} /index.html
		file_server
	}
	handle /account* {
		root * /openedx/dist/account
		uri strip_prefix /account
		try_files {path} /index.html
		file_server
	}
	handle /profile* {
		root * /openedx/dist/profile
		uri strip_prefix /profile
		try_files {path} /index.html
		file_server
	}
	handle /gradebook* {
		root * /openedx/dist/gradebook
		uri strip_prefix /gradebook
		try_files {path} /index.html
		file_server
	}
	handle /discussions* {
		root * /openedx/dist/discussions
		uri strip_prefix /discussions
		try_files {path} /index.html
		file_server
	}
	handle /course-authoring* {
		root * /openedx/dist/course-authoring
		uri strip_prefix /course-authoring
		try_files {path} /index.html
		file_server
	}
	handle /learning {
		redir /learning/ /learning 308
	}
	redir / /learning 302
	handle {
		root * /openedx/dist
		try_files {path} {path}/index.html
		file_server
	}
}
EOF

kubectl -n openedx create cm mfe-caddy --from-file=Caddyfile=/tmp/mfe-Caddyfile --dry-run=client -o yaml | kubectl apply -f -

kubectl -n openedx patch deploy mfe --type json -p '[
  {"op":"add","path":"/spec/template/spec/volumes/-","value":{"name":"mfe-caddy","configMap":{"name":"mfe-caddy"}}},
  {"op":"add","path":"/spec/template/spec/containers/0/volumeMounts/-","value":{"name":"mfe-caddy","mountPath":"/etc/caddy/Caddyfile","subPath":"Caddyfile","readOnly":true}}
]'

kubectl -n openedx rollout status deploy/mfe --timeout=240s
echo "=== internal route tests ==="
kubectl exec -n openedx deploy/mfe -- sh -c "wget -S -q -O /dev/null http://localhost:80/learning 2>&1 | head -1; wget -S -q -O /dev/null http://localhost:80/authn 2>&1 | head -1; wget -S -q -O /dev/null http://localhost:80/ 2>&1 | head -1"
echo "=== ingress tests (apps host via :31825) ==="
for p in / /learning /authn /account /profile; do
  code=$(kubectl run curltest-mfe-$(echo $p | tr -cd 'a-z') --rm -i --restart=Never --image=curlimages/curl:8.4.0 --silent -- -sk -o /dev/null -w "%{http_code}" --resolve "apps.openedx.10.167.2.175.nip.io:31825:10.167.2.176" "https://apps.openedx.10.167.2.175.nip.io:31825$p" 2>/dev/null)
  echo "$p -> $code"
done
echo MFEFIXDONE
