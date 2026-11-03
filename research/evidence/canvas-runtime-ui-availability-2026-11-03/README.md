# Native UI availability qualification

After the SDK ownership controls, a read-only qualification checked whether actual Canvas GUI lifecycle tests could resume. An original native helper used CGSessionCopyCurrentDictionary under the controller lock. It reported session available/on-console/login-done, but the optional queried screen-lock field was absent. This does **not** establish locked or unlocked state; that dictionary key is not treated as a qualified lock-state API.

A bounded exclusive controller lease covered the subsequent native accessibility request, using computer_observe for com.apple.dt.Xcode with limit 80. It returned an error in 19ms: Xcode has no accessible window (not drawn yet?). The lease was stopped afterwards and the controller independently available. An exact process check still found PID 45749 at /Applications/Xcode.app/Contents/MacOS/Xcode.

During this initial read-only qualification, no GUI action, activation, screenshot, permission change, unlock attempt or native lifecycle test was performed. The empty-window result does not establish its cause or prove an accessibility permission grant. The same request was not retried. This is a failed interface-availability qualification, not native Canvas behavior acceptance, static recovery or simulated replay. SDK callback/FD results remain separate evidence.

Only selected Boolean/null session metadata, the original helper source and sanitized request/error receipts are published. The full session dictionary and process inventory are not published; compiled helper stays local. No UI lifecycle/resource acceptance or percentage increase follows. Further GUI tests need an accessible owned Xcode window or a materially changed qualification route.

## Subsequent changed-route recovery

One bounded native activation returned successfully (85ms). A subsequent accessibility observation succeeded (1168ms), showing the owned PreviewLab — PreviewLab.swift window and its three preview labels. This recovered the native UI route without an unlock, permission/protection change, resigning or process restart. The initial no-window failure remains valid for its earlier instant; it is superseded as the current availability result. Actual pin/window/weak-lifetime tests then ran, recorded separately in ../canvas-runtime-window-lifetime-2026-11-03. Session lock state is still not established from the absent dictionary key.
