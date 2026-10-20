//! Inspect remote request data. No capture, symbolication or transport is invoked.
use canvas_core::remote_crash::RemoteEventRequest;
fn run() -> Result<(), String> {
    use std::io::Read;
    let args = std::env::args_os().skip(1).collect::<Vec<_>>();
    if args.len() != 1 {
        return Err("usage: inspect-preview-request INPUT.bplist".into());
    }
    let f = std::fs::File::open(&args[0]).map_err(|e| e.to_string())?;
    let mut b = Vec::new();
    f.take(64 * 1024 * 1024 + 1)
        .read_to_end(&mut b)
        .map_err(|e| e.to_string())?;
    if b.len() > 64 * 1024 * 1024 {
        return Err("input exceeds 64 MiB".into());
    }
    match RemoteEventRequest::decode_binary(&b).map_err(|e| format!("{e:?}"))? {
        RemoteEventRequest::RequestScreenshot => println!("request=requestScreenshot"),
        RemoteEventRequest::SymbolicateCrashedDiagnostics(r) => println!(
            "request=symbolicateCrashedDiagnostics report={} pid={} images={} frames={}",
            r.id.canonical(),
            r.pid,
            r.images.len(),
            r.frames.len()
        ),
    };
    Ok(())
}
fn main() {
    if let Err(e) = run() {
        eprintln!("{e}");
        std::process::exit(1);
    }
}
