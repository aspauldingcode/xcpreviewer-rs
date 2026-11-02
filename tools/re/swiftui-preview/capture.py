#!/usr/bin/env python3
"""Compile one SwiftUI factory, PreviewProvider or selected plain #Preview and atomically publish its first bitmap.

macOS producer; original payload adapter and bounds. No automatic PreviewProvider selection,
Xcode Canvas session, watcher, native interactions or project build inference.
"""
from pathlib import Path
import argparse, hashlib, json, math, os, platform, plistlib, re, signal
import subprocess, sys, tempfile

LIMIT = 32 * 1024 * 1024

def run(arguments, timeout, environment):
    process = subprocess.Popen(arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               env=environment, start_new_session=True)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
        # Only the process group created by this invocation is canceled.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate()
        if isinstance(error, KeyboardInterrupt):
            raise
        raise RuntimeError(f"Owned process exceeded {timeout:g} seconds") from None
    if process.returncode:
        raise RuntimeError(stderr[-65536:].decode(errors="replace") or
                           f"Owned process exited {process.returncode}")
    return stdout

def publish(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=".swiftui-preview-", dir=path.parent,
                                     delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
            stream.close()
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

def capture(args):
    if platform.system() != "Darwin" or platform.machine() not in ("arm64", "x86_64"):
        raise ValueError("SwiftUI capture requires a supported Mac")
    registry_index=args.preview_index
    if registry_index is not None and (platform.machine()!="arm64" or registry_index<0):
        raise ValueError("Registry capture requires arm64 Mac and a nonnegative preview index")
    provider = args.provider
    factory = args.factory if args.factory is not None else (None if provider is not None or registry_index is not None else "makePreview")
    if provider is not None and args.factory is not None:
        raise ValueError("Choose either a factory or a provider")
    selected = provider if provider is not None else factory
    if registry_index is None and (not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*", selected) or len(selected)>128):
        raise ValueError("Factory/provider must be a Swift identifier or qualified identifier")
    if not 1<=args.width<=2048 or not 1<=args.height<=2048 or args.width*args.height*args.scale**2*4>LIMIT:
        raise ValueError("Capture dimensions exceed the 32 MiB bitmap limit")
    if not math.isfinite(args.runtime_seconds) or not 0.1<=args.runtime_seconds<=8:
        raise ValueError("Runtime deadline must be between 0.1 and 8 seconds")
    source=Path(args.source).resolve(strict=True)
    if not source.is_file() or source.stat().st_size>1024*1024:
        raise ValueError("Source must be a file of at most 1 MiB")
    with source.open("rb") as stream:
        source_bytes=stream.read(1024*1024+1)
    if len(source_bytes)>1024*1024:
        raise ValueError("Source exceeds 1 MiB")
    output=Path(args.output).absolute()
    reference=Path(args.reference_png).absolute() if args.reference_png else None
    paths=[output]+([reference] if reference else [])
    if any(p.is_symlink() for p in paths) or source in [p.resolve() for p in paths] or (reference and output.resolve()==reference.resolve()):
        raise ValueError("Output paths must be distinct files and cannot replace the source or symlinks")
    environment={k:v for k,v in os.environ.items() if not k.startswith("DYLD_")}
    compiler=run(["xcrun","--find","swiftc"],5,environment).decode().strip()
    sdk=run(["xcrun","--show-sdk-path"],5,environment).decode().strip()
    version=run([compiler,"--version"],5,environment).decode().strip()
    template=(Path(__file__).with_name("Capture.swift.template")).read_text()
    expression = f"Self.providerContent({provider}.self)" if provider is not None else f"{factory}()"
    registry=None
    if registry_index is not None:
        from discover import discover
        discovery=discover(str(source),args.runtime_seconds)
        if discovery['source_sha256']!=hashlib.sha256(source_bytes).hexdigest() or discovery['compiler']!=compiler or discovery['compiler_version']!=version:
            raise ValueError("Source/compiler changed during registry discovery")
        if registry_index>=len(discovery['previews']):
            raise ValueError("Preview index is outside the discovered registry list")
        registry=discovery['previews'][registry_index]
        expression=f"try RegistryBridge.content(`{registry['registry']}`.self)"
    wrapper=template.replace("__PREVIEW_CONTENT__",expression)
    receipt_code='try JSONSerialization.data(withJSONObject:RegistryBridge.receipt,options:[.sortedKeys]).write(to:root.appendingPathComponent("registry.json"))' if registry else ''
    wrapper=wrapper.replace("__PREVIEW_RECEIPT__",receipt_code)
    deployment=platform.machine()+"-apple-macos"+("14.0" if registry else "13.0")
    native_registry=None
    adapter_hashes=None
    with tempfile.TemporaryDirectory(prefix="swiftui-preview-") as directory:
        work=Path(directory)
        (work/"Source.swift").write_bytes(source_bytes)
        (work/"Capture.swift").write_text(wrapper)
        executable=work/"capture"
        compile_args=[compiler,"-parse-as-library","-sdk",sdk,"-target",deployment,
                      "-module-cache-path",str(work/"module-cache")]
        if registry:
            here=Path(__file__).parent
            adapter_hashes={}
            for name in ["Registry.swift","RegistryBridge.s","RegistryBridge.h","RegistryIdentity.c"]:
                content=(here/name).read_bytes()
                (work/name).write_bytes(content)
                adapter_hashes[name]=hashlib.sha256(content).hexdigest()
            for name in ["RegistryBridge.s","RegistryIdentity.c"]:
                run(["xcrun","clang","-arch","arm64","-c",str(work/name),"-o",str(work/(name+".o"))],30,environment)
            compile_args += ["-module-name","PreviewDiscovery","-import-objc-header",str(work/"RegistryBridge.h"),
                             str(work/"Registry.swift"),str(work/"RegistryBridge.s.o"),str(work/"RegistryIdentity.c.o")]
        run(compile_args+[str(work/"Source.swift"),str(work/"Capture.swift"),"-o",str(executable)],30,environment)
        run([str(executable),str(args.width),str(args.height),str(args.scale),str(work)],
            args.runtime_seconds,environment)
        if registry:
            with (work/"registry.json").open("rb") as stream:
                receipt_bytes=stream.read(65537)
            if len(receipt_bytes)>65536: raise ValueError("Registry receipt exceeds 64 KiB")
            native_registry=json.loads(receipt_bytes)
            if native_registry.get('body_calls')!=1 or native_registry.get('getter_calls')!=1 or native_registry.get('body_destroys')!=1:
                raise ValueError("Unexpected registry native receipt")
        with (work/"capture.bplist").open("rb") as stream:
            payload=stream.read(64*1024*1024+1)
        with (work/"reference.png").open("rb") as stream:
            png=stream.read(64*1024*1024+1)
        if len(payload)>64*1024*1024 or len(png)>64*1024*1024:
            raise ValueError("Native capture artifact exceeds 64 MiB")
        value=plistlib.loads(payload)
        bitmap=value["bitmapDescription"]
        expected=(args.width*args.scale,args.height*args.scale)
        if (bitmap["width"],bitmap["height"])!=expected or bitmap["bytesPerRow"]!=expected[0]*4 or bitmap["bitmapInfo"]!=8194 or bitmap["bitsPerPixel"]!=32 or bitmap["bitsPerComponent"]!=8 or bitmap["byteOrder"]!="little" or bitmap["colorSpace"]!="kCGColorSpaceSRGB" or len(bitmap["data"])!=expected[0]*expected[1]*4 or value["scaleFactor"]!=args.scale or value["snapshotCornerRadius"]!=0 or value["selectableRegions"]!=[]:
            raise ValueError("Native capture returned an unexpected bitmap profile")
        # All compile/render/shape checks finish before either output is replaced.
        # Each file is atomic individually; the optional diagnostic PNG is not a
        # transactional pair with the payload.
        if reference:
            publish(reference,png)
        publish(output,payload)
    sha=lambda data:hashlib.sha256(data).hexdigest()
    return {"producer":"SwiftUI.ImageRenderer","factory":factory,"provider":provider,"preview_index":registry_index,"registry":registry,"native_registry":native_registry,"registry_adapter_sha256":adapter_hashes,"source_sha256":sha(source_bytes),
            "renderer_source_sha256":sha(wrapper.encode()),"deployment_target":deployment,"compiler":compiler,"compiler_version":version,
            "point_size":[args.width,args.height],"pixel_size":list(expected),"scale":args.scale,
            "output":str(output),"payload_sha256":sha(payload),"reference_png_sha256":sha(png)}

def argument_parser():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    selection=parser.add_mutually_exclusive_group()
    selection.add_argument("--factory",help="Zero-argument view factory (default: makePreview)")
    selection.add_argument("--provider",help="Explicit PreviewProvider type; renders its complete previews value")
    selection.add_argument("--preview-index",type=int,help="Capture one discovered plain #Preview (qualified arm64 runtime only)")
    parser.add_argument("--output",required=True)
    parser.add_argument("--reference-png")
    parser.add_argument("--width",type=int,default=320)
    parser.add_argument("--height",type=int,default=240)
    parser.add_argument("--scale",type=int,choices=range(1,5),default=1)
    parser.add_argument("--runtime-seconds",type=float,default=8)
    return parser

def main():
    args=argument_parser().parse_args()
    try:
        print(json.dumps(capture(args),sort_keys=True))
    except (OSError,ValueError,RuntimeError,KeyError,TypeError) as error:
        print(str(error),file=sys.stderr)
        return 1
    return 0

if __name__=="__main__":
    sys.exit(main())
