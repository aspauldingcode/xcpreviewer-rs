//! Inspect supported crash notifications without acting on any process.
use canvas_core::remote_crash::{RemoteEventPayload, STREAM_IDENTIFIER};
fn run() -> Result<(), String> {
    use std::io::Read;
    let args = std::env::args_os().skip(1).collect::<Vec<_>>();
    if args.len() != 1 {
        return Err("usage: inspect-preview-crash INPUT.bplist".into());
    }
    let f = std::fs::File::open(&args[0]).map_err(|e| e.to_string())?;
    let mut bytes = Vec::new();
    f.take(64 * 1024 * 1024 + 1)
        .read_to_end(&mut bytes)
        .map_err(|e| e.to_string())?;
    if bytes.len() > 64 * 1024 * 1024 {
        return Err("input exceeds 64 MiB".into());
    }
    let e = RemoteEventPayload::decode_binary(&bytes).map_err(|e| format!("{e:?}"))?;
    match e {
        RemoteEventPayload::AgentCrashed(e) => println!(
            "stream={STREAM_IDENTIFIER} pid={} agent_behavior={:?}",
            e.pid, e.agent_behavior
        ),
        RemoteEventPayload::AgentCrashedDiagnostics(r) => println!(
            "stream={STREAM_IDENTIFIER} diagnostics_report={} pid={} images={} frames={}",
            r.id.canonical(),
            r.pid,
            r.images.len(),
            r.frames.len()
        ),
    }
    Ok(())
}
fn main() {
    if let Err(e) = run() {
        eprintln!("{e}");
        std::process::exit(1);
    }
}
