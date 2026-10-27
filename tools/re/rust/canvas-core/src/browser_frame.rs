//! Original bounded presentation packet for the browser host; not Apple wire format.
use crate::{
    binary_plist::decode_render_payload_binary,
    preview_geometry::{regions_in_point_space, size_in_points},
};
const LIMIT: usize = 64 * 1024 * 1024;
pub fn frame_packet(input: &[u8]) -> Result<Vec<u8>, String> {
    if input.len() > LIMIT {
        return Err("Preview file exceeds 64 MiB".into());
    }
    let p = decode_render_payload_binary(input)
        .map_err(|e| format!("Invalid preview payload: {e:?}"))?;
    if !p.scale_factor.is_finite() || p.scale_factor <= 0.0 {
        return Err("Display requires a positive finite scale".into());
    }
    if !p.snapshot_corner_radius.is_finite() || p.snapshot_corner_radius < 0.0 {
        return Err("Display requires a finite nonnegative corner radius".into());
    }
    let b = &p.bitmap_description;
    let width = usize::try_from(b.width).map_err(|_| "Invalid bitmap width")?;
    let height = usize::try_from(b.height).map_err(|_| "Invalid bitmap height")?;
    let stride = width.checked_mul(4).ok_or("Bitmap width overflow")?;
    let length = stride
        .checked_mul(height)
        .filter(|n| *n <= LIMIT)
        .ok_or("Bitmap exceeds display limit")?;
    let points = size_in_points((b.width as f64, b.height as f64), p.scale_factor);
    if !points.0.is_finite()
        || !points.1.is_finite()
        || points.0 <= 0.0
        || points.1 <= 0.0
        || points.0 > 16384.0
        || points.1 > 16384.0
    {
        return Err("Preview point size exceeds display limits".into());
    }
    let mut pixels = vec![0; length];
    b.write_premultiplied_rgba8(stride, &mut pixels)
        .map_err(|e| format!("Unsupported bitmap: {e:?}"))?;
    let regions = regions_in_point_space(&p.selectable_regions, p.scale_factor);
    if regions.len() > 16384 {
        return Err("Too many selectable regions".into());
    }
    let mut output = Vec::new();
    output.extend_from_slice(b"XCPV\x01\0\0\0");
    for n in [width, height, length, regions.len()] {
        output.extend_from_slice(
            &u32::try_from(n)
                .map_err(|_| "Display size overflow")?
                .to_le_bytes(),
        );
    }
    output.extend_from_slice(&p.scale_factor.to_le_bytes());
    output.extend_from_slice(&p.snapshot_corner_radius.to_le_bytes());
    for region in regions {
        if region.path.len() > 1024 * 1024 {
            return Err("Region path exceeds display limit".into());
        }
        output.extend_from_slice(&(region.path.len() as u32).to_le_bytes());
        output.extend_from_slice(
            &u32::try_from(
                region
                    .serialized_accessibility_element
                    .as_ref()
                    .map_or(0, Vec::len),
            )
            .map_err(|_| "Accessibility data exceeds display limit")?
            .to_le_bytes(),
        );
        for n in [
            region.rect.x,
            region.rect.y,
            region.rect.width,
            region.rect.height,
        ] {
            output.extend_from_slice(&n.to_le_bytes());
        }
        output.extend_from_slice(region.path.as_bytes());
        if output.len() > 4 * 1024 * 1024 {
            return Err("Region metadata exceeds display limit".into());
        }
    }
    output.extend_from_slice(&pixels);
    Ok(output)
}
