use canvas_core::{
    iosurface_payload::{Error, IOSurfacePayload as P},
    iosurface_snapshot::{copy_linear_snapshot, LinearSurfaceLayout},
    payload_codec::{DecodeError, Value},
};
fn value() -> Value {
    canvas_core::binary_plist::decode(include_bytes!("fixtures/iosurface-payload/payload.bplist"))
        .unwrap()
}
#[test]
fn complete_independent_fixture_and_receiver_projection() {
    let v = value();
    let p = P::decode_binary(include_bytes!("fixtures/iosurface-payload/payload.bplist")).unwrap();
    assert_eq!(p.to_value(), v);
    assert_eq!(p.surface_id, 12345);
    assert_eq!(p.size_in_pixels(), (3.0, 2.0));
    assert_eq!(p.selectable_regions[0].rect.x, 1.0);
    let point = p.regions_in_point_space();
    assert_eq!(point[0].rect.x, 0.5);
    assert_eq!(point[0].rect.width, 1.0);
    assert_eq!(point[0].path, "root/🪨");
    assert_eq!(
        point[0].serialized_accessibility_element,
        Some(vec![0, 255])
    );
}
#[test]
fn all_fields_required_without_render_payload_defaults() {
    for key in [
        "surfaceID",
        "scaleFactor",
        "width",
        "height",
        "selectableRegions",
    ] {
        let mut v = value();
        let Value::Dictionary(ref mut d) = v else {
            panic!()
        };
        d.remove(key);
        assert_eq!(P::decode(&v), Err(Error::Field(DecodeError::Missing(key))));
    }
    for n in [-1, u32::MAX as i64 + 1] {
        let mut v = value();
        let Value::Dictionary(ref mut d) = v else {
            panic!()
        };
        d.insert("surfaceID".into(), Value::Integer(n));
        assert_eq!(
            P::decode(&v),
            Err(Error::Field(DecodeError::Range("surfaceID")))
        );
    }
    for n in [0, u32::MAX] {
        let mut v = value();
        let Value::Dictionary(ref mut d) = v else {
            panic!()
        };
        d.insert("surfaceID".into(), Value::Integer(i64::from(n)));
        assert_eq!(P::decode(&v).unwrap().surface_id, n);
    }
}
#[test]
fn strict_types_and_ieee_geometry_preserve_inputs() {
    for key in ["scaleFactor", "width", "height"] {
        let mut v = value();
        let Value::Dictionary(ref mut d) = v else {
            panic!()
        };
        d.insert(key.into(), Value::Integer(1));
        assert_eq!(P::decode(&v), Err(Error::Field(DecodeError::Type(key))));
    }
    let mut p = P::decode(&value()).unwrap();
    p.scale_factor = -0.0;
    assert_eq!(p.size_in_pixels().0.to_bits(), (-0.0f64).to_bits());
    p.scale_factor = f64::INFINITY;
    assert!(p.size_in_pixels().0.is_infinite());
    let v = value();
    let before = v.clone();
    P::decode(&v).unwrap();
    assert_eq!(v, before);
}
#[test]
fn resource_id_does_not_deduplicate_changed_copied_contents() {
    let p = P::decode(&value()).unwrap();
    let id = p.surface_id;
    let layout = LinearSurfaceLayout {
        width: 3,
        height: 2,
        bytes_per_row: 64,
        bytes_per_element: 4,
    };
    let first = copy_linear_snapshot(
        layout,
        include_bytes!("fixtures/iosurface-payload/generation1.bin"),
    )
    .unwrap();
    let second = copy_linear_snapshot(
        layout,
        include_bytes!("fixtures/iosurface-payload/generation2.bin"),
    )
    .unwrap();
    assert_eq!(p.surface_id, id);
    assert_ne!(first.data, second.data);
    assert_eq!(
        first.data.as_slice(),
        include_bytes!("fixtures/iosurface-payload/generation1.bin")
    );
    assert_eq!(second.data, [0x19; 128]);
}
