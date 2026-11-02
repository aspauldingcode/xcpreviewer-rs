# Native project buildable-selection policy

This advances the recovery-first project-binding gate, not standalone Canvas implementation. The shipped PreviewsIDEAPI BuildSystem.buildables interface names scheme, workspace, run-context manager and execution environment. Selected implementation source qualifies scheme/workspace buildable selection and preferences; no runtime use of a real workspace/scheme or behavior of every parameter is claimed. Related PreviewsXcode XcodeWorkspaceBuilder graph/dependency methods were found as symbol candidates only; their caller relationship remains to be followed.

Full image hashes/UUIDs are pinned. The complete buildables function (0x6f50–0x7418) and its package-selector helper (0x7418–0x747c) total 1,324 independently byte-checked instruction bytes. Native Objective-C selector stubs and preference strings bind the selected operations. No private Swift ABI or native method is invoked.

Source policy:
- Read PreviewsBuildAllPackageTargets and pass its Boolean inverse to the includingPackages argument of the workspace/scheme buildables query.
- When that preference is true, append primaryBuildable values from blueprints of workspace referenced source packages.
- Read PreviewsBuildTestTargets through a lookup with explicit false fallback. Effective runtime defaults are not measured. With the test preference true, the filter retains buildables whose blueprint lacks the packageProductType selector. With false, it retains selector-bearing blueprints or other blueprints that respond to isUnitTest and return false; a non-marker blueprint without that selector is excluded.
- The package helper tests respondsToSelector for packageProductType. It does not read a packageProductType property value. Native type names do not justify substituting a different predicate.

These are source-backed observations on one pinned build, not a complete semantic model of package products, target discovery or Canvas project binding. No native preference is read/changed at runtime. No project is opened, build dispatched, Canvas selected or user Xcode/simulator process controlled. No Rust/product changes or test rerun. Required runtime project/selection/refresh comparisons and all-target coverage remain open; both milestones incomplete.

GhidraVibe read-only project listing did not return before its orchestration cell was stopped; no Ghidra target identity/result was obtained and backend cancellation is not asserted. Local symbol/disassembly analysis provided a permitted route. Initial LLVM Mach-O disassembly ignored requested bounds and returned a broader local dump; generic ARM64 mode produced exactly selected addresses with every word equal to file bytes. Raw symbol/disassembly files stay only in temporary directories, including direct source.py execution. This package contains original verification code and sanitized findings, not Apple instruction bodies/binaries.

verify.py checks its original source pin, copies it into a fresh directory and rechecks installed images, selected instruction bytes, selectors and metadata under a nonblocking exclusive controller. Native analyses use bounded subprocess deadlines; controller releases on exit. Publication and matching issue updates remain pending the existing explicit approval gate.

Fresh disposable source replay passed: both image identities and all selected words/selectors/anchors reproduce the complete source findings. Native workspace behavior remains untested.
