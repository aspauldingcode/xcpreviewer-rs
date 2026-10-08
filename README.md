# xcpreviewer-rs

Research toward a portable Swift view previewer. This repository begins with reverse engineering of Xcode's preview pipeline; it is not yet a working SwiftUI-to-WebAssembly renderer.

The proposed roadmap is in [plan.md](plan.md). Its dependency versions, protocol examples, and portability assumptions are proposals to validate against observed behavior.

`master` holds the baseline; `development` holds ongoing investigation and implementation. Reverse engineering tools and findings will land on `development` first.
