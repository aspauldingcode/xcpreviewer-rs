//! Finite configuration-to-raw allocation CLI, not a Swift source compiler.
#![forbid(unsafe_code)]
use canvas_core::{render_primary, FrameSpec, ALLOCATION};
fn run() -> Result<(), Box<dyn std::error::Error>> {
    let a: Vec<_> = std::env::args().skip(1).collect();
    if a.len() != 8 {
        return Err("width height stride red green blue reverse output".into());
    }
    let spec = FrameSpec {
        width: a[0].parse()?,
        height: a[1].parse()?,
        stride: a[2].parse()?,
    };
    let alphas = [a[3].parse()?, a[4].parse()?, a[5].parse()?];
    let order: u8 = a[6].parse()?;
    if order > 1 {
        return Err("Unsupported primary order".into());
    }
    let mut output = vec![0; ALLOCATION];
    let used =
        render_primary(spec, alphas, order == 1, &mut output).map_err(|e| format!("{e:?}"))?;
    std::fs::write(&a[7], &output)?;
    println!("rendered {used} {ALLOCATION}");
    Ok(())
}
fn main() {
    if let Err(e) = run() {
        eprintln!("rejected {e}");
        std::process::exit(2);
    }
}
