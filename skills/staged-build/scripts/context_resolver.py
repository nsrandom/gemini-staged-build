#!/usr/bin/env python3
"""
Context Resolver for Staged Build Plugin.
Extracts VCS state, feature specifications, active state, and pipeline routing configuration.
"""

import os
import sys
import json
import subprocess
import glob

def run_cmd(cmd):
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

def resolve_context():
    ctx = {
        "vcs": "none",
        "current_branch": "(n/a)",
        "branches": [],
        "uncommitted_code": "(clean)",
        "features": [],
        "active_feature": None,
        "state_content": None,
        "decisions_content": None,
        "pipeline_routing": {},
        "routing_source": "default"
    }

    # 1. VCS Check
    if os.path.exists(".jj"):
        ctx["vcs"] = "jj"
    elif os.path.exists(".git") or run_cmd("git rev-parse --is-inside-work-tree")[0] == 0:
        ctx["vcs"] = "git"
        _, branch, _ = run_cmd("git branch --show-current")
        ctx["current_branch"] = branch if branch else "(detached/none)"
        
        _, branch_list, _ = run_cmd("git branch --format='%(refname:short)'")
        ctx["branches"] = [b for b in branch_list.split('\n') if b]

        _, status_out, _ = run_cmd("git status --porcelain -- ':!specs'")
        ctx["uncommitted_code"] = status_out if status_out else "(clean)"

    # 2. Specs & Features Check
    if os.path.isdir("specs"):
        features = [d for d in os.listdir("specs") if os.path.isdir(os.path.join("specs", d))]
        ctx["features"] = sorted(features)
        if len(features) == 1:
            ctx["active_feature"] = features[0]
            state_file = os.path.join("specs", features[0], "STATE.md")
            if os.path.exists(state_file):
                with open(state_file, "r", encoding="utf-8") as f:
                    ctx["state_content"] = f.read()
            dec_file = os.path.join("specs", features[0], "DECISIONS.md")
            if os.path.exists(dec_file):
                with open(dec_file, "r", encoding="utf-8") as f:
                    ctx["decisions_content"] = f.read()

    # 3. Pipeline Routing Config
    workspace_pipeline = os.path.join(".agents", "pipeline.json")
    plugin_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    plugin_pipeline = os.path.join(plugin_dir, "pipeline.json")
    if not os.path.exists(plugin_pipeline) and os.path.exists("pipeline.json"):
        plugin_pipeline = "pipeline.json"

    if os.path.exists(workspace_pipeline):
        try:
            with open(workspace_pipeline, "r", encoding="utf-8") as f:
                ctx["pipeline_routing"] = json.load(f)
                ctx["routing_source"] = "workspace (.agents/pipeline.json)"
        except Exception:
            pass
    elif os.path.exists(plugin_pipeline):
        try:
            with open(plugin_pipeline, "r", encoding="utf-8") as f:
                ctx["pipeline_routing"] = json.load(f)
                ctx["routing_source"] = "plugin default"
        except Exception:
            pass

    return ctx

if __name__ == "__main__":
    context = resolve_context()
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        print(json.dumps(context, indent=2))
    else:
        print(f"=== Staged Build Context ===")
        print(f"VCS: {context['vcs']}")
        print(f"Branch: {context['current_branch']}")
        print(f"Uncommitted Code (excl specs): {context['uncommitted_code']}")
        print(f"Features in specs/: {', '.join(context['features']) if context['features'] else '(none)'}")
        print(f"Routing Source: {context['routing_source']}")
        print(f"Routing Config: {json.dumps(context['pipeline_routing'])}")
        if context['state_content']:
            print(f"\n--- STATE.md ---\n{context['state_content']}")
