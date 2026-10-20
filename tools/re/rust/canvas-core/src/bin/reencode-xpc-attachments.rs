//! Reorder supported wire syntax and report attachment references; no native APIs.
use std::io::{Read, Write};
fn run() -> Result<(), String> {
    let a = std::env::args().skip(1).collect::<Vec<_>>();
    if a.len() != 4 {
        return Err("usage: reencode-xpc-attachments INPUT COUNT NEW_OUTPUT NEW_ORDER".into());
    }
    let n = a[1].parse::<u32>().map_err(|e| e.to_string())?;
    let mut b = Vec::new();
    std::fs::File::open(&a[0])
        .map_err(|e| e.to_string())?
        .take(64 * 1024 * 1024 + 1)
        .read_to_end(&mut b)
        .map_err(|e| e.to_string())?;
    let v =
        canvas_core::xpc_wire::decode_body_with_descriptors(&b, n).map_err(|e| format!("{e:?}"))?;
    let encoded =
        canvas_core::xpc_wire::encode_body_with_descriptors(&v, n).map_err(|e| format!("{e:?}"))?;
    let order = encoded
        .descriptor_order
        .iter()
        .map(|n| n.to_string())
        .collect::<Vec<_>>()
        .join("\n")
        + "\n";
    for (path, data) in [(&a[2], encoded.body.as_slice()), (&a[3], order.as_bytes())] {
        std::fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(path)
            .map_err(|e| e.to_string())?
            .write_all(data)
            .map_err(|e| e.to_string())?;
    }
    Ok(())
}
fn main() {
    if let Err(e) = run() {
        eprintln!("{e}");
        std::process::exit(1);
    }
}
