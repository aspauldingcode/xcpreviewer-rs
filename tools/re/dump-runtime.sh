#!/bin/sh
# Keep OS-side and Xcode-side Foundation implementations in separate processes.
set -eu
project=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
xcode=${XCODE_APP:-/Applications/Xcode.app}
export DEVELOPER_DIR="$xcode/Contents/Developer"
cd "$project"
mkdir -p research/build research/runtime
xcrun clang -fobjc-arc -framework Foundation "-Wl,-rpath,$xcode/Contents" -o research/build/runtime-dump tools/re/runtime_dump.m
research/build/runtime-dump \
  /System/Library/PrivateFrameworks/PreviewsServices.framework/PreviewsServices \
  /System/Library/PrivateFrameworks/PreviewsMessagingOS.framework/PreviewsMessagingOS \
  > research/runtime/os.json 2> research/runtime/os.stderr
research/build/runtime-dump \
  "$xcode/Contents/SharedFrameworks/PreviewsMessagingHost.framework/PreviewsMessagingHost" \
  > research/runtime/host.json 2> research/runtime/host.stderr
xcrun clang -fobjc-arc -framework Foundation -o research/build/plist-probe tools/re/plist_probe.m
research/build/plist-probe > research/runtime/plist-probe.json
xcrun swiftc -module-cache-path research/build/swift-cache tools/re/message_keys.swift \
  -Xlinker "$xcode/Contents/SharedFrameworks/PreviewsMessagingHost.framework/PreviewsMessagingHost" \
  -Xlinker -rpath -Xlinker "$xcode/Contents" -o research/build/message-keys
research/build/message-keys > research/runtime/message-keys.json
