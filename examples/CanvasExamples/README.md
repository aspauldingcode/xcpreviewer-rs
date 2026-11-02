# Canvas examples

Open `PreviewLab.xcodeproj` in Xcode, choose **PreviewLab → My Mac**, then open
`Sources/PreviewLab/PreviewLab.swift` and resume Canvas.

Three named previews exercise separate boundaries:

| Preview | Edit to try | Portable reconstruction |
|---|---|---|
| Primary layers | Green opacity `0.25` → `0.75` | Extracted `ZStack.frame` expression supported; full app source and `#Preview` macro are not parser inputs |
| Text and interaction | Change title; click Increment in Live mode | Text, Button, state, font and refresh behavior remain unsupported |
| Layout edit | `HStack` → `VStack` | Layout and Rectangle remain unsupported |

The baseline is intentionally restored after testing. The white text backgrounds use
explicit black foregrounds. Examples are self-contained and require no network.

For automated research, copy this project into `research/build/preview-workspaces`
using `reloop.canvas.workspace`; edit the owned copy. Close its Xcode workspace
after each session, preserving other user projects.

See [measured comparison](../../docs/reverse-engineering/canvas-edit-comparison.md)
for source snapshots, native screenshots, portable outputs and scope limits.
