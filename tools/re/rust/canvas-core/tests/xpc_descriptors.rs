use canvas_core::{
    settings_xpc::XpcValue::{self, *},
    xpc_wire::*,
};
use std::collections::BTreeMap;
fn payload(v: &XpcValue) -> &BTreeMap<std::string::String, XpcValue> {
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
    let Dictionary(payload) = &parts[1] else {
        panic!()
    };
    payload
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
fn native_attachment_corpus_when_supplied() {
    let Some(paths) = std::env::var_os("XCPREVIEW_NATIVE_FD_BODIES") else {
        return;
    };
    let paths = std::env::split_paths(&paths).collect::<Vec<_>>();
    assert_eq!(paths.len(), 2);
    let mut bodies = Vec::new();
    for p in paths {
        let b = std::fs::read(p).unwrap();
        let v = decode_body_with_descriptors(&b, 2).unwrap();
        assert_eq!(payload(&v)["zDescriptor"], DescriptorRef(0));
        assert_eq!(payload(&v)["aDescriptor"], DescriptorRef(1));
        let encoded = encode_body_with_descriptors(&v, 2).unwrap();
        assert_eq!(encoded.descriptor_order, vec![1, 0]);
        let tokens = ["z-resource", "a-resource"];
        assert_eq!(
            encoded.bind_resources(&tokens).unwrap(),
            vec![&tokens[1], &tokens[0]]
        );
        assert_eq!(
            rebind(
                &decode_body_with_descriptors(&encoded.body, 2).unwrap(),
                &encoded.descriptor_order
            ),
            v
        );
        assert_eq!(decode_body(&b), Err(Error::Tag(0xb000)));
        bodies.push(b);
    }
    assert_eq!(bodies[0], bodies[1]);
    println!("independent native FD corpus verified: 2; alias identity outside wire");
}
#[test]
fn explicit_opt_in_counts_and_limits() {
    let v = Array(vec![DescriptorRef(0), DescriptorRef(1)]);
    let e = encode_body_with_descriptors(&v, 2).unwrap();
    assert_eq!(encode_body(&v), Err(Error::Tag(0xb000)));
    assert_eq!(
        decode_body_with_descriptors(&e.body, 0),
        Err(Error::Descriptors)
    );
    assert_eq!(
        decode_body_with_descriptors(&e.body, 3),
        Err(Error::Descriptors)
    );
    assert_eq!(encode_body_with_descriptors(&v, 1), Err(Error::Descriptors));
    assert_eq!(
        decode_body_with_descriptors(&e.body, 1025),
        Err(Error::Limit)
    );
}
#[test]
fn canonical_order_requires_table_permutation() {
    let v = Dictionary(BTreeMap::from([
        ("z".into(), DescriptorRef(0)),
        ("a".into(), DescriptorRef(1)),
    ]));
    let e = encode_body_with_descriptors(&v, 2).unwrap();
    assert_eq!(e.descriptor_order, vec![1, 0]);
    let decoded = decode_body_with_descriptors(&e.body, 2).unwrap();
    assert_ne!(decoded, v);
    assert_eq!(rebind(&decoded, &e.descriptor_order), v);
}
#[test]
fn repeated_refs_are_plans_not_new_capabilities() {
    let v = Array(vec![DescriptorRef(0), DescriptorRef(0)]);
    let e = encode_body_with_descriptors(&v, 1).unwrap();
    assert_eq!(e.descriptor_order, vec![0, 0]);
    assert_eq!(
        rebind(
            &decode_body_with_descriptors(&e.body, 2).unwrap(),
            &e.descriptor_order
        ),
        v
    );
    let many = Array(vec![DescriptorRef(0); 1025]);
    assert_eq!(encode_body_with_descriptors(&many, 1), Err(Error::Limit));
}

#[test]
fn resource_binding_preserves_tokens_and_alias_plan() {
    let value = Dictionary(BTreeMap::from([
        ("z".into(), DescriptorRef(0)),
        ("a".into(), DescriptorRef(1)),
    ]));
    let encoded = encode_body_with_descriptors(&value, 2).unwrap();
    let resources = [vec![0, 1], vec![2, 3]];
    let bound = encoded.bind_resources(&resources).unwrap();
    assert!(std::ptr::eq(bound[0], &resources[1]));
    assert!(std::ptr::eq(bound[1], &resources[0]));
    let repeated =
        encode_body_with_descriptors(&Array(vec![DescriptorRef(0), DescriptorRef(0)]), 1).unwrap();
    let single = [vec![7]];
    let bound = repeated.bind_resources(&single).unwrap();
    assert!(std::ptr::eq(bound[0], bound[1]));
}
#[test]
fn resource_binding_rejects_incoherent_public_plans() {
    let mut encoded = encode_body_with_descriptors(&Array(vec![DescriptorRef(0)]), 1).unwrap();
    assert_eq!(encoded.bind_resources::<()>(&[]), Err(Error::Descriptors));
    encoded.descriptor_order.clear();
    assert_eq!(encoded.bind_resources(&[()]), Err(Error::Descriptors));
    encoded.descriptor_order = vec![0];
    encoded.body[0] ^= 1;
    assert_eq!(encoded.bind_resources(&[()]), Err(Error::Header));
    assert_eq!(encoded.bind_resources(&vec![(); 1025]), Err(Error::Limit));
}
