use canvas_core::{
    binary_plist,
    payload_codec::Value as V,
    purge::{Error, PurgePayload as P},
    service_envelope::{
        CapabilitiesPayload, Error as OuterError, ServiceContent as C, ServiceEnvelope as E,
        IDENTIFIER_KEY,
    },
};
use std::collections::BTreeMap;
#[test]
fn complete_native_purge_dictionary_controls() {
    let V::Array(rows) =
        binary_plist::decode(include_bytes!("fixtures/purge/native.bplist")).unwrap()
    else {
        panic!()
    };
    assert_eq!(rows.len(), 11);
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
                binary_plist::decode(
                    &canvas_core::binary_plist_writer::encode(&canonical).unwrap()
                )
                .unwrap(),
                canonical
            )
        }
    }
}
#[test]
fn missing_flag_is_false_but_invalid_present_flag_rejects() {
    let fields = BTreeMap::from([("workspaceID".into(), V::String("".into()))]);
    let payload = P::decode_dictionary(&fields).unwrap();
    assert!(!payload.kill_agents);
    assert_eq!(
        payload.to_dictionary().get("killAgents"),
        Some(&V::Boolean(false))
    );
    for value in [
        V::Null,
        V::Integer(2),
        V::String("false".into()),
        V::Unsigned(u64::MAX),
        V::Real(f64::NAN),
    ] {
        let mut fields = fields.clone();
        fields.insert("killAgents".into(), value);
        assert_eq!(
            P::decode_dictionary(&fields),
            Err(Error::Type("killAgents"))
        )
    }
    assert_eq!(
        P::decode_dictionary(&BTreeMap::new()),
        Err(Error::Missing("workspaceID"))
    );
    for value in [V::Null, V::Integer(1)] {
        assert_eq!(
            P::decode_dictionary(&BTreeMap::from([("workspaceID".into(), value)])),
            Err(Error::Type("workspaceID"))
        )
    }
    for value in [V::Unsigned(0), V::Unsigned(1)] {
        let mut fields = fields.clone();
        fields.insert("killAgents".into(), value.clone());
        let purge = P::decode_dictionary(&fields).unwrap();
        let capability = CapabilitiesPayload::decode_dictionary(&BTreeMap::from([(
            "isRunningInXTP".into(),
            value,
        )]))
        .unwrap();
        assert_eq!(purge.kill_agents, capability.is_running_in_xtp)
    }
}
#[test]
fn outer_purge_routes_values_without_settlement() {
    for flag in [false, true] {
        let value = E {
            identifier: Some("owned/purge/🙂".into()),
            content: C::Purge(P {
                workspace_id: "owned/workspace".into(),
                kill_agents: flag,
            }),
        };
        assert_eq!(E::decode(&value.to_value()).unwrap(), value);
        let bytes = canvas_core::binary_plist_writer::encode(&value.to_value()).unwrap();
        assert_eq!(E::decode_binary(&bytes).unwrap(), value);
        let V::Dictionary(mut root) = value.to_value() else {
            panic!()
        };
        let V::Dictionary(payload) = root.get_mut("payload").unwrap() else {
            panic!()
        };
        payload.insert(IDENTIFIER_KEY.into(), V::Integer(1));
        assert_eq!(
            E::decode(&V::Dictionary(root)),
            Err(OuterError::Type(IDENTIFIER_KEY))
        );
    }
    let value = V::Dictionary(BTreeMap::from([
        ("messageType".into(), V::String("purge".into())),
        ("workspaceID".into(), V::String("wrong-root".into())),
        ("payload".into(), V::Dictionary(BTreeMap::new())),
    ]));
    assert_eq!(
        E::decode(&value),
        Err(OuterError::Purge(Error::Missing("workspaceID")))
    );
}
