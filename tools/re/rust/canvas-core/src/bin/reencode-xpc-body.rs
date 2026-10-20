//! Inspect/normalize an already extracted supported XPC body; no native calls.
use std::io::{Read, Write};
fn run() -> Result<(), String> {
    let a = std::env::args_os().skip(1).collect::<Vec<_>>();
    if a.len() != 2 {
        return Err("usage: reencode-xpc-body INPUT OUTPUT (new file)".into());
    }
    let mut b = Vec::new();
    std::fs::File::open(&a[0])
        .map_err(|e| e.to_string())?
        .take(64 * 1024 * 1024 + 1)
        .read_to_end(&mut b)
        .map_err(|e| e.to_string())?;
    let value = canvas_core::xpc_wire::decode_body(&b).map_err(|e| format!("{e:?}"))?;
    let encoded = canvas_core::xpc_wire::encode_body(&value).map_err(|e| format!("{e:?}"))?;
    std::fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&a[1])
        .map_err(|e| e.to_string())?
        .write_all(&encoded)
        .map_err(|e| e.to_string())?;
    println!("validated={} encoded={}", b.len(), encoded.len());
    Ok(())
}
fn main() {
    if let Err(e) = run() {
        eprintln!("{e}");
        std::process::exit(1);
    }
}
