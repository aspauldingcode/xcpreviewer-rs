use canvas_core::{
    binary_plist, binary_plist_writer as writer,
    cancel_update::CancelUpdatePayload as P,
    payload_codec::Value as V,
    service_envelope::{Error, ServiceContent as C, ServiceEnvelope as E, IDENTIFIER_KEY},
};
use std::collections::BTreeMap;

fn full_native_uint64_seed_controls() {
    let V::Array(rows) =
        binary_plist::decode(include_bytes!("native.bplist")).unwrap()
    else {
        panic!()
    };
    assert_eq!(rows.len(), 10);
    for (i, row) in rows.iter().enumerate() {
        let V::Dictionary(row) = row else { panic!() };
        let V::Dictionary(input) = &row["input"] else {
            panic!()
        };
        let V::Boolean(accepted) = row["accepted"] else {
            panic!()
        };
        let result = P::decode_dictionary(input);
        assert_eq!(result.is_ok(), accepted, "case {i}");
        if let Ok(payload) = result {
            let canonical = V::Dictionary(payload.to_dictionary());
            assert_eq!(canonical, row["canonical"]);
            assert_eq!(
                binary_plist::decode(&writer::encode(&canonical).unwrap()).unwrap(),
                canonical
            );
        }
    }
}

fn outer_cancel_identity_is_not_scene_seed_or_completion() {
    for seed in [0, i64::MAX as u64, i64::MAX as u64 + 1, u64::MAX] {
        let payload = P {
            pid: -1,
            content_identifier: "".into(),
            update_seed: seed,
        };
        let envelope = E {
            identifier: Some("owned/request".into()),
            content: C::CancelUpdate(payload.clone()),
        };
        let value = envelope.to_value();
        assert_eq!(E::decode(&value).unwrap(), envelope);
        assert_eq!(
            E::decode_binary(&writer::encode(&value).unwrap()).unwrap(),
            envelope
        );
        let V::Dictionary(mut root) = value else {
            panic!()
        };
        let V::Dictionary(fields) = root.get_mut("payload").unwrap() else {
            panic!()
        };
        fields.insert("extra".into(), V::Boolean(true));
        fields.insert(IDENTIFIER_KEY.into(), V::Integer(4));
        assert_eq!(
            E::decode(&V::Dictionary(root)),
            Err(Error::Type(IDENTIFIER_KEY))
        );
    }
    let base = P {
        pid: 42,
        content_identifier: "content".into(),
        update_seed: 1,
    }
    .to_dictionary();
    for key in ["pid", "contentIdentifier", "updateSeed"] {
        let mut fields = base.clone();
        fields.remove(key);
        assert!(P::decode_dictionary(&fields).is_err())
    }
    let mut fields = base;
    fields.insert("contentIdentifier".into(), V::Integer(4));
    assert!(P::decode_dictionary(&fields).is_err());
}

fn unsigned_plist_boundaries_and_budgets() {
    for n in [i64::MAX as u64 + 1, u64::MAX] {
        let value = V::Unsigned(n);
        let bytes = writer::encode(&value).unwrap();
        assert_eq!(bytes[8], 0x14);
        assert_eq!(bytes.len(), 58);
        assert_eq!(binary_plist::decode(&bytes).unwrap(), value);
        let mut limits = writer::Limits::default();
        limits.bytes = 57;
        assert!(writer::encode_with_limits(&value, limits).is_err());
        limits.bytes = 58;
        assert!(writer::encode_with_limits(&value, limits).is_ok());
        let mut invalid = bytes.clone();
        invalid[9] = 1;
        assert!(binary_plist::decode(&invalid).is_err());
        invalid[9] = 255;
        assert!(binary_plist::decode(&invalid).is_err());
    }
    assert_eq!(
        binary_plist::decode(&writer::encode(&V::Unsigned(1)).unwrap()).unwrap(),
        V::Integer(1)
    );
    assert_eq!(
        binary_plist::decode(&writer::encode(&V::Integer(-1)).unwrap()).unwrap(),
        V::Integer(-1)
    );
}

fn main(){full_native_uint64_seed_controls();outer_cancel_identity_is_not_scene_seed_or_completion();unsigned_plist_boundaries_and_budgets();
let V::Array(rows)=binary_plist::decode(include_bytes!("native.bplist")).unwrap() else {panic!()};
for row in rows {let V::Dictionary(row)=row else {panic!()};if let Some(value)=row.get("canonical") {let bytes=writer::encode(value).unwrap();println!("encoded:{}",bytes.iter().map(|b|format!("{b:02x}")).collect::<String>());}}
println!("UInt64/cancel-update controls and bounds passed in WASI");}
