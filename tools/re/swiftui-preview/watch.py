#!/usr/bin/env python3
"""Recapture one SwiftUI source revision at a time, preserving the last good frame."""
from pathlib import Path
import hashlib, json, math, sys, tempfile, time
from types import SimpleNamespace
import capture

MAX_SOURCE = 1024 * 1024

def source_bytes(source):
    with source.open("rb") as stream:
        data = stream.read(MAX_SOURCE + 1)
    if len(data) > MAX_SOURCE:
        raise ValueError("Source exceeds 1 MiB")
    return data

def destinations(args, source):
    paths = [Path(args.output).absolute()]
    if args.reference_png:
        paths.append(Path(args.reference_png).absolute())
    if any(path.is_symlink() for path in paths):
        raise ValueError("Output paths cannot be symlinks")
    resolved = [path.resolve() for path in paths]
    if source.resolve() in resolved or len(set(resolved)) != len(resolved):
        raise ValueError("Output paths must be distinct and cannot replace the source")
    return paths

def attempt(args, source, data, producer=capture.capture):
    # Compile an immutable snapshot. The real destinations are replaced only
    # after source identity is checked again; native capture writes into scratch.
    paths = destinations(args, source)
    digest = hashlib.sha256(data).hexdigest()
    with tempfile.TemporaryDirectory(prefix="swiftui-watch-") as directory:
        work = Path(directory)
        snapshot = work / "Source.swift"
        snapshot.write_bytes(data)
        local = vars(args).copy()
        local.update(source=str(snapshot), output=str(work / "frame.bplist"),
                     reference_png=str(work / "frame.png") if args.reference_png else None)
        receipt = producer(SimpleNamespace(**local))
        if source_bytes(source) != data:
            return {"status": "superseded", "source_sha256": digest}
        # Recheck identities immediately before publication. This is not a
        # filesystem transaction with source edits or the optional PNG.
        destinations(args, source)
        payload = (work / "frame.bplist").read_bytes()
        png = (work / "frame.png").read_bytes() if args.reference_png else None
        if len(payload) > 64*1024*1024 or (png is not None and len(png) > 64*1024*1024):
            raise ValueError("Capture artifact exceeds 64 MiB")
        if png is not None:
            capture.publish(paths[1], png)
        capture.publish(paths[0], payload)
        receipt.update(output=str(paths[0]), source=str(source), source_sha256=digest)
        return {"status": "published", "capture": receipt}

def watch(args, emit=lambda value: print(json.dumps(value, sort_keys=True), flush=True)):
    if not math.isfinite(args.interval) or not 0.05 <= args.interval <= 10:
        raise ValueError("Polling interval must be between 0.05 and 10 seconds")
    if not math.isfinite(args.debounce) or not 0 <= args.debounce <= 10:
        raise ValueError("Debounce must be between 0 and 10 seconds")
    source = Path(args.source).absolute()
    destinations(args, source)
    attempted = None
    pending = None
    changed_at = 0.0
    read_error = None
    while True:
        try:
            data = source_bytes(source)
            revision = hashlib.sha256(data).hexdigest()
            read_error = None
        except (OSError, ValueError) as error:
            message = str(error)
            if message != read_error:
                emit({"status": "source-error", "error": message})
            read_error = message
            pending = None
            if args.once:
                return 1
            time.sleep(args.interval)
            continue
        if revision != pending:
            pending, changed_at = revision, time.monotonic()
        if revision != attempted and (args.once or time.monotonic()-changed_at >= args.debounce):
            attempted = revision
            emit({"status": "capturing", "source_sha256": revision})
            try:
                result = attempt(args, source, data)
            except (OSError, ValueError, RuntimeError, KeyError, TypeError) as error:
                result = {"status": "capture-error", "source_sha256": revision, "error": str(error)}
            emit(result)
            if args.once:
                return 0 if result["status"] == "published" else 1
        time.sleep(args.interval)

def main():
    parser = capture.argument_parser()
    parser.description = __doc__
    parser.add_argument("--interval", type=float, default=0.25)
    parser.add_argument("--debounce", type=float, default=0.5)
    parser.add_argument("--once", action="store_true", help="Capture one snapshot and exit")
    args = parser.parse_args()
    try:
        return watch(args)
    except KeyboardInterrupt:
        return 130
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
