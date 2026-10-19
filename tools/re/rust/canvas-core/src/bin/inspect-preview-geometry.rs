//! Inspect decoded bitmap/region geometry in pixel and point coordinates.
use canvas_core::binary_plist::decode_render_payload_binary;
use canvas_core::preview_geometry::{regions_in_point_space, size_in_points};
fn run() -> Result<(), String> {
    use std::io::Read;
    let args = std::env::args_os().skip(1).collect::<Vec<_>>();
    if args.len() != 1 {
        return Err("usage: inspect-preview-geometry INPUT.bplist".into());
    }
    let f = std::fs::File::open(&args[0]).map_err(|e| e.to_string())?;
    let mut bytes = Vec::new();
    f.take(64 * 1024 * 1024 + 1)
        .read_to_end(&mut bytes)
        .map_err(|e| e.to_string())?;
    if bytes.len() > 64 * 1024 * 1024 {
        return Err("input exceeds 64 MiB".into());
    }
    let p = decode_render_payload_binary(&bytes).map_err(|e| format!("{e:?}"))?;
    let size = (
        p.bitmap_description.width as f64,
        p.bitmap_description.height as f64,
    );
    let points = regions_in_point_space(&p.selectable_regions, p.scale_factor);
    println!(
        "size_in_pixels={size:?} scale_factor={} size_in_points={:?} regions={}",
        p.scale_factor,
        size_in_points(size, p.scale_factor),
        points.len()
    );
    for (pixel, point) in p.selectable_regions.iter().zip(points) {
        println!(
            "path={:?} pixel_rect={:?} point_rect={:?} accessibility_bytes={}",
            pixel.path,
            pixel.rect,
            point.rect,
            pixel
                .serialized_accessibility_element
                .as_ref()
                .map_or(0, Vec::len)
        );
    }
    Ok(())
}
fn main() {
    if let Err(error) = run() {
        eprintln!("{error}");
        std::process::exit(1);
    }
}
