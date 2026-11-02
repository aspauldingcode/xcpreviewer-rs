tell application id "com.apple.dt.Xcode"
set ws to active workspace document
if path of ws is not "/Users/8amps/xcpreviewer-rs/research/build/preview-workspaces/preview-ca9cbc8786144517b3a14ef57a90e08b/PreviewLab.xcodeproj" then error "Workspace identity mismatch"
set actionResult to build ws
repeat 100 times
 if completed of actionResult then return {completed of actionResult, status of actionResult, (build log of actionResult contains "RuntimeRefreshDependency.swift")}
 delay 0.2
end repeat
return {completed of actionResult, "deadline-observed-pending"}
end tell