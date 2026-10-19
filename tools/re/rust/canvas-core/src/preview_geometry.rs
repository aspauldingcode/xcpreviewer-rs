//! Coordinate operations recovered from PreviewsMessagingHost/PreviewsPipeline.
//! These preserve IEEE floating behavior rather than introducing UI validation.
//! They do not implement selection dispatch, address/model-path parsing or hits.
use crate::payload_codec::{Rect, SelectableRegion};
impl Rect {
    /// Match the recovered scaledBy sequence: preserve null/infinite sentinels,
    /// multiply origin, and scale CGRectGetWidth/GetHeight (absolute extents).
    /// This differs from scaling raw signed extents or applying an affine transform.
    pub fn scaled_by(&self, factor: f64) -> Self {
        let null = self.x == f64::INFINITY || self.y == f64::INFINITY;
        // The measured 64-bit CGRectInfinite sentinel is finite. IEEE infinite
        // width/height alone do not identify this sentinel.
        let infinite = self.x.to_bits() == 0xffdfffffffffffff
            && self.y.to_bits() == 0xffdfffffffffffff
            && self.width.to_bits() == 0x7fefffffffffffff
            && self.height.to_bits() == 0x7fefffffffffffff;
        if null || infinite {
            return *self;
        }
        Self {
            x: self.x * factor,
            y: self.y * factor,
            width: self.width.abs() * factor,
            height: self.height.abs() * factor,
        }
    }
}
impl SelectableRegion {
    /// Preserve the path and serialized accessibility bytes when scaling a region.
    pub fn scaled_by(&self, factor: f64) -> Self {
        Self {
            path: self.path.clone(),
            rect: self.rect.scaled_by(factor),
            serialized_accessibility_element: self.serialized_accessibility_element.clone(),
        }
    }
}
/// Match PreviewGeometry's region getter: map regions by the reciprocal scale.
/// List order and metadata are preserved; no zero/nonfinite scale guard is added.
pub fn regions_in_point_space(
    regions: &[SelectableRegion],
    scale_factor: f64,
) -> Vec<SelectableRegion> {
    let reciprocal = 1.0 / scale_factor;
    regions.iter().map(|r| r.scaled_by(reciprocal)).collect()
}
/// Match PreviewGeometry's size getter with direct division of each raw dimension.
/// Do not substitute reciprocal multiplication: rounding and signed extents differ.
pub fn size_in_points(size_in_pixels: (f64, f64), scale_factor: f64) -> (f64, f64) {
    (
        size_in_pixels.0 / scale_factor,
        size_in_pixels.1 / scale_factor,
    )
}
