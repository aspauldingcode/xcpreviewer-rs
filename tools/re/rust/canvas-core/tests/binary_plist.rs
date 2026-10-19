use canvas_core::binary_plist::{decode, decode_render_payload_binary, Error};
use canvas_core::payload_codec::Value;
const DEFAULT: &[u8] = include_bytes!("fixtures/payload-defaults.bplist");
const EXPLICIT: &[u8] = include_bytes!("fixtures/payload-explicit.bplist");
const UNICODE: &[u8] = include_bytes!("fixtures/unicode.bplist");
// Small binary fixtures constructed from explicit format bytes independently of
// the parser. The Python-produced fixtures exercise wide offsets and references.
fn plist(objects: &[&[u8]], top: u64) -> Vec<u8> {
    let mut b = b"bplist00".to_vec();
    let mut offsets = Vec::new();
    for object in objects {
        offsets.push(b.len() as u8);
        b.extend_from_slice(object);
    }
    let table = b.len() as u64;
    b.extend(offsets);
    b.extend([0u8; 6]);
    b.extend([1, 1]);
    b.extend((objects.len() as u64).to_be_bytes());
    b.extend(top.to_be_bytes());
    b.extend(table.to_be_bytes());
    b
}
#[test]
fn independent_payloads_keep_every_byte_and_native_defaults() {
    let p = decode_render_payload_binary(DEFAULT).unwrap();
    assert_eq!(
        p.bitmap_description.data,
        include_bytes!("fixtures/expected-bitmap.bin")
    );
    assert_eq!(
        (
            p.bitmap_description.width,
            p.bitmap_description.height,
            p.bitmap_description.bytes_per_row
        ),
        (3, 2, 40)
    );
    assert_eq!(
        (
            p.bitmap_description.bitmap_info,
            p.bitmap_description.bits_per_component,
            p.bitmap_description.bits_per_pixel
        ),
        (8194, 8, 32)
    );
    assert_eq!(p.bitmap_description.color_space, "kCGColorSpaceSRGB");
    assert_eq!((p.snapshot_corner_radius, p.scale_factor), (0.0, 3.0));
    assert_eq!(p.selectable_regions[0].path, "root/按钮/🧪");
    assert_eq!(p.selectable_regions[0].rect.x, -1.5);
    assert_eq!(
        p.selectable_regions[0].serialized_accessibility_element,
        Some(vec![0, 255, 0, 7])
    );
    let e = decode_render_payload_binary(EXPLICIT).unwrap();
    assert_eq!((e.snapshot_corner_radius, e.scale_factor), (6.5, 2.0));
    assert_eq!(e.bitmap_description.data, p.bitmap_description.data);
}
#[test]
fn independent_unicode_scalars_extended_lengths_and_data() {
    let Value::Dictionary(d) = decode(UNICODE).unwrap() else {
        panic!("dictionary required")
    };
    assert_eq!(
        d["text"],
        Value::String(format!("{}按钮🧪", "a".repeat(20)))
    );
    assert_eq!(d["positive"], Value::Integer(65535));
    assert_eq!(d["negative"], Value::Integer(-7));
    assert_eq!(d["false"], Value::Boolean(false));
    assert_eq!(d["true"], Value::Boolean(true));
    assert_eq!(d["null"], Value::Null);
    assert_eq!(d["float32-compatible"], Value::Real(1.25));
    assert_eq!(
        d["data"],
        Value::Data((0..512).map(|i| (i % 256) as u8).collect())
    );
    assert_eq!(
        decode(&plist(&[&[0x22, 0x3f, 0xa0, 0, 0]], 0)),
        Ok(Value::Real(1.25))
    );
}
#[test]
fn truncations_and_corrupt_trailers_fail_without_panics() {
    for end in 0..DEFAULT.len() {
        assert!(decode(&DEFAULT[..end]).is_err(), "prefix {end}");
    }
    for (back, value) in [(26, 0), (26, 9), (25, 0), (25, 9)] {
        let mut b = DEFAULT.to_vec();
        let pos = b.len() - back;
        b[pos] = value;
        assert!(decode(&b).is_err());
    }
    let mut b = DEFAULT.to_vec();
    b[0] = 0;
    assert_eq!(decode(&b), Err(Error::Header));
    for back in [24, 16, 8] {
        let mut b = DEFAULT.to_vec();
        let pos = b.len() - back;
        b[pos..pos + 8].fill(255);
        assert!(decode(&b).is_err());
    }
}
#[test]
fn cycles_bad_references_text_keys_and_unsupported_types_rejected() {
    assert_eq!(decode(&plist(&[&[0xa1, 0]], 0)), Err(Error::Cycle));
    assert_eq!(decode(&plist(&[&[0xa1, 1]], 0)), Err(Error::Bounds));
    assert_eq!(decode(&plist(&[&[0x61, 0xd8, 0]], 0)), Err(Error::Text));
    assert_eq!(decode(&plist(&[&[0x51, 0xff]], 0)), Err(Error::Text));
    assert_eq!(
        decode(&plist(&[&[0xd1, 1, 1], &[0]], 0)),
        Err(Error::DictionaryKey)
    );
    assert_eq!(
        decode(&plist(&[&[0xd2, 1, 1, 2, 2], &[0x51, b'a'], &[0]], 0)),
        Err(Error::DuplicateKey)
    );
    for marker in [0x33, 0x80, 0xc0, 0x14, 0xff] {
        assert_eq!(
            decode(&plist(&[&[marker]], 0)),
            Err(Error::Unsupported(marker))
        );
    }
    assert!(decode(&plist(
        &[&[0x4f, 0x13, 255, 255, 255, 255, 255, 255, 255, 255]],
        0
    ))
    .is_err());
}
#[test]
fn depth_and_expansion_limits_prevent_recursive_resource_exhaustion() {
    let mut objects = vec![vec![0xa1, 0]; 66];
    for (i, o) in objects.iter_mut().enumerate().take(65) {
        o[1] = (i + 1) as u8;
    }
    objects[65] = vec![0];
    assert_eq!(
        decode(&plist(
            &objects.iter().map(Vec::as_slice).collect::<Vec<_>>(),
            0
        )),
        Err(Error::Limit)
    );
    // A small acyclic DAG expands exponentially without a global node budget.
    let mut objects = vec![vec![0xa2, 0, 0]; 18];
    for (i, o) in objects.iter_mut().enumerate().take(17) {
        o[1] = (i + 1) as u8;
        o[2] = (i + 1) as u8;
    }
    objects[17] = vec![0];
    assert_eq!(
        decode(&plist(
            &objects.iter().map(Vec::as_slice).collect::<Vec<_>>(),
            0
        )),
        Err(Error::Limit)
    );
}
#[test]
fn finite_marker_mutations_never_panic() {
    for marker in 0..=255 {
        let b = plist(&[&[marker, 0, 0, 0, 0, 0, 0, 0, 0]], 0);
        let _ = decode(&b);
    }
}

#[test]
fn independent_wide_object_references() {
    let Value::Array(items) = decode(include_bytes!("fixtures/wide-references.bplist")).unwrap()
    else {
        panic!("array required")
    };
    assert_eq!(items.len(), 300);
    for (i, item) in items.iter().enumerate() {
        assert_eq!(*item, Value::String(format!("item-{i}")));
    }
}
