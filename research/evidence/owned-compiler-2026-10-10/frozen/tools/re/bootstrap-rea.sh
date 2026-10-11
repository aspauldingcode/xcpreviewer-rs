#!/bin/sh
# Pin REA without lifecycle scripts or global installation.
set -eu
project=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$project"
mkdir -p research/build/rea research/build/npm-cache
cp tools/re/rea/package.json tools/re/rea/package-lock.json research/build/rea/
npm ci --ignore-scripts --no-audit --no-fund --cache "$project/research/build/npm-cache" --prefix "$project/research/build/rea"
