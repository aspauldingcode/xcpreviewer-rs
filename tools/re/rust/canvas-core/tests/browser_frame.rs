use canvas_core::{
    binary_plist::decode,
    binary_plist_writer::encode,
    browser_frame::frame_packet,
    payload_codec::{decode_render_payload, Value},
};
fn sample() -> Value {
    decode(include_bytes!("fixtures/browser_frame/sample.bplist")).unwrap()
}
fn u32_at(p: &[u8], i: usize) -> u32 {
    u32::from_le_bytes(p[i..i + 4].try_into().unwrap())
}
fn f64_at(p: &[u8], i: usize) -> f64 {
    f64::from_le_bytes(p[i..i + 8].try_into().unwrap())
}
#[test]
fn presentation_packet_preserves_pixels_and_qualified_point_geometry() {
    let mut source = sample();
    let Value::Dictionary(ref mut fields) = source else {
        panic!()
    };
    fields.insert("scaleFactor".into(), Value::Integer(2));
    let bytes = encode(&source).unwrap();
    let packet = frame_packet(&bytes).unwrap();
    assert_eq!(&packet[..8], b"XCPV\x01\0\0\0");
    assert_eq!((u32_at(&packet, 8), u32_at(&packet, 12)), (128, 96));
    assert_eq!(u32_at(&packet, 16), 128 * 96 * 4);
    assert_eq!(u32_at(&packet, 20), 2);
    assert_eq!(f64_at(&packet, 24), 2.0);
    assert_eq!(f64_at(&packet, 32), 6.0);
    assert_eq!(u32_at(&packet, 40), 9);
    assert_eq!(u32_at(&packet, 44), 21);
    assert_eq!(
        [
            f64_at(&packet, 48),
            f64_at(&packet, 56),
            f64_at(&packet, 64),
            f64_at(&packet, 72)
        ],
        [6.0, 8.0, 29.0, 25.0]
    );
    assert_eq!(&packet[80..89], b"Blue card");
    let Value::Dictionary(native) =
        decode(include_bytes!("fixtures/browser_frame/native.bplist")).unwrap()
    else {
        panic!()
    };
    let Value::Array(rows) = &native["rows"] else {
        panic!()
    };
    let Value::Dictionary(row) = &rows[0] else {
        panic!()
    };
    assert_eq!(row["accepted"], Value::Boolean(true));
    let native = decode_render_payload(&row["canonical"]).unwrap();
    let data = native.bitmap_description.data;
    let expected: Vec<u8> = data
        .chunks_exact(4)
        .flat_map(|p| [p[2], p[1], p[0], p[3]])
        .collect();
    assert_eq!(&packet[packet.len() - expected.len()..], expected);
}
#[test]
fn presentation_limits_do_not_change_native_payload_acceptance() {
    for (field, value) in [
        ("scaleFactor", Value::Integer(0)),
        ("scaleFactor", Value::Real(1e-320)),
        ("snapshotCornerRadius", Value::Integer(-1)),
    ] {
        let mut source = sample();
        let Value::Dictionary(ref mut f) = source else {
            panic!()
        };
        f.insert(field.into(), value);
        assert!(decode_render_payload(&source).is_ok());
        assert!(frame_packet(&encode(&source).unwrap()).is_err());
    }
    assert!(frame_packet(b"owned invalid preview").is_err());
}
