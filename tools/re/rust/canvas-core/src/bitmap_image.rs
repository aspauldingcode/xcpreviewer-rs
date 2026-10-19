//! Portable import of the independently checked 8/32-bit premultiplied sRGB
//! bitmap subset. Output bytes are premultiplied RGBA, not straight-alpha RGBA.
//! This is pixel import, not color management, view rendering or Canvas capture.
use crate::payload_codec::BitmapDescription;
const MAX_BYTES: usize = 64 * 1024 * 1024;
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Dimensions,
    Stride,
    Length,
    Limit,
    UnsupportedFormat,
    UnsupportedColorSpace,
    InvalidPremultiplication,
}
impl BitmapDescription {
    /// Convert active pixels only. Destination padding/tail remain unchanged.
    /// All validation precedes writes, preserving the entire destination on error.
    pub fn write_premultiplied_rgba8(
        &self,
        output_stride: usize,
        output: &mut [u8],
    ) -> Result<usize, Error> {
        if self.bits_per_component != 8 || self.bits_per_pixel != 32 {
            return Err(Error::UnsupportedFormat);
        }
        if self.color_space != "kCGColorSpaceSRGB" {
            return Err(Error::UnsupportedColorSpace);
        }
        // Source byte positions for canonical R, G, B, A. Explicit 32-bit byte
        // orders only; host-dependent default and additional flags stay unsupported.
        let order = match self.bitmap_info {
            0x2002 => [2, 1, 0, 3], // premultiplied first, little: BGRA
            0x4002 => [1, 2, 3, 0], // premultiplied first, big: ARGB
            0x2001 => [3, 2, 1, 0], // premultiplied last, little: ABGR
            0x4001 => [0, 1, 2, 3], // premultiplied last, big: RGBA
            _ => return Err(Error::UnsupportedFormat),
        };
        let width = usize::try_from(self.width).map_err(|_| Error::Dimensions)?;
        let height = usize::try_from(self.height).map_err(|_| Error::Dimensions)?;
        if width == 0 || height == 0 || width > 16384 || height > 16384 {
            return Err(Error::Dimensions);
        }
        let active = width.checked_mul(4).ok_or(Error::Dimensions)?;
        if self.bytes_per_row > MAX_BYTES as i64 {
            return Err(Error::Limit);
        }
        let source_stride = usize::try_from(self.bytes_per_row).map_err(|_| Error::Stride)?;
        if source_stride < active || output_stride < active {
            return Err(Error::Stride);
        }
        let source_used = source_stride.checked_mul(height).ok_or(Error::Limit)?;
        let output_used = output_stride.checked_mul(height).ok_or(Error::Limit)?;
        if source_used > MAX_BYTES || output_used > MAX_BYTES {
            return Err(Error::Limit);
        }
        if self.data.len() < source_used || output.len() < output_used {
            return Err(Error::Length);
        }
        for row in self.data[..source_used].chunks_exact(source_stride) {
            for pixel in row[..active].chunks_exact(4) {
                if order[..3].iter().any(|i| pixel[*i] > pixel[order[3]]) {
                    return Err(Error::InvalidPremultiplication);
                }
            }
        }
        for (source, target) in self.data[..source_used]
            .chunks_exact(source_stride)
            .zip(output[..output_used].chunks_exact_mut(output_stride))
        {
            for (input, pixel) in source[..active]
                .chunks_exact(4)
                .zip(target[..active].chunks_exact_mut(4))
            {
                for (channel, index) in order.iter().enumerate() {
                    pixel[channel] = input[*index];
                }
            }
        }
        Ok(output_used)
    }
}
