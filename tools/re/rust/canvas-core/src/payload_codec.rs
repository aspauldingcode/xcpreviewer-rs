//! Typed property-list tree adapter recovered from PreviewsMessagingHost.
//!
//! This consumes decoded values. It does not parse binary/XML plists or reproduce
//! Foundation's numeric coercions. CGRect uses the recovered flat dictionary
//! keys x, y, width and height, represented here as explicit real values.
use crate::render_payload::RenderPayload;
use std::collections::BTreeMap;

#[derive(Clone, Debug, PartialEq)]
pub enum Value {
    Data(Vec<u8>),
    Integer(i64),
    Real(f64),
    String(String),
    Array(Vec<Value>),
    Dictionary(BTreeMap<String, Value>),
}
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Rect {
    pub x: f64,
    pub y: f64,
    pub width: f64,
    pub height: f64,
}
#[derive(Clone, Debug, PartialEq)]
pub struct SelectableRegion {
    pub path: String,
    pub rect: Rect,
    pub serialized_accessibility_element: Option<Vec<u8>>,
}
#[derive(Clone, Debug, PartialEq)]
pub struct BitmapDescription {
    pub data: Vec<u8>,
    pub width: i64,
    pub height: i64,
    pub bytes_per_row: i64,
    pub bitmap_info: u32,
    pub bits_per_component: i64,
    pub bits_per_pixel: i64,
    pub color_space: String,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum DecodeError {
    Missing(&'static str),
    Type(&'static str),
    Range(&'static str),
    UnknownByteOrder,
}

type Fields = BTreeMap<String, Value>;
fn dictionary<'a>(value: &'a Value, key: &'static str) -> Result<&'a Fields, DecodeError> {
    match value {
        Value::Dictionary(v) => Ok(v),
        _ => Err(DecodeError::Type(key)),
    }
}
fn required<'a>(fields: &'a Fields, key: &'static str) -> Result<&'a Value, DecodeError> {
    fields.get(key).ok_or(DecodeError::Missing(key))
}
fn integer(value: &Value, key: &'static str) -> Result<i64, DecodeError> {
    match value {
        Value::Integer(v) => Ok(*v),
        _ => Err(DecodeError::Type(key)),
    }
}
fn string(value: &Value, key: &'static str) -> Result<String, DecodeError> {
    match value {
        Value::String(v) => Ok(v.clone()),
        _ => Err(DecodeError::Type(key)),
    }
}
fn data(value: &Value, key: &'static str) -> Result<Vec<u8>, DecodeError> {
    match value {
        Value::Data(v) => Ok(v.clone()),
        _ => Err(DecodeError::Type(key)),
    }
}
fn optional_real(fields: &Fields, key: &'static str) -> Result<Option<f64>, DecodeError> {
    fields
        .get(key)
        .map(|v| match v {
            Value::Real(x) => Ok(*x),
            _ => Err(DecodeError::Type(key)),
        })
        .transpose()
}
impl BitmapDescription {
    pub fn decode(value: &Value) -> Result<Self, DecodeError> {
        let f = dictionary(value, "bitmapDescription")?;
        // Native decoding tries bitmapInfo first. Legacy byteOrder is consumed
        // only when bitmapInfo is absent, even if a byteOrder field is present.
        let bitmap_info = match f.get("bitmapInfo") {
            Some(v) => u32::try_from(integer(v, "bitmapInfo")?)
                .map_err(|_| DecodeError::Range("bitmapInfo"))?,
            None => match string(required(f, "byteOrder")?, "byteOrder")?.as_str() {
                "little" => 0x2002,
                "big" => 0x4002,
                _ => return Err(DecodeError::UnknownByteOrder),
            },
        };
        let bits_per_component = f
            .get("bitsPerComponent")
            .map(|v| integer(v, "bitsPerComponent"))
            .transpose()?
            .unwrap_or(8);
        let bits_per_pixel = f
            .get("bitsPerPixel")
            .map(|v| integer(v, "bitsPerPixel"))
            .transpose()?
            .unwrap_or(32);
        let color_space = f
            .get("colorSpace")
            .map(|v| string(v, "colorSpace"))
            .transpose()?
            .unwrap_or_else(|| "kCGColorSpaceSRGB".into());
        Ok(Self {
            data: data(required(f, "data")?, "data")?,
            width: integer(required(f, "width")?, "width")?,
            height: integer(required(f, "height")?, "height")?,
            bytes_per_row: integer(required(f, "bytesPerRow")?, "bytesPerRow")?,
            bitmap_info,
            bits_per_component,
            bits_per_pixel,
            color_space,
        })
    }
}
impl Rect {
    pub fn decode(value: &Value) -> Result<Self, DecodeError> {
        let f = dictionary(value, "rect")?;
        fn coordinate(f: &Fields, key: &'static str) -> Result<f64, DecodeError> {
            match required(f, key)? {
                Value::Real(v) => Ok(*v),
                _ => Err(DecodeError::Type(key)),
            }
        }
        Ok(Self {
            x: coordinate(f, "x")?,
            y: coordinate(f, "y")?,
            width: coordinate(f, "width")?,
            height: coordinate(f, "height")?,
        })
    }
}
impl SelectableRegion {
    pub fn decode(value: &Value) -> Result<Self, DecodeError> {
        let f = dictionary(value, "selectableRegion")?;
        let path = string(required(f, "path")?, "path")?;
        let rect = Rect::decode(required(f, "rect")?)?;
        let serialized_accessibility_element = f
            .get("serializedAccessibilityElement")
            .map(|v| data(v, "serializedAccessibilityElement"))
            .transpose()?;
        Ok(Self {
            path,
            rect,
            serialized_accessibility_element,
        })
    }
}
pub fn decode_render_payload(
    value: &Value,
) -> Result<RenderPayload<BitmapDescription, SelectableRegion>, DecodeError> {
    let f = dictionary(value, "renderPayload")?;
    let bitmap = BitmapDescription::decode(required(f, "bitmapDescription")?)?;
    let regions = match required(f, "selectableRegions")? {
        Value::Array(a) => a
            .iter()
            .map(SelectableRegion::decode)
            .collect::<Result<Vec<_>, _>>()?,
        _ => return Err(DecodeError::Type("selectableRegions")),
    };
    Ok(RenderPayload::from_decoded_fields(
        bitmap,
        regions,
        optional_real(f, "snapshotCornerRadius")?,
        optional_real(f, "scaleFactor")?,
    ))
}

#[cfg(test)]
mod tests {
    use super::*;
    fn bitmap_fields() -> Fields {
        BTreeMap::from([
            (
                "data".into(),
                Value::Data(vec![0, 1, 2, 255, 91, 92, 93, 94]),
            ),
            ("width".into(), Value::Integer(1)),
            ("height".into(), Value::Integer(1)),
            ("bytesPerRow".into(), Value::Integer(8)),
            ("byteOrder".into(), Value::String("little".into())),
        ])
    }
    #[test]
    fn legacy_defaults_and_all_data_bytes() {
        let b = BitmapDescription::decode(&Value::Dictionary(bitmap_fields())).unwrap();
        assert_eq!(
            (b.bitmap_info, b.bits_per_component, b.bits_per_pixel),
            (0x2002, 8, 32)
        );
        assert_eq!(b.color_space, "kCGColorSpaceSRGB");
        assert_eq!(b.data, vec![0, 1, 2, 255, 91, 92, 93, 94]);
    }
    #[test]
    fn big_endian_and_explicit_format_fields() {
        let mut f = bitmap_fields();
        f.insert("byteOrder".into(), Value::String("big".into()));
        f.insert("bitsPerPixel".into(), Value::Integer(64));
        let b = BitmapDescription::decode(&Value::Dictionary(f)).unwrap();
        assert_eq!(b.bitmap_info, 0x4002);
        assert_eq!(b.bits_per_pixel, 64);
    }
    #[test]
    fn explicit_bitmap_info_bypasses_even_malformed_legacy_order() {
        let mut f = bitmap_fields();
        f.insert("bitmapInfo".into(), Value::Integer(0));
        f.insert("byteOrder".into(), Value::Data(vec![255]));
        assert_eq!(
            BitmapDescription::decode(&Value::Dictionary(f))
                .unwrap()
                .bitmap_info,
            0
        );
    }
    #[test]
    fn missing_order_and_invalid_uint32_are_errors() {
        let mut f = bitmap_fields();
        f.remove("byteOrder");
        assert_eq!(
            BitmapDescription::decode(&Value::Dictionary(f.clone())),
            Err(DecodeError::Missing("byteOrder"))
        );
        for v in [-1, 4294967296] {
            f.insert("bitmapInfo".into(), Value::Integer(v));
            assert_eq!(
                BitmapDescription::decode(&Value::Dictionary(f.clone())),
                Err(DecodeError::Range("bitmapInfo"))
            );
        }
    }
    #[test]
    fn region_preserves_geometry_unicode_and_optional_accessibility_bytes() {
        let rect = Rect {
            x: -1.5,
            y: 2.0,
            width: 3.0,
            height: 4.0,
        };
        let f = BTreeMap::from([
            ("path".into(), Value::String("root/按钮".into())),
            (
                "rect".into(),
                Value::Dictionary(BTreeMap::from([
                    ("x".into(), Value::Real(rect.x)),
                    ("y".into(), Value::Real(rect.y)),
                    ("width".into(), Value::Real(rect.width)),
                    ("height".into(), Value::Real(rect.height)),
                ])),
            ),
            (
                "serializedAccessibilityElement".into(),
                Value::Data(vec![0, 255, 0]),
            ),
        ]);
        let r = SelectableRegion::decode(&Value::Dictionary(f)).unwrap();
        assert_eq!(r.path, "root/按钮");
        assert_eq!(r.rect, rect);
        assert_eq!(r.serialized_accessibility_element, Some(vec![0, 255, 0]));
    }
    #[test]
    fn rect_requires_flat_coordinates_and_rejects_missing_height() {
        let mut f = BTreeMap::from([
            ("x".into(), Value::Real(1.0)),
            ("y".into(), Value::Real(2.0)),
            ("width".into(), Value::Real(3.0)),
            ("height".into(), Value::Real(4.0)),
        ]);
        assert_eq!(
            Rect::decode(&Value::Dictionary(f.clone())).unwrap(),
            Rect {
                x: 1.0,
                y: 2.0,
                width: 3.0,
                height: 4.0
            }
        );
        f.remove("height");
        assert_eq!(
            Rect::decode(&Value::Dictionary(f)),
            Err(DecodeError::Missing("height"))
        );
    }
    #[test]
    fn complete_outer_tree_uses_native_defaults_and_required_region_array() {
        let mut f = BTreeMap::from([
            (
                "bitmapDescription".into(),
                Value::Dictionary(bitmap_fields()),
            ),
            ("selectableRegions".into(), Value::Array(vec![])),
        ]);
        let r = decode_render_payload(&Value::Dictionary(f.clone())).unwrap();
        assert_eq!((r.snapshot_corner_radius, r.scale_factor), (0.0, 3.0));
        f.remove("selectableRegions");
        assert_eq!(
            decode_render_payload(&Value::Dictionary(f)),
            Err(DecodeError::Missing("selectableRegions"))
        );
    }
}
