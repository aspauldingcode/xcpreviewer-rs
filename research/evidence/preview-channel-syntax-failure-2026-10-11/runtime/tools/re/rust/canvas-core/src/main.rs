//! Finite owned-corpus verifier, not a general source-to-image CLI.
#![forbid(unsafe_code)]
use canvas_core::{validate, FrameAbi, FrameSpec, ALLOCATION};
use std::{fs::File, io::Read};
fn read(path: &str) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    if !std::fs::symlink_metadata(path)?.file_type().is_file() {
        return Err("Owned regular fixture required".into());
    }
    let mut bytes = Vec::new();
    File::open(path)?
        .take((ALLOCATION + 1) as u64)
        .read_to_end(&mut bytes)?;
    Ok(bytes)
}
fn run() -> Result<(), Box<dyn std::error::Error>> {
    let a: Vec<_> = std::env::args().skip(1).collect();
    if a.len() != 9 {
        return Err("width height stride memory pointer capacity rendered actual expected".into());
    }
    let spec = FrameSpec {
        width: a[0].parse()?,
        height: a[1].parse()?,
        stride: a[2].parse()?,
    };
    let abi = FrameAbi {
        memory: a[3].parse()?,
        pointer: a[4].parse()?,
        capacity: a[5].parse()?,
        rendered: a[6].parse()?,
    };
    validate(spec, abi, &read(&a[7])?, &read(&a[8])?).map_err(|e| format!("{e:?}"))?;
    println!("accepted {ALLOCATION}");
    Ok(())
}
fn main() {
    if let Err(e) = run() {
        eprintln!("rejected {e}");
        std::process::exit(2);
    }
}
