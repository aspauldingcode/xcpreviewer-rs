// Replay actual native render decoding; this is not view rendering or color management.
use canvas_core::{
    binary_plist,
    payload_codec::{decode_render_payload, Value},
};
use std::collections::BTreeMap;
fn dict(value: &Value) -> &BTreeMap<String, Value> {
    let Value::Dictionary(f) = value else {
        panic!("dictionary")
    };
    f
}
fn integer(value: &Value) -> i64 {
    let Value::Integer(v) = value else {
        panic!("native integer")
    };
    *v
}
fn string(value: &Value) -> &str {
    let Value::String(v) = value else {
        panic!("native string")
    };
    v
}
fn data(value: &Value) -> &[u8] {
    let Value::Data(v) = value else {
        panic!("native data")
    };
    v
}
fn real(actual: f64, expected: &Value) {
    let Value::Real(expected) = expected else {
        panic!("native real")
    };
    if expected.is_nan() {
        assert!(actual.is_nan())
    } else if *expected == 0.0 {
        assert_eq!(actual, 0.0)
    } else {
        assert_eq!(actual.to_bits(), expected.to_bits())
    }
    // Fixture serializers may coalesce signed zero and NaN payloads. No bit-fidelity claim for those cases.
}
fn main() {
    let native = binary_plist::decode(include_bytes!(
        "../tests/fixtures/native_render/native.bplist"
    ))
    .unwrap();
    let native = dict(&native);
    let Value::Array(rows) = &native["rows"] else {
        panic!()
    };
    assert_eq!(rows.len(), 465);
    let (mut accepted, mut rejected, mut rendered) = (0, 0, 0);
    for row in rows {
        let row = dict(row);
        let name = string(&row["case"]);
        let result = decode_render_payload(&row["input"]);
        assert_eq!(
            result.is_ok(),
            row["accepted"] == Value::Boolean(true),
            "{name}: {result:?}"
        );
        if let Ok(actual) = result {
            accepted += 1;
            let expected = dict(&row["canonical"]);
            let bitmap = dict(&expected["bitmapDescription"]);
            let b = &actual.bitmap_description;
            assert_eq!(b.data, data(&bitmap["data"]), "{name}");
            assert_eq!(b.width, integer(&bitmap["width"]), "{name}");
            assert_eq!(b.height, integer(&bitmap["height"]), "{name}");
            assert_eq!(b.bytes_per_row, integer(&bitmap["bytesPerRow"]), "{name}");
            assert_eq!(
                u64::from(b.bitmap_info),
                integer(&bitmap["bitmapInfo"]) as u64,
                "{name}"
            );
            assert_eq!(
                b.bits_per_component,
                integer(&bitmap["bitsPerComponent"]),
                "{name}"
            );
            assert_eq!(b.bits_per_pixel, integer(&bitmap["bitsPerPixel"]), "{name}");
            assert_eq!(b.color_space, string(&bitmap["colorSpace"]), "{name}");
            real(actual.scale_factor, &expected["scaleFactor"]);
            real(
                actual.snapshot_corner_radius,
                &expected["snapshotCornerRadius"],
            );
            let Value::Array(regions) = &expected["selectableRegions"] else {
                panic!()
            };
            assert_eq!(regions.len(), actual.selectable_regions.len());
            for (region, native) in actual.selectable_regions.iter().zip(regions) {
                let native = dict(native);
                assert_eq!(region.path, string(&native["path"]));
                let rect = dict(&native["rect"]);
                for (value, key) in [
                    (region.rect.x, "x"),
                    (region.rect.y, "y"),
                    (region.rect.width, "width"),
                    (region.rect.height, "height"),
                ] {
                    real(value, &rect[key]);
                }
                assert_eq!(
                    region.serialized_accessibility_element.as_deref(),
                    native.get("serializedAccessibilityElement").map(data)
                );
            }
            if name.starts_with("usable/") {
                let stride = b.width as usize * 4;
                let mut pixels = vec![0; b.height as usize * stride];
                assert_eq!(
                    b.write_premultiplied_rgba8(stride, &mut pixels).unwrap(),
                    pixels.len()
                );
                let expected: Vec<u8> = if b.width == 1 {
                    vec![255, 0, 0, 255]
                } else {
                    vec![
                        255, 0, 0, 255, 0, 255, 0, 255, 0, 0, 255, 255, 255, 255, 255, 255,
                    ]
                };
                assert_eq!(pixels, expected);
                rendered += 1;
            }
        } else {
            rejected += 1;
        }
    }
    assert_eq!((accepted, rejected, rendered), (298, 167, 3));
    println!("native render cases={} accepted={accepted} rejected={rejected} exact_pixel_controls={rendered}",rows.len());
}
