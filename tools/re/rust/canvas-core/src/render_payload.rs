//! Recovered outer render-payload fields for the pinned Xcode messaging image.
//!
//! The shipped decoder at 0x8d9a0 uses 0.0 for an absent corner radius and
//! 3.0 for an absent scale factor. This is a decoded-value adapter, not a
//! Swift ABI binding or a complete native property-list decoder. Bitmap and
//! selectable-region decoding remain the caller's responsibility.

#[derive(Clone, Debug, PartialEq)]
pub struct RenderPayload<Bitmap, Region> {
    pub bitmap_description: Bitmap,
    pub selectable_regions: Vec<Region>,
    pub snapshot_corner_radius: f64,
    pub scale_factor: f64,
}

impl<Bitmap, Region> RenderPayload<Bitmap, Region> {
    pub fn from_decoded_fields(
        bitmap_description: Bitmap,
        selectable_regions: Vec<Region>,
        snapshot_corner_radius: Option<f64>,
        scale_factor: Option<f64>,
    ) -> Self {
        Self {
            bitmap_description,
            selectable_regions,
            snapshot_corner_radius: snapshot_corner_radius.unwrap_or(0.0),
            scale_factor: scale_factor.unwrap_or(3.0),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::RenderPayload;

    #[test]
    fn absent_values_match_recovered_native_constants() {
        let payload = RenderPayload::from_decoded_fields(vec![1, 2, 3], vec![7], None, None);
        assert_eq!(payload.snapshot_corner_radius.to_bits(), 0x0000_0000_0000_0000);
        assert_eq!(payload.scale_factor.to_bits(), 0x4008_0000_0000_0000);
        assert_eq!(payload.bitmap_description, vec![1, 2, 3]);
        assert_eq!(payload.selectable_regions, vec![7]);
    }

    #[test]
    fn present_values_override_each_default_independently() {
        let corner = RenderPayload::<_, ()>::from_decoded_fields((), vec![], Some(-0.0), None);
        assert_eq!(corner.snapshot_corner_radius.to_bits(), (-0.0_f64).to_bits());
        assert_eq!(corner.scale_factor, 3.0);
        let scale = RenderPayload::<_, ()>::from_decoded_fields((), vec![], None, Some(2.0));
        assert_eq!(scale.snapshot_corner_radius, 0.0);
        assert_eq!(scale.scale_factor, 2.0);
    }
}
