//! Portable copy stage recovered from IOSurfacePreviewViewable.snapshot.
//! Caller supplies an already readable, synchronized linear byte view. This
//! module performs no lookup, lock, ownership transfer or GPU synchronization.
use crate::payload_codec::BitmapDescription;
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct LinearSurfaceLayout {
    pub width: i64,
    pub height: i64,
    pub bytes_per_row: i64,
    pub bytes_per_element: i64,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Error {
    Dimensions,
    Stride,
    ElementSize,
    Extent,
    SourceLength,
}
/// Copy exactly stride*height bytes, including row padding, excluding allocation
/// tail. Bounds/errors are original portable policy, not native trap parity.
pub fn copy_linear_snapshot(
    layout: LinearSurfaceLayout,
    source: &[u8],
) -> Result<BitmapDescription, Error> {
    if layout.width <= 0 || layout.height <= 0 || layout.width > 16384 || layout.height > 16384 {
        return Err(Error::Dimensions);
    }
    if layout.bytes_per_element <= 0 {
        return Err(Error::ElementSize);
    }
    let bits = layout
        .bytes_per_element
        .checked_mul(8)
        .ok_or(Error::ElementSize)?;
    let active = layout
        .width
        .checked_mul(layout.bytes_per_element)
        .ok_or(Error::Stride)?;
    if layout.bytes_per_row < active {
        return Err(Error::Stride);
    }
    let extent = layout
        .bytes_per_row
        .checked_mul(layout.height)
        .and_then(|n| usize::try_from(n).ok())
        .ok_or(Error::Extent)?;
    if extent > 64 * 1024 * 1024 {
        return Err(Error::Extent);
    }
    let bytes = source.get(..extent).ok_or(Error::SourceLength)?;
    Ok(BitmapDescription {
        data: bytes.to_vec(),
        width: layout.width,
        height: layout.height,
        bytes_per_row: layout.bytes_per_row,
        bitmap_info: 0x2002,
        bits_per_component: 8,
        bits_per_pixel: bits,
        color_space: "kCGColorSpaceSRGB".into(),
    })
}
