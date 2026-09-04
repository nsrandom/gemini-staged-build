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
            feature_dir = os.path.join("specs", features[0])
            state_file = os.path.join(feature_dir, "STATE.md")
            if os.path.exists(state_file):
                with open(state_file, "r", encoding="utf-8") as f:
                    ctx["state_content"] = f.read()
            dec_file = os.path.join(feature_dir, "DECISIONS.md")
            if os.path.exists(dec_file):
                with open(dec_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    ctx["decisions_content"] = content
                    # Parse decision counts and tiers
                    dec_summary = {"total": 0, "tier1": 0, "tier2": 0, "unconfirmed": 0, "confirmed": 0, "rejected": 0, "deferred": 0, "modified": 0}
                    for line in content.splitlines():
                        line_s = line.strip()
                        if line_s.startswith("- **Tier:**"):
                            tier_val = line_s.split(":", 2)[-1].strip()
                            if "1" in tier_val:
                                dec_summary["tier1"] += 1
                            elif "2" in tier_val:
                                dec_summary["tier2"] += 1
                        elif line_s.startswith("- **Status:**"):
                            dec_summary["total"] += 1
                            status_val = line_s.split(":", 2)[-1].strip().lower()
                            if "unconfirmed" in status_val:
                                dec_summary["unconfirmed"] += 1
                            elif "confirmed" in status_val:
                                dec_summary["confirmed"] += 1
                            elif "rejected" in status_val:
                                dec_summary["rejected"] += 1
                            elif "deferred" in status_val:
                                dec_summary["deferred"] += 1
                            elif "modified" in status_val:
                                dec_summary["modified"] += 1
                    ctx["decision_summary"] = dec_summary
            
            # Session State check
            session_state_file = os.path.join(feature_dir, "SESSION_STATE.json")
            if os.path.exists(session_state_file):
                try:
                    with open(session_state_file, "r", encoding="utf-8") as f:
                        ctx["session_state"] = json.load(f)
                except Exception:
                    pass

            # Scratchpad check
            scratch_dir = os.path.join(feature_dir, "scratchpad")
            if os.path.isdir(scratch_dir):
                scratch_files = []
                for root, _, files in os.walk(scratch_dir):
                    for file in files:
                        scratch_files.append(os.path.relpath(os.path.join(root, file), feature_dir))
                ctx["has_scratchpad"] = True
                ctx["scratchpad_files"] = scratch_files
            else:
                ctx["has_scratchpad"] = False
                ctx["scratchpad_files"] = []

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
        if context.get("session_state"):
            ss = context["session_state"]
            print(f"Session State: Branch={ss.get('branch', 'n/a')}, BypassRequired={ss.get('sandbox_bypass_required', False)}")
        if context.get("decision_summary"):
            s = context["decision_summary"]
            print(f"Decisions: {s['total']} total ({s.get('tier1', 0)} Tier 1, {s.get('tier2', 0)} Tier 2) | {s['unconfirmed']} unconfirmed, {s['confirmed']} confirmed, {s['rejected']} rejected, {s['deferred']} deferred, {s['modified']} modified")
        if "has_scratchpad" in context:
            print(f"Scratchpad: {'Present (' + str(len(context['scratchpad_files'])) + ' files)' if context['has_scratchpad'] else 'None'}")
        print(f"Routing Source: {context['routing_source']}")
        print(f"Routing Config: {json.dumps(context['pipeline_routing'])}")
        if context['state_content']:
            print(f"\n--- STATE.md ---\n{context['state_content']}")
