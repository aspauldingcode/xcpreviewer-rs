use canvas_core::{
    binary_plist,
    payload_codec::Value as V,
    service_envelope::{
        Error, ForwardServiceEnvelope as F, ServiceContent as C, ServiceEnvelope as E,
        IDENTIFIER_KEY,
    },
};
use std::collections::BTreeMap;
fn map(fields: &[(&str, V)]) -> V {
    V::Dictionary(
        fields
            .iter()
            .map(|(k, v)| (k.to_string(), v.clone()))
            .collect(),
    )
}
#[test]
fn complete_foundation_ping_envelopes_and_canonical_output() {
    let V::Array(rows) =
        binary_plist::decode(include_bytes!("fixtures/service-ping/native.bplist")).unwrap()
    else {
        panic!()
    };
    assert_eq!(rows.len(), 4);
    for (i, row) in rows.iter().enumerate() {
        let envelope = E::decode(row).unwrap();
        assert_eq!(envelope.content, C::Ping);
        assert_eq!(
            envelope.identifier.as_deref(),
            [None, Some("owned/ping/🙂"), Some(""), None][i]
        );
        let payload = envelope.identifier.as_ref().map_or(BTreeMap::new(), |s| {
            BTreeMap::from([(IDENTIFIER_KEY.into(), V::String(s.clone()))])
        });
        let canonical = map(&[
            ("messageType", V::String("ping".into())),
            ("payload", V::Dictionary(payload)),
        ]);
        assert_eq!(envelope.to_value(), canonical);
        let bytes = canvas_core::binary_plist_writer::encode(&canonical).unwrap();
        assert_eq!(E::decode_binary(&bytes).unwrap(), envelope);
        assert_eq!(F::decode(row), Err(Error::UnsupportedMessageType));
    }
}
#[test]
fn ping_requires_root_payload_and_typed_identifier() {
    let empty = V::Dictionary(BTreeMap::new());
    assert_eq!(E::decode(&V::Null), Err(Error::Type("serviceMessage")));
    assert_eq!(E::decode(&empty), Err(Error::Missing("messageType")));
    for kind in [V::Null, V::Integer(0)] {
        assert_eq!(
            E::decode(&map(&[("messageType", kind)])),
            Err(Error::Type("messageType"))
        )
    }
    for kind in ["Ping", "launch", "captureIOSurface", "unknown"] {
        assert_eq!(
            E::decode(&map(&[("messageType", V::String(kind.into()))])),
            Err(Error::UnsupportedMessageType)
        )
    }
    let ping = V::String("ping".into());
    assert_eq!(
        E::decode(&map(&[("messageType", ping.clone())])),
        Err(Error::Missing("payload"))
    );
    for payload in [V::Null, V::Array(vec![]), V::String("".into())] {
        assert_eq!(
            E::decode(&map(&[("messageType", ping.clone()), ("payload", payload)])),
            Err(Error::Type("payload"))
        )
    }
    for id in [V::Null, V::Integer(1), V::Boolean(false), V::Data(vec![])] {
        assert_eq!(
            E::decode(&map(&[
                ("messageType", ping.clone()),
                ("payload", map(&[(IDENTIFIER_KEY, id)]))
            ])),
            Err(Error::Type(IDENTIFIER_KEY))
        )
    }
}
#[test]
fn unified_forward_preserves_existing_wire_and_explicit_construction() {
    let bytes = include_bytes!("fixtures/service-envelope/forward.bplist");
    let previous = F::decode_binary(bytes).unwrap();
    let envelope = E::decode_binary(bytes).unwrap();
    assert_eq!(envelope.identifier, previous.identifier);
    assert_eq!(envelope.content, C::Forward(previous.forward.clone()));
    assert_eq!(envelope.to_value(), previous.to_value());
    let first = E::new(C::Ping);
    let second = E::new(C::Forward(previous.forward.clone()));
    assert!(first.identifier.as_ref().unwrap().parse::<u64>().is_ok());
    assert!(second.identifier.as_ref().unwrap().parse::<u64>().is_ok());
    assert_ne!(first.identifier, second.identifier);
    assert_eq!(E::decode(&first.to_value()).unwrap(), first);
    assert_eq!(E::decode(&second.to_value()).unwrap(), second);
    let V::Dictionary(mut invalid) = previous.to_value() else {
        panic!()
    };
    let V::Dictionary(payload) = invalid.get_mut("payload").unwrap() else {
        panic!()
    };
    payload.remove("pid");
    assert!(matches!(
        E::decode(&V::Dictionary(invalid)),
        Err(Error::Forward(_))
    ));
}
