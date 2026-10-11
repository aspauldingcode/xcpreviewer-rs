//! Allocation-free owned frame contract; usable from no_std.
#![forbid(unsafe_code)]
pub const ALLOCATION: usize = 16384;
pub const MEMORY: u64 = 131072;
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct FrameSpec {
    pub width: u32,
    pub height: u32,
    pub stride: u32,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct FrameAbi {
    pub memory: u64,
    pub pointer: u64,
    pub capacity: u64,
    pub rendered: u64,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Alpha,
    Dimensions,
    Stride,
    Memory,
    Capacity,
    Span,
    Rendered,
    Length,
    Mismatch(usize),
    Revision,
}
impl FrameSpec {
    pub fn byte_count(self) -> Result<u64, Error> {
        if !(1..=64).contains(&self.width) || !(1..=64).contains(&self.height) {
            return Err(Error::Dimensions);
        }
        if self.stride < self.width * 4 || self.stride > 256 {
            return Err(Error::Stride);
        }
        Ok(u64::from(self.stride) * u64::from(self.height))
    }
}
pub fn validate(
    spec: FrameSpec,
    abi: FrameAbi,
    actual: &[u8],
    expected: &[u8],
) -> Result<(), Error> {
    let used = spec.byte_count()?;
    if abi.memory != MEMORY {
        return Err(Error::Memory);
    }
    if abi.capacity != ALLOCATION as u64 {
        return Err(Error::Capacity);
    }
    if abi
        .pointer
        .checked_add(abi.capacity)
        .filter(|end| *end <= abi.memory)
        .is_none()
    {
        return Err(Error::Span);
    }
    if abi.rendered != used {
        return Err(Error::Rendered);
    }
    if actual.len() != ALLOCATION || expected.len() != ALLOCATION {
        return Err(Error::Length);
    }
    // Compare the complete allocation, including row padding and unused tail.
    if let Some(offset) = actual.iter().zip(expected).position(|(a, b)| a != b) {
        return Err(Error::Mismatch(offset));
    }
    Ok(())
}
/// Render only the independently measured three-primary, alpha-eighth contract.
/// Writes the whole allocation; every invalid request leaves the input unchanged.
pub fn render_primary(
    spec: FrameSpec,
    alphas: [u8; 3],
    reverse: bool,
    output: &mut [u8],
) -> Result<usize, Error> {
    let used = spec.byte_count()? as usize;
    if alphas.iter().any(|a| *a > 8) {
        return Err(Error::Alpha);
    }
    if output.len() != ALLOCATION {
        return Err(Error::Length);
    }
    let mut pixel = [0u32; 4];
    let order = if reverse { [1, 0, 2] } else { [2, 0, 1] };
    for channel in order {
        let alpha = (u32::from(alphas[channel]) * 255 + 4) / 8;
        for (c, value) in pixel.iter_mut().enumerate() {
            let source = if c == channel || c == 3 { alpha } else { 0 };
            *value = (source * 255 + *value * (255 - alpha) + 127) / 255;
        }
    }
    output.fill(0xc3);
    for row in output[..used].chunks_exact_mut(spec.stride as usize) {
        row.fill(0xa5);
        for target in row[..spec.width as usize * 4].chunks_exact_mut(4) {
            for (byte, value) in target.iter_mut().zip(pixel) {
                *byte = value as u8;
            }
        }
    }
    Ok(used)
}

