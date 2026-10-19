use canvas_core::payload_codec::{Rect, SelectableRegion};
use canvas_core::preview_geometry::{regions_in_point_space, size_in_points};
include!("fixtures/geometry_cases.rs");
fn rect(bits: [u64; 4]) -> Rect {
    Rect {
        x: f64::from_bits(bits[0]),
        y: f64::from_bits(bits[1]),
        width: f64::from_bits(bits[2]),
        height: f64::from_bits(bits[3]),
    }
}
fn values(r: Rect) -> [f64; 4] {
    [r.x, r.y, r.width, r.height]
}
fn check(actual: f64, bits: u64) {
    let expected = f64::from_bits(bits);
    if expected.is_nan() {
        assert!(actual.is_nan());
    } else {
        assert_eq!(
            actual.to_bits(),
            bits,
            "actual {actual:?}, expected {expected:?}"
        );
    }
}
#[test]
fn scaled_regions_and_point_coordinates_match_native_corpus() {
    assert_eq!(NATIVE.len(), 180);
    for (input, factor, scaled, point, size) in NATIVE {
        let r = rect(*input);
        let scale = f64::from_bits(*factor);
        for (a, b) in values(r.scaled_by(scale)).iter().zip(scaled) {
            check(*a, *b);
        }
        let region = SelectableRegion {
            path: "root/按钮/🧪".into(),
            rect: r,
            serialized_accessibility_element: Some(vec![0, 255, 7, 0]),
        };
        let converted = regions_in_point_space(&[region.clone()], scale);
        for (a, b) in values(converted[0].rect).iter().zip(point) {
            check(*a, *b);
        }
        let s = size_in_points((r.width, r.height), scale);
        check(s.0, size[0]);
        check(s.1, size[1]);
        assert_eq!(converted[0].path, region.path);
        assert_eq!(
            converted[0].serialized_accessibility_element,
            region.serialized_accessibility_element
        );
    }
}
#[test]
fn division_and_reciprocal_multiplication_are_distinct() {
    let r = SelectableRegion {
        path: "a".into(),
        rect: Rect {
            x: 1.0,
            y: 2.0,
            width: 7.0,
            height: 11.0,
        },
        serialized_accessibility_element: None,
    };
    let p = regions_in_point_space(&[r], 3.0);
    let s = size_in_points((7.0, 11.0), 3.0);
    assert_ne!(p[0].rect.width.to_bits(), s.0.to_bits());
    assert_eq!(p[0].rect.width.to_bits(), (7.0_f64 * (1.0 / 3.0)).to_bits());
    assert_eq!(s.0.to_bits(), (7.0_f64 / 3.0).to_bits());
}
#[test]
fn region_mapping_preserves_order_metadata_and_inputs() {
    let first = SelectableRegion {
        path: "first".into(),
        rect: Rect {
            x: 10.0,
            y: 20.0,
            width: -4.0,
            height: -8.0,
        },
        serialized_accessibility_element: Some(vec![1, 0, 255]),
    };
    let second = SelectableRegion {
        path: "second".into(),
        rect: Rect {
            x: 30.0,
            y: 40.0,
            width: 1.0,
            height: 2.0,
        },
        serialized_accessibility_element: None,
    };
    let original = vec![first, second];
    let mapped = regions_in_point_space(&original, 2.0);
    assert_eq!(
        mapped.iter().map(|r| r.path.as_str()).collect::<Vec<_>>(),
        vec!["first", "second"]
    );
    assert_eq!(
        mapped[0].rect,
        Rect {
            x: 5.0,
            y: 10.0,
            width: 2.0,
            height: 4.0
        }
    );
    assert_eq!(original[0].rect.width, -4.0);
    assert_eq!(
        mapped[0].serialized_accessibility_element,
        Some(vec![1, 0, 255])
    );
    assert!(regions_in_point_space(&[], 0.0).is_empty());
}

#[test]
fn decoded_binary_payload_connects_to_point_space_api() {
    let p = canvas_core::binary_plist::decode_render_payload_binary(include_bytes!(
        "fixtures/payload-defaults.bplist"
    ))
    .unwrap();
    let regions = regions_in_point_space(&p.selectable_regions, p.scale_factor);
    assert_eq!(regions[0].path, "root/按钮/🧪");
    assert_eq!(regions[0].rect.x, -0.5);
    assert_eq!(regions[0].rect.y, 2.0 * (1.0 / 3.0));
    assert_eq!(
        regions[0].serialized_accessibility_element,
        Some(vec![0, 255, 0, 7])
    );
    assert_eq!(
        size_in_points(
            (
                p.bitmap_description.width as f64,
                p.bitmap_description.height as f64
            ),
            p.scale_factor
        ),
        (1.0, 2.0 / 3.0)
    );
}
