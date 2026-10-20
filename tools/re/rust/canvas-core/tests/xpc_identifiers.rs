use canvas_core::{
    settings_xpc::XpcValue::{self, *},
    xpc_wire::*,
};
const PRIMARY: [u8; 16] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 255];
const HOLDOUT: [u8; 16] = [
    255, 254, 253, 252, 251, 250, 249, 248, 247, 246, 245, 244, 243, 242, 241, 240,
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
fn independent_native_identifier_corpus_when_supplied() {
    let Some(paths) = std::env::var_os("XCPREVIEW_NATIVE_IDENTIFIER_BODIES") else {
        return;
    };
    let paths = std::env::split_paths(&paths).collect::<Vec<_>>();
    assert_eq!(paths.len(), 3);
    let mut originals = Vec::new();
    for (i, p) in paths.iter().enumerate() {
        let bytes = std::fs::read(p).unwrap();
        let tree = decode_body_with_descriptors(&bytes, 2).unwrap();
        let values = payload(&tree);
        assert_eq!(
            values["identifier"],
            Uuid(if i == 2 { HOLDOUT } else { PRIMARY })
        );
        assert_eq!(
            values["timestamp"],
            DateNanos(if i == 2 { i64::MAX } else { -123456789 })
        );
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
    println!("independent native UUID/date corpus verified: 3");
}
#[test]
fn original_uuid_wire_fixtures_preserve_all_bytes() {
    for bytes in [PRIMARY, HOLDOUT] {
        let wire = [b"CPX@\x05\0\0\0".as_slice(), &[0, 0xa0, 0, 0], &bytes].concat();
        assert_eq!(wire.len(), 28);
        assert_eq!(decode_body(&wire), Ok(Uuid(bytes)));
        assert_eq!(encode_body(&Uuid(bytes)).unwrap(), wire);
        for end in 0..wire.len() {
            assert!(decode_body(&wire[..end]).is_err());
        }
        let mut extra = wire;
        extra.push(0);
        assert_eq!(decode_body(&extra), Err(Error::Trailing));
    }
    assert_ne!(Uuid(PRIMARY), Data(PRIMARY.to_vec()));
}
#[test]
fn original_date_wire_fixtures_preserve_signed_payload() {
    for nanos in [-123456789, i64::MAX] {
        let wire = [
            b"CPX@\x05\0\0\0".as_slice(),
            &[0, 0x70, 0, 0],
            &nanos.to_le_bytes(),
        ]
        .concat();
        assert_eq!(wire.len(), 20);
        assert_eq!(decode_body(&wire), Ok(DateNanos(nanos)));
        assert_eq!(encode_body(&DateNanos(nanos)).unwrap(), wire);
        for end in 0..wire.len() {
            assert!(decode_body(&wire[..end]).is_err());
        }
        let mut extra = wire;
        extra.extend_from_slice(&[0; 4]);
        assert_eq!(decode_body(&extra), Err(Error::Trailing));
        assert_ne!(DateNanos(nanos), Int64(nanos));
    }
}
