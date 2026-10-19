//! Decode a bounded binary preview payload and optionally export its exact data.
use canvas_core::binary_plist::decode_render_payload_binary;
fn run() -> Result<(), String> {
    let args = std::env::args_os().skip(1).collect::<Vec<_>>();
    if !(1..=2).contains(&args.len()) {
        return Err("usage: decode-preview-payload INPUT.bplist [BITMAP_OUTPUT]".into());
    }
    // Bound input allocation independently of the recursive decoder budgets.
    use std::io::Read;
    let f = std::fs::File::open(&args[0]).map_err(|e| e.to_string())?;
    let mut bytes = Vec::new();
    f.take(64 * 1024 * 1024 + 1)
        .read_to_end(&mut bytes)
        .map_err(|e| e.to_string())?;
    if bytes.len() > 64 * 1024 * 1024 {
        return Err("input exceeds 64 MiB".into());
    }
    let p = decode_render_payload_binary(&bytes).map_err(|e| format!("{e:?}"))?;
    if args.len() == 2 {
        std::fs::write(&args[1], &p.bitmap_description.data).map_err(|e| e.to_string())?;
    }
    println!("width={} height={} stride={} bytes={} bitmap_info={} bits_per_component={} bits_per_pixel={} corner={} scale={} regions={}",
        p.bitmap_description.width,p.bitmap_description.height,p.bitmap_description.bytes_per_row,
        p.bitmap_description.data.len(),p.bitmap_description.bitmap_info,
        p.bitmap_description.bits_per_component,p.bitmap_description.bits_per_pixel,
        p.snapshot_corner_radius,p.scale_factor,p.selectable_regions.len());
    Ok(())
}
fn main() {
    if let Err(error) = run() {
        eprintln!("{error}");
        std::process::exit(1);
    }
}
