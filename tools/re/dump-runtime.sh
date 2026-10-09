#!/bin/sh
# Keep OS-side and Xcode-side Foundation implementations in separate processes.
set -eu
project=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
xcode=${XCODE_APP:-/Applications/Xcode.app}
export DEVELOPER_DIR="$xcode/Contents/Developer"
cd "$project"
output=${RE_OUT:-"$project/research"}
mkdir -p "$output/build" "$output/runtime"
xcrun clang -fobjc-arc -framework Foundation "-Wl,-rpath,$xcode/Contents" -o "$output/build/runtime-dump" tools/re/runtime_dump.m
"$output/build/runtime-dump" \
  /System/Library/PrivateFrameworks/PreviewsServices.framework/PreviewsServices \
  /System/Library/PrivateFrameworks/PreviewsMessagingOS.framework/PreviewsMessagingOS \
  > "$output/runtime/os.json" 2> "$output/runtime/os.stderr"
"$output/build/runtime-dump" \
  "$xcode/Contents/SharedFrameworks/PreviewsMessagingHost.framework/PreviewsMessagingHost" \
  > "$output/runtime/host.json" 2> "$output/runtime/host.stderr"
xcrun clang -fobjc-arc -framework Foundation -o "$output/build/plist-probe" tools/re/plist_probe.m
"$output/build/plist-probe" > "$output/runtime/plist-probe.json"
xcrun swiftc -module-cache-path "$output/build/swift-cache" tools/re/message_keys.swift \
  -Xlinker "$xcode/Contents/SharedFrameworks/PreviewsMessagingHost.framework/PreviewsMessagingHost" \
  -Xlinker -rpath -Xlinker "$xcode/Contents" -o "$output/build/message-keys"
"$output/build/message-keys" > "$output/runtime/message-keys.json"
