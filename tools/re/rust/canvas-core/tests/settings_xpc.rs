use canvas_core::settings_xpc::{ArchivedSettings, Error, XpcValue::*};
use std::collections::BTreeMap;
#[test]
fn native_owned_envelopes_roundtrip_every_archive_byte() {
    let native = include!("fixtures/native-settings-xpc.rs");
    let flags = [vec![], vec![(0,true),(42,true)], vec![(0,true),(42,false)], vec![(0,true),(42,true),(65535,true)]];
    let slots = [vec![], vec![1,65535], vec![65535], vec![0,1,65535]];
    for (i, value) in native.iter().enumerate() {
        let decoded = ArchivedSettings::from_xpc(value).unwrap();
        assert_eq!(decoded.flags, flags[i].iter().copied().collect());
        assert_eq!(decoded.objects.keys().copied().collect::<Vec<_>>(), slots[i]);
        for bytes in decoded.objects.values() { assert!(bytes.starts_with(b"bplist17")); }
        assert_eq!(&decoded.to_xpc(), value); // includes all 447 native archive bytes
        assert_eq!(decoded.flag(99), None);
    }
    let decoded = ArchivedSettings::from_xpc(&native[3]).unwrap();
    assert_eq!(decoded.flag(0),Some(true));
    assert!(decoded.objects.contains_key(&0)); // independent namespaces
    assert_eq!(ArchivedSettings::from_xpc(&native[2]).unwrap().flag(42),Some(false));
}
#[test]
fn malformed_and_unsupported_shapes_fail_closed() {
    let native = include!("fixtures/native-settings-xpc.rs");
    assert_eq!(ArchivedSettings::from_xpc(&Array(vec![])),Err(Error::Envelope));
    for key in ["flags","objects"] {
        assert_eq!(ArchivedSettings::from_xpc(&Dictionary(BTreeMap::from([(key.into(),Bool(false))]))),Err(Error::Bucket));
    }
    let Dictionary(mut d) = native[1].clone() else { panic!() };
    let Some(Array(entries)) = d.get_mut("flags") else { panic!() };
    entries.push(entries[0].clone());
    assert_eq!(ArchivedSettings::from_xpc(&Dictionary(d)),Err(Error::DuplicateSlot));
    for tag in [Bool(true),UInt64(2),Int64(1),Int64(3)] {
        let Dictionary(mut d) = native[1].clone() else { panic!() };
        let Some(Array(entries)) = d.get_mut("objects") else { panic!() };
        let Array(parts) = &mut entries[0] else { panic!() };parts[2]=tag;
        assert_eq!(ArchivedSettings::from_xpc(&Dictionary(d)),Err(Error::UnsupportedObject));
    }
}
#[test]
fn archive_projection_owns_bytes_without_decoding_them() {
    let mut native = include!("fixtures/native-settings-xpc.rs");
    let saved = ArchivedSettings::from_xpc(&native[1]).unwrap();
    let Dictionary(d) = &mut native[1] else { panic!() };
    let Some(Array(entries)) = d.get_mut("objects") else { panic!() };
    let Array(parts) = &mut entries[0] else { panic!() };
    let Dictionary(obj) = &mut parts[1] else { panic!() };
    let Some(Data(bytes)) = obj.get_mut("root") else { panic!() };bytes[0]^=1;
    assert_ne!(saved.to_xpc(),native[1]);
    assert!(saved.objects[&1].starts_with(b"bplist17"));
}
