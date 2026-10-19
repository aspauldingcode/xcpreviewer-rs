//! Convert a decoded preview bitmap into tightly packed premultiplied RGBA8.
use canvas_core::binary_plist::decode_render_payload_binary;
fn run() -> Result<(), String> {
    use std::io::Read;
    let args = std::env::args_os().skip(1).collect::<Vec<_>>();
    if args.len() != 2 {
        return Err(
            "usage: render-preview-bitmap INPUT.bplist OUTPUT.rgba (premultiplied RGBA8)".into(),
        );
    }
    let file = std::fs::File::open(&args[0]).map_err(|e| e.to_string())?;
    let mut bytes = Vec::new();
    file.take(64 * 1024 * 1024 + 1)
        .read_to_end(&mut bytes)
        .map_err(|e| e.to_string())?;
    if bytes.len() > 64 * 1024 * 1024 {
        return Err("input exceeds 64 MiB".into());
    }
    let p = decode_render_payload_binary(&bytes).map_err(|e| format!("{e:?}"))?;
    let b = p.bitmap_description;
    let width = usize::try_from(b.width).map_err(|_| "invalid width")?;
    let height = usize::try_from(b.height).map_err(|_| "invalid height")?;
    let stride = width.checked_mul(4).ok_or("width overflow")?;
    let length = stride
        .checked_mul(height)
        .filter(|n| *n <= 64 * 1024 * 1024)
        .ok_or("output exceeds limit")?;
    let mut output = vec![0; length];
    b.write_premultiplied_rgba8(stride, &mut output)
        .map_err(|e| format!("{e:?}"))?;
    std::fs::write(&args[1], &output).map_err(|e| e.to_string())?;
    println!(
        "width={width} height={height} stride={stride} bytes={length} format=premultiplied-RGBA8"
    );
    Ok(())
}
fn main() {
    if let Err(error) = run() {
        eprintln!("{error}");
        std::process::exit(1);
    }
}
