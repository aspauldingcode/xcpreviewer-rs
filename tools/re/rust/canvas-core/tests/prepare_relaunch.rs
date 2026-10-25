use canvas_core::{
    agent_descriptor::{AgentBundle, AgentDescriptor},
    binary_plist, binary_plist_writer,
    payload_codec::Value,
    prepare_relaunch::PrepareToRelaunchPayload,
    service_envelope::{Error, ServiceContent, ServiceEnvelope},
};
use std::{
    collections::BTreeMap,
    io::Write,
    process::{Command, Stdio},
};
fn dict(fields: Vec<(&str, Value)>) -> Value {
    Value::Dictionary(fields.into_iter().map(|(k, v)| (k.into(), v)).collect())
}
fn controls() -> Vec<Value> {
    let Value::Array(rows) =
        binary_plist::decode(include_bytes!("fixtures/prepare_relaunch/native.bplist")).unwrap()
    else {
        panic!()
    };
    rows
}
#[test]
fn complete_public_foundation_compositions_match_value_and_envelope_routes() {
    let rows = controls();
    assert_eq!(rows.len(), 17);
    let mut accepted = 0;
    for row in rows {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let Value::Dictionary(input) = &row["input"] else {
            panic!()
        };
        let decoded = PrepareToRelaunchPayload::decode_dictionary(input);
        if row["accepted"] == Value::Boolean(true) {
            accepted += 1;
            let payload = decoded.unwrap();
            assert_eq!(
                Value::Dictionary(payload.to_dictionary()),
                row["output"],
                "{:?}",
                row["name"]
            );
            let original = dict(vec![
                ("messageType", Value::String("prepareToRelaunch".into())),
                ("payload", row["input"].clone()),
            ]);
            let envelope = ServiceEnvelope::decode(&original).unwrap();
            assert_eq!(envelope.content, ServiceContent::PrepareToRelaunch(payload));
            let canonical = envelope.to_value();
            assert_eq!(
                ServiceEnvelope::decode_binary(&binary_plist_writer::encode(&canonical).unwrap())
                    .unwrap(),
                envelope
            );
        } else {
            assert!(decoded.is_err(), "{:?}", row["name"]);
        }
    }
    assert_eq!(accepted, 12);
}
#[test]
fn errors_and_identifier_namespace_remain_separate_from_legacy_fallback() {
    let fields = BTreeMap::new();
    assert_eq!(
        PrepareToRelaunchPayload::decode_dictionary(&fields),
        Err(canvas_core::agent_descriptor::Error::Missing(
            "agentIdentifier"
        ))
    );
    let bundle = AgentBundle {
        bundle_id: "opaque".into(),
        path: Some(String::new()),
    };
    assert_eq!(AgentBundle::decode(&bundle.to_value()).unwrap(), bundle);
    let descriptor = AgentDescriptor {
        id_across_relaunches: "id".into(),
        bundle,
    };
    assert_eq!(
        AgentDescriptor::decode(&descriptor.to_value()).unwrap(),
        descriptor
    );
    let payload = PrepareToRelaunchPayload {
        agent_descriptor: descriptor,
    };
    let mut fields = payload.to_dictionary();
    fields.insert(
        "__unique_service_message_identifier".into(),
        Value::Integer(1),
    );
    assert_eq!(
        ServiceEnvelope::decode(&dict(vec![
            ("messageType", Value::String("prepareToRelaunch".into())),
            ("payload", Value::Dictionary(fields.clone()))
        ])),
        Err(Error::Type("__unique_service_message_identifier"))
    );
    fields.insert(
        "__unique_service_message_identifier".into(),
        Value::String(String::new()),
    );
    let message = ServiceEnvelope::decode(&dict(vec![
        ("messageType", Value::String("prepareToRelaunch".into())),
        ("payload", Value::Dictionary(fields)),
    ]))
    .unwrap();
    assert_eq!(message.identifier, Some(String::new()));
}
#[test]
fn inspector_handles_preparation_value_without_agent_execution() {
    let rows = controls();
    let Value::Dictionary(row) = &rows[0] else {
        panic!()
    };
    let input = dict(vec![
        ("messageType", Value::String("prepareToRelaunch".into())),
        ("payload", row["input"].clone()),
    ]);
    for canonical in [false, true] {
        let mut c = Command::new(env!("CARGO_BIN_EXE_inspect-service-message"));
        if canonical {
            c.arg("--canonical");
        }
        c.arg("-");
        let mut child = c
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .unwrap();
        child
            .stdin
            .take()
            .unwrap()
            .write_all(&binary_plist_writer::encode(&input).unwrap())
            .unwrap();
        let output = child.wait_with_output().unwrap();
        assert!(output.status.success());
        assert!(output.stderr.is_empty());
        if canonical {
            assert_eq!(
                ServiceEnvelope::decode_binary(&output.stdout)
                    .unwrap()
                    .to_value(),
                ServiceEnvelope::decode(&input).unwrap().to_value()
            );
        } else {
            let summary = String::from_utf8(output.stdout).unwrap();
            assert!(summary.starts_with("messageType=prepareToRelaunch\n"));
            assert!(summary.contains("bundleID=\"owned.bundle\""));
            assert!(!summary.contains('\0'));
        }
    }
}
