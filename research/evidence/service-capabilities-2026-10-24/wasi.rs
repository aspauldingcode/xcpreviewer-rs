use canvas_core::{
    binary_plist,
    payload_codec::Value as V,
    service_envelope::{
        CapabilitiesPayload as P, Error, ServiceContent as C, ServiceEnvelope as E, IDENTIFIER_KEY,
    },
};
use std::collections::BTreeMap;
fn envelope(payload: BTreeMap<String, V>) -> V {
    V::Dictionary(BTreeMap::from([
        ("messageType".into(), V::String("capabilities".into())),
        ("payload".into(), V::Dictionary(payload)),
    ]))
}

fn complete_foundation_boolean_profiles_and_outer_fallback() {
    let V::Array(rows) = binary_plist::decode(include_bytes!(
        "native.bplist"
    ))
    .unwrap() else {
        panic!()
    };
    assert_eq!(rows.len(), 15);
    for row in rows {
        let V::Dictionary(row) = row else { panic!() };
        let V::Dictionary(payload) = &row["payload"] else {
            panic!()
        };
        let V::Boolean(accepted) = row["accepted"] else {
            panic!()
        };
        let result = P::decode_dictionary(payload);
        assert_eq!(result.is_ok(), accepted, "{:?}", row["label"]);
        let expected = if accepted {
            let V::Boolean(value) = row["value"] else {
                panic!()
            };
            Some(P {
                is_running_in_xtp: value,
            })
        } else {
            None
        };
        assert_eq!(result.ok(), expected);
        let value = envelope(payload.clone());
        let decoded = E::decode(&value).unwrap();
        assert_eq!(decoded.identifier, None);
        assert_eq!(decoded.content, C::Capabilities(expected.clone()));
        let canonical = envelope(
            expected
                .as_ref()
                .map_or_else(BTreeMap::new, P::to_dictionary),
        );
        assert_eq!(decoded.to_value(), canonical);
        let bytes = canvas_core::binary_plist_writer::encode(&canonical).unwrap();
        assert_eq!(E::decode_binary(&bytes).unwrap(), decoded);
    }
}

fn capability_errors_are_suppressed_after_identifier_validation_only() {
    let mut fields = BTreeMap::from([
        (
            IDENTIFIER_KEY.into(),
            V::String("owned/capability/🙂".into()),
        ),
        ("extra".into(), V::Data(vec![1, 2, 3])),
    ]);
    let absent = E::decode(&envelope(fields.clone())).unwrap();
    assert_eq!(absent.identifier.as_deref(), Some("owned/capability/🙂"));
    assert_eq!(absent.content, C::Capabilities(None));
    assert_eq!(
        absent.to_value(),
        envelope(BTreeMap::from([(
            IDENTIFIER_KEY.into(),
            V::String("owned/capability/🙂".into())
        )]))
    );
    fields.insert("isRunningInXTP".into(), V::String("true".into()));
    assert_eq!(E::decode(&envelope(fields.clone())).unwrap(), absent);
    fields.insert(IDENTIFIER_KEY.into(), V::Integer(2));
    assert_eq!(
        E::decode(&envelope(fields)),
        Err(Error::Type(IDENTIFIER_KEY))
    );
    let mut root = BTreeMap::from([("messageType".into(), V::String("capabilities".into()))]);
    assert_eq!(
        E::decode(&V::Dictionary(root.clone())),
        Err(Error::Missing("payload"))
    );
    for value in [V::Null, V::Array(vec![]), V::Integer(0)] {
        root.insert("payload".into(), value);
        assert_eq!(
            E::decode(&V::Dictionary(root.clone())),
            Err(Error::Type("payload"))
        )
    }
}

fn absent_false_true_and_nonfinite_values_remain_distinct() {
    for expected in [
        None,
        Some(P {
            is_running_in_xtp: false,
        }),
        Some(P {
            is_running_in_xtp: true,
        }),
    ] {
        let value = E {
            identifier: Some("".into()),
            content: C::Capabilities(expected),
        };
        assert_eq!(E::decode(&value.to_value()).unwrap(), value)
    }
    for number in [f64::NAN, f64::INFINITY, f64::NEG_INFINITY, 0.5, 2.0, -1.0] {
        assert_eq!(
            P::decode_dictionary(&BTreeMap::from([(
                "isRunningInXTP".into(),
                V::Real(number)
            )])),
            Err(Error::Type("isRunningInXTP"))
        )
    }
    assert_eq!(
        P::decode_dictionary(&BTreeMap::from([("isRunningInXTP".into(), V::Real(-0.0))])),
        Ok(P {
            is_running_in_xtp: false
        })
    );
    assert_eq!(
        P::decode_dictionary(&BTreeMap::new()),
        Err(Error::Missing("isRunningInXTP"))
    );
    assert_eq!(
        P::decode_dictionary(&BTreeMap::from([("isRunningInXTP".into(), V::Null)])),
        Err(Error::Type("isRunningInXTP"))
    );
}

fn main(){complete_foundation_boolean_profiles_and_outer_fallback();capability_errors_are_suppressed_after_identifier_validation_only();absent_false_true_and_nonfinite_values_remain_distinct();println!("Fifteen Foundation Bool profiles, outer fallback boundary and absent/false/true capability states passed in WASI");}
