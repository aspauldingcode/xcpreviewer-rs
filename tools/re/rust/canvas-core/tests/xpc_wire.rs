use canvas_core::{
    settings_xpc::XpcValue::{self, *},
    xpc_wire::{decode_body, encode_body, Error},
};
use std::collections::BTreeMap;
fn expected(holdout: bool) -> XpcValue {
    let mut payload = BTreeMap::from([
        ("flag".into(), Bool(true)),
        ("signed".into(), Int64(if holdout { i64::MIN } else { -7 })),
        (
            "unsigned".into(),
            UInt64(if holdout { 0 } else { u64::MAX }),
        ),
        (
            "text".into(),
            String(
                if holdout {
                    "owned-snow☃"
                } else {
                    "owned-typed"
                }
                .into(),
            ),
        ),
        ("bytes".into(), Data(vec![0, 255, 3])),
        ("list".into(), Array(vec![Bool(false)])),
    ]);
    if holdout {
        payload.insert("empty".into(), Dictionary(BTreeMap::new()));
    }
    let info = Dictionary(BTreeMap::from([
        ("bsx_class".into(), String("BSSettings".into())),
        (
            "objects".into(),
            Array(vec![Array(vec![UInt64(1), Dictionary(payload)])]),
        ),
    ]));
    Dictionary(BTreeMap::from([
        ("bsx_class".into(), String("BSActionResponse".into())),
        (
            "bsx_auto".into(),
            Dictionary(BTreeMap::from([("_info".into(), info)])),
        ),
    ]))
}
#[test]
fn frozen_native_owned_corpus_when_supplied() {
    let Some(paths) = std::env::var_os("XCPREVIEW_NATIVE_XPC_BODIES") else {
        return;
    };
    let paths = std::env::split_paths(&paths).collect::<Vec<_>>();
    assert_eq!(paths.len(), 2);
    for (i, path) in paths.iter().enumerate() {
        let bytes = std::fs::read(path).unwrap();
        let v = decode_body(&bytes).unwrap();
        assert_eq!(v, expected(i == 1));
        assert_eq!(decode_body(&encode_body(&v).unwrap()).unwrap(), v);
    }
    println!("independent native typed corpus verified: 2");
}
#[test]
fn original_exact_small_dictionary_fixture() {
    let v = Dictionary(BTreeMap::from([("k".into(), Bool(true))]));
    let bytes = vec![
        67, 80, 88, 64, 5, 0, 0, 0, 0, 240, 0, 0, 16, 0, 0, 0, 1, 0, 0, 0, 107, 0, 0, 0, 0, 32, 0,
        0, 1, 0, 0, 0,
    ];
    assert_eq!(encode_body(&v).unwrap(), bytes);
    assert_eq!(decode_body(&bytes).unwrap(), v);
}
#[test]
fn malformed_length_tag_version_and_padding_reject() {
    let bytes = encode_body(&Dictionary(BTreeMap::from([("k".into(), Bool(true))]))).unwrap();
    for (offset, value) in [(0, 0), (4, 4), (8, 1), (12, 255), (22, 1), (28, 2)] {
        let mut b = bytes.clone();
        b[offset] = value;
        assert!(decode_body(&b).is_err());
    }
    for n in 0..bytes.len() {
        assert!(decode_body(&bytes[..n]).is_err());
    }
    let mut b = bytes.clone();
    b.push(0);
    assert_eq!(decode_body(&b), Err(Error::Trailing));
    let mut b = encode_body(&Dictionary(BTreeMap::from([
        ("a".into(), Bool(true)),
        ("b".into(), Bool(false)),
    ])))
    .unwrap();
    b[32] = b'a';
    assert_eq!(decode_body(&b), Err(Error::DuplicateKey));
}
#[test]
fn strings_integer_extremes_data_and_empty_containers() {
    let v = Array(vec![
        Int64(i64::MIN),
        UInt64(u64::MAX),
        String("snow☃".into()),
        Data(vec![0, 255, 3]),
        Array(vec![]),
        Dictionary(BTreeMap::new()),
    ]);
    assert_eq!(decode_body(&encode_body(&v).unwrap()).unwrap(), v);
    assert_eq!(encode_body(&String("a\0b".into())), Err(Error::Text));
    let mut b = encode_body(&String("x".into())).unwrap();
    b[16] = 255;
    assert_eq!(decode_body(&b), Err(Error::Text));
}
#[test]
fn bounded_depth_and_unknown_attachment_tags() {
    let mut v = Bool(true);
    for _ in 0..66 {
        v = Array(vec![v]);
    }
    assert_eq!(encode_body(&v), Err(Error::Limit));
    let mut b = b"CPX@\x05\0\0\0".to_vec();
    b.extend_from_slice(&0x10000u32.to_le_bytes());
    assert_eq!(decode_body(&b), Err(Error::Tag(0x10000)));
}
