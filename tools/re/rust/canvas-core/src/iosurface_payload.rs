//! Source-guided IOSurface payload value codec and receiver geometry projection.
//! Numeric surface ID is data, not a frame revision, readiness or ownership proof.
use crate::{
    binary_plist,
    payload_codec::{DecodeError, SelectableRegion, Value},
    preview_geometry,
};
use std::collections::BTreeMap;
#[derive(Clone, Debug, PartialEq)]
pub struct IOSurfacePayload {
    pub surface_id: u32,
    pub scale_factor: f64,
    pub width: f64,
    pub height: f64,
    pub selectable_regions: Vec<SelectableRegion>,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Plist(binary_plist::Error),
    Field(DecodeError),
}
fn missing(k: &'static str) -> Error {
    Error::Field(DecodeError::Missing(k))
}
fn bad(k: &'static str) -> Error {
    Error::Field(DecodeError::Type(k))
}
impl IOSurfacePayload {
    pub fn decode(v: &Value) -> Result<Self, Error> {
        let Value::Dictionary(d) = v else {
            return Err(bad("iosurfacePayload"));
        };
        let surface_id = match d.get("surfaceID").ok_or_else(|| missing("surfaceID"))? {
            Value::Integer(n) => {
                u32::try_from(*n).map_err(|_| Error::Field(DecodeError::Range("surfaceID")))?
            }
            _ => return Err(bad("surfaceID")),
        };
        let real = |k: &'static str| -> Result<f64, Error> {
            match d.get(k).ok_or_else(|| missing(k))? {
                Value::Real(v) => Ok(*v),
                _ => Err(bad(k)),
            }
        };
        let scale_factor = real("scaleFactor")?;
        let width = real("width")?;
        let height = real("height")?;
        let selectable_regions = match d
            .get("selectableRegions")
            .ok_or_else(|| missing("selectableRegions"))?
        {
            Value::Array(a) => a
                .iter()
                .map(SelectableRegion::decode)
                .collect::<Result<Vec<_>, _>>()
                .map_err(Error::Field)?,
            _ => return Err(bad("selectableRegions")),
        };
        Ok(Self {
            surface_id,
            scale_factor,
            width,
            height,
            selectable_regions,
        })
    }
    pub fn decode_binary(bytes: &[u8]) -> Result<Self, Error> {
        Self::decode(&binary_plist::decode(bytes).map_err(Error::Plist)?)
    }
    /// The recovered receiver multiplies point-sized payload dimensions by scale.
    /// It does not rescale region rectangles when wrapping them for PreviewGeometry.
    pub fn size_in_pixels(&self) -> (f64, f64) {
        (
            self.width * self.scale_factor,
            self.height * self.scale_factor,
        )
    }
    pub fn regions_in_point_space(&self) -> Vec<SelectableRegion> {
        preview_geometry::regions_in_point_space(&self.selectable_regions, self.scale_factor)
    }
    pub fn to_value(&self) -> Value {
        let regions = self
            .selectable_regions
            .iter()
            .map(|r| {
                let mut d = BTreeMap::from([
                    ("path".into(), Value::String(r.path.clone())),
                    (
                        "rect".into(),
                        Value::Dictionary(BTreeMap::from([
                            ("x".into(), Value::Real(r.rect.x)),
                            ("y".into(), Value::Real(r.rect.y)),
                            ("width".into(), Value::Real(r.rect.width)),
                            ("height".into(), Value::Real(r.rect.height)),
                        ])),
                    ),
                ]);
                if let Some(b) = &r.serialized_accessibility_element {
                    d.insert(
                        "serializedAccessibilityElement".into(),
                        Value::Data(b.clone()),
                    );
                }
                Value::Dictionary(d)
            })
            .collect();
        Value::Dictionary(BTreeMap::from([
            (
                "surfaceID".into(),
                Value::Integer(i64::from(self.surface_id)),
            ),
            ("scaleFactor".into(), Value::Real(self.scale_factor)),
            ("width".into(), Value::Real(self.width)),
            ("height".into(), Value::Real(self.height)),
            ("selectableRegions".into(), Value::Array(regions)),
        ]))
    }
}
