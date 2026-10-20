use canvas_core::{
    settings_xpc::XpcValue::{self, *},
    xpc_wire::*,
};
const BASE: [u64; 6] = [
    0x3ff8000000000000,
    0x8000000000000000,
    1,
    0x7ff0000000000000,
    0xfff0000000000000,
    0x7ff8000000001234,
];
const HOLDOUT: [u64; 6] = [
    0xc004000000000000,
    0,
    0x000fffffffffffff,
    0x7fefffffffffffff,
    0xffefffffffffffff,
    0xfff8000000005678,
];
fn payload(v: &XpcValue) -> &std::collections::BTreeMap<std::string::String, XpcValue> {
    let Dictionary(root) = v else { panic!() };
    let Dictionary(auto) = &root["bsx_auto"] else {
        panic!()
    };
    let Dictionary(info) = &auto["_info"] else {
        panic!()
    };
    let Array(entries) = &info["objects"] else {
        panic!()
    };
    let Array(parts) = &entries[0] else { panic!() };
    let Dictionary(p) = &parts[1] else { panic!() };
    p
}
fn rebind(v: &XpcValue, order: &[u32]) -> XpcValue {
    match v {
        DescriptorRef(i) => DescriptorRef(order[*i as usize]),
        Dictionary(d) => Dictionary(
            d.iter()
                .map(|(k, v)| (k.clone(), rebind(v, order)))
                .collect(),
        ),
        Array(a) => Array(a.iter().map(|v| rebind(v, order)).collect()),
        v => v.clone(),
    }
}
#[test]
fn independent_native_scalar_corpus_when_supplied() {
    let Some(paths) = std::env::var_os("XCPREVIEW_NATIVE_SCALAR_BODIES") else {
        return;
    };
    let paths = std::env::split_paths(&paths).collect::<Vec<_>>();
    assert_eq!(paths.len(), 3);
    let names = [
        "finiteDouble",
        "negativeZero",
        "subnormal",
        "positiveInfinity",
        "negativeInfinity",
        "quietNaN",
    ];
    let mut originals = Vec::new();
    for (i, path) in paths.iter().enumerate() {
        let bytes = std::fs::read(path).unwrap();
        let tree = decode_body_with_descriptors(&bytes, 2).unwrap();
        let values = payload(&tree);
        for (name, bits) in names.iter().zip(if i == 2 { HOLDOUT } else { BASE }) {
            assert_eq!(values[*name], DoubleBits(bits));
        }
        assert_eq!(values["nullValue"], Null);
        let encoded = encode_body_with_descriptors(&tree, 2).unwrap();
        assert_eq!(encoded.descriptor_order, vec![1, 0]);
        assert_eq!(
            rebind(
                &decode_body_with_descriptors(&encoded.body, 2).unwrap(),
                &encoded.descriptor_order
            ),
            tree
        );
        originals.push(bytes);
    }
    assert_eq!(originals[0], originals[1]);
    assert_ne!(originals[0], originals[2]);
    println!(
        "independent native scalar corpus verified: 3; twelve exact double bit patterns and null"
    );
}
#[test]
fn original_scalar_wire_fixtures_and_truncation() {
    let header = b"CPX@\x05\0\0\0";
    let null = [header.as_slice(), &[0, 0x10, 0, 0]].concat();
    assert_eq!(decode_body(&null), Ok(Null));
    assert_eq!(encode_body(&Null).unwrap(), null);
    for bits in BASE.into_iter().chain(HOLDOUT) {
        let bytes = [header.as_slice(), &[0, 0x50, 0, 0], &bits.to_le_bytes()].concat();
        assert_eq!(bytes.len(), 20);
        assert_eq!(decode_body(&bytes), Ok(DoubleBits(bits)));
        assert_eq!(encode_body(&DoubleBits(bits)).unwrap(), bytes);
        for end in 0..bytes.len() {
            assert!(decode_body(&bytes[..end]).is_err());
        }
        let mut extra = bytes;
        extra.push(0);
        assert_eq!(decode_body(&extra), Err(Error::Trailing));
    }
    for end in 0..null.len() {
        assert!(decode_body(&null[..end]).is_err());
    }
    let mut extra = null;
    extra.extend_from_slice(&[0; 8]);
    assert_eq!(decode_body(&extra), Err(Error::Trailing));
}
#[test]
fn bitwise_scalar_identity_preserves_zero_sign_and_nan_payload() {
    assert_ne!(DoubleBits(0), DoubleBits(0x8000000000000000));
    assert_ne!(
        DoubleBits(0x7ff8000000001234),
        DoubleBits(0x7ff8000000005678)
    );
    assert_ne!(
        DoubleBits(0x7ff8000000001234),
        DoubleBits(0xfff8000000001234)
    );
    assert_eq!(
        DoubleBits(0x7ff8000000001234),
        DoubleBits(0x7ff8000000001234)
    );
    assert_ne!(Null, Bool(false));
    assert_ne!(Null, Data(vec![]));
}
