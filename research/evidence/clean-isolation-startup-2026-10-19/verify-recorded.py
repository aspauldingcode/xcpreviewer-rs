import json,sys
from pathlib import Path
p=Path(sys.argv[1])
for label in ["v1","v2","v3"]:
 r=json.loads((p/label/"results.json").read_text()); s=json.loads((p/label/"summary.json").read_text())
 if len(r)!=7 or r[0]["exit"]!=0 or not r[0]["stdout_matches_owned_sentinel"] or r[0]["stdout_bytes"]!=23: raise ValueError("control mismatch")
 if any(x["exit"]!=-6 or x["stdout_bytes"]!=0 for x in r[1:]): raise ValueError("recorded startup relation changed")
 if s["passed"] or s["output_exact"] or not s["input_intact"] or s["model_tool_isolation_proven"] or s["handoff_approved"]: raise ValueError("failed startup promoted")
print("Three failed candidates retained; no isolation or handoff acceptance.")
