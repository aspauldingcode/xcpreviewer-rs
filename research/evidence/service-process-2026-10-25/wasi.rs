use canvas_core::{
    binary_plist,
    payload_codec::Value as V,
    service_envelope::{ServiceContent as C, ServiceEnvelope as E, IDENTIFIER_KEY},
    service_process::{Error, ProcessTarget as P},
};
use std::collections::BTreeMap;

fn complete_public_foundation_process_controls() {
    let V::Array(rows) =
        binary_plist::decode(include_bytes!("native.bplist")).unwrap()
    else {
        panic!()
    };
    assert_eq!(rows.len(), 21);
    for (i, row) in rows.iter().enumerate() {
        let V::Dictionary(row) = row else { panic!() };
        let V::Boolean(accepted) = row["accepted"] else {
            panic!()
        };
        let result = P::decode(&row["input"]);
        assert_eq!(result.is_ok(), accepted, "case {i}");
        if let Ok(target) = result {
            assert_eq!(target.to_value(), row["canonical"], "case {i}");
            assert_eq!(P::decode(&target.to_value()).unwrap(), target);
            let bytes = canvas_core::binary_plist_writer::encode(&target.to_value()).unwrap();
            assert_eq!(
                P::decode(&binary_plist::decode(&bytes).unwrap()).unwrap(),
                target
            )
        }
    }
}

fn process_control_envelopes_preserve_target_and_identifier() {
    let targets = [
        P::Pid(-1),
        P::Pid(12345),
        P::AuditToken([0, 1, 2, 3, 4, 12345, 6, 7]),
    ];
    for target in targets {
        for kind in ["connect", "stop", "kill"] {
            let mut payload = target.to_dictionary();
            payload.insert(IDENTIFIER_KEY.into(), V::String("owned/process/🙂".into()));
            payload.insert("ignored".into(), V::Data(vec![1, 2]));
            let value = V::Dictionary(BTreeMap::from([
                ("messageType".into(), V::String(kind.into())),
                ("payload".into(), V::Dictionary(payload)),
            ]));
            let envelope = E::decode(&value).unwrap();
            assert_eq!(envelope.identifier.as_deref(), Some("owned/process/🙂"));
            let expected = match kind {
                "connect" => C::Connect(target.clone()),
                "stop" => C::Stop(target.clone()),
                _ => C::Kill(target.clone()),
            };
            assert_eq!(envelope.content, expected);
            assert_eq!(E::decode(&envelope.to_value()).unwrap(), envelope);
        }
    }
}

fn fallback_is_pid_only_and_token_words_are_not_authority() {
    let token = P::AuditToken([0, 0, 0, 0, 0, 0x80000000, 0, 0]);
    assert_eq!(token.pid(), i32::MIN);
    assert_eq!(P::decode(&token.to_value()).unwrap(), token);
    let mut fields = token.to_dictionary();
    fields.insert("discriminant".into(), V::String("unknown".into()));
    fields.insert("pid".into(), V::Integer(22));
    assert_eq!(P::decode_dictionary(&fields), Ok(P::Pid(22)));
    fields.remove("pid");
    assert_eq!(P::decode_dictionary(&fields), Err(Error::Missing("pid")));
    fields.insert("discriminant".into(), V::String("auditToken".into()));
    fields.insert(
        "auditToken".into(),
        V::Dictionary(BTreeMap::from([(
            "val".into(),
            V::Array(vec![V::Integer(0); 9]),
        )])),
    );
    assert_eq!(P::decode_dictionary(&fields), Err(Error::Missing("pid")));
    for value in [
        V::Null,
        V::Real(f64::NAN),
        V::Real(f64::INFINITY),
        V::Integer(i64::MAX),
    ] {
        fields.insert("pid".into(), value);
        assert!(P::decode_dictionary(&fields).is_err())
    }
    assert_eq!(P::decode(&V::Null), Err(Error::Type("process")));
}

fn main(){complete_public_foundation_process_controls();process_control_envelopes_preserve_target_and_identifier();fallback_is_pid_only_and_token_words_are_not_authority();println!("21 public process-value controls, three outer routes and legacy fallback passed in WASI");}
