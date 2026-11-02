# Canvas status dashboard

Static GitHub Pages dashboard. `status.json` is the editable source of truth; percentages are calculated by `app.js`.

Three metrics are intentionally separate:

- **Overall delivery:** closed issues across M1 and M2 / their total issues. Initially 1/26 = 3.8% (rounded down to one decimal). 100% additionally requires all recovery areas and explicit Linux, macOS, Windows, standalone SwiftUI WASM runtime and full product conformance acceptance. Until then a fully closed tracker is capped at 99.9%.

- **Recovery gate acceptance:** accepted complete areas / nine required areas. Initially 0/9 = 0%. This is not an estimate of every behavior discovered.
- **GitHub milestone tasks:** closed issues / total milestone issues. Initial M1 1/10 = 10%; the closed item is the toolkit baseline. M2 0/16 = 0% and gated.

Before accepting an area, add explicit `acceptance.source`, `acceptance.native_controls`, `acceptance.contract`, `acceptance.replay` and `acceptance.target_coverage` evidence references. Only then set `status: "accepted"`. Preserve incomplete scopes. Record denominator changes instead of silently changing history.

At meaningful verified checkpoints: update snapshot date, qualified/remaining summaries, focus and recent work; refresh issue counts from GitHub; append a history row when acceptance/counts/denominator change. Do not invent historical percentages. Detailed recent evidence is local pending separate publication review; never add Apple binaries, disassembly or private captures to this site. GitHub source/milestone links are public.

Preview: `python3 -m http.server 57831 --bind 127.0.0.1 --directory status-site`.

Deployment: the Pages workflow copies only index.html, style.css, app.js and status.json into the public artifact and refreshes aggregate milestone counts via sync_status.py on relevant master updates, manual dispatch or hourly schedule. The user explicitly authorized making the original source repository public and enabling Pages there. The empty companion repository is not used. No plan changes or purchases are authorized.

Public site: https://aspauldingcode.github.io/xcpreviewer-rs/ . Pages is enabled on the original public repository; the workflow deploys without a repository-variable prerequisite. It refreshes aggregate milestone counts on relevant master pushes, manual runs and hourly schedules. Detailed evidence summaries still require explicit acceptance review; task counts do not establish native parity.
