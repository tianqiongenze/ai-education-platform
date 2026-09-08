import os, sys
filepath = "/usr/local/lib/python3.11/site-packages/litellm/proxy/auth/user_api_key_auth.py"
with open(filepath, "r") as f:
    content = f.read()

old_line = '        elif api_key is None:  # only require api key if master key is set\n            raise Exception("No api key passed in.")'

new_line = '        elif api_key is None:  # only require api key if master key is set\n            if os.environ.get("LITELLM_ALLOW_REQUESTS_WITHOUT_API_KEY", "false").lower() == "true":\n                return UserAPIKeyAuth(\n                    api_key=master_key,\n                    user_role=LitellmUserRoles.INTERNAL_USER,\n                    parent_otel_span=parent_otel_span,\n                )\n            else:\n                raise Exception("No api key passed in.")'

if old_line in content:
    content = content.replace(old_line, new_line)
    with open(filepath, "w") as f:
        f.write(content)
    print("PATCHED: return early when no API key + ALLOW_REQUESTS_WITHOUT_API_KEY=true")
elif "LITELLM_ALLOW_REQUESTS_WITHOUT_API_KEY" in content and "return UserAPIKeyAuth" in content:
    print("Already patched with early return!")
elif "LITELLM_ALLOW_REQUESTS_WITHOUT_API_KEY" in content:
    # Previous patch only set api_key, need to update to return early
    old_patch = '        elif api_key is None:  # only require api key if master key is set\n            if os.environ.get("LITELLM_ALLOW_REQUESTS_WITHOUT_API_KEY", "false").lower() == "true":\n                api_key = master_key\n            else:\n                raise Exception("No api key passed in.")'
    if old_patch in content:
        content = content.replace(old_patch, new_line)
        with open(filepath, "w") as f:
            f.write(content)
        print("UPDATED: changed api_key=master_key to return UserAPIKeyAuth early")
    else:
        print("WARN: old patch found but pattern mismatched")
        idx = content.find("LITELLM_ALLOW_REQUESTS_WITHOUT_API_KEY")
        if idx >= 0:
            print(content[idx-200:idx+300])
        sys.exit(1)
else:
    print("WARN: pattern not found")
    idx = content.find("elif api_key is None")
    if idx >= 0:
        print(content[idx-100:idx+300])
    sys.exit(1)
