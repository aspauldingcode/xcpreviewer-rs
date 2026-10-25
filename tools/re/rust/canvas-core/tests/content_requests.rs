use canvas_core::{
    binary_plist, binary_plist_writer,
    content_requests::{Error, RequestContentOverridePayload, RequestPreviewVariantsPayload},
    payload_codec::Value,
    service_envelope::{ServiceContent, ServiceEnvelope},
};
use std::{
    collections::BTreeMap,
    io::Write,
    process::{Command, Stdio},
};
fn rows() -> Vec<Value> {
    let Value::Array(rows) =
        binary_plist::decode(include_bytes!("fixtures/content_requests/native.bplist")).unwrap()
    else {
        panic!()
    };
    rows
}
fn message(kind: &str, input: Value) -> Value {
    Value::Dictionary(BTreeMap::from([
        ("messageType".into(), Value::String(kind.into())),
        ("payload".into(), input),
    ]))
}
#[test]
fn complete_foundation_controls_match_both_request_shapes_and_canonical_routes() {
    let mut accepted = 0;
    let rows = rows();
    assert_eq!(rows.len(), 21);
    for row in rows {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let Value::String(kind) = &row["kind"] else {
            panic!()
        };
        let Value::Dictionary(input) = &row["input"] else {
            panic!()
        };
        let decoded = ServiceEnvelope::decode(&message(kind, row["input"].clone()));
        if row["accepted"] == Value::Boolean(true) {
            accepted += 1;
            let decoded = decoded.unwrap();
            let fields = match &decoded.content {
                ServiceContent::Variants(value) => value.to_dictionary(),
                ServiceContent::ContentOverride(value) => value.to_dictionary(),
                _ => panic!(),
            };
            assert_eq!(
                Value::Dictionary(fields),
                row["output"],
                "{:?}",
                row["name"]
            );
            let canonical = decoded.to_value();
            assert_eq!(
                ServiceEnvelope::decode_binary(&binary_plist_writer::encode(&canonical).unwrap())
                    .unwrap(),
                decoded
            );
        } else {
            assert!(
                matches!(
                    decoded,
                    Err(canvas_core::service_envelope::Error::ContentRequest(_))
                ),
                "{:?}",
                row["name"]
            );
        }
        if kind == "variants" {
            assert_eq!(
                RequestPreviewVariantsPayload::decode_dictionary(input).is_ok(),
                row["accepted"] == Value::Boolean(true)
            );
        } else {
            assert_eq!(
                RequestContentOverridePayload::decode_dictionary(input).is_ok(),
                row["accepted"] == Value::Boolean(true)
            );
        }
    }
    assert_eq!(accepted, 10);
}
#[test]
fn scalar_errors_array_index_and_common_identifier_validation_are_explicit() {
    let mut fields = BTreeMap::from([
        ("contentCategory".into(), Value::String("".into())),
        (
            "requestedOverrides".into(),
            Value::Array(vec![Value::String("a".into()), Value::Integer(1)]),
        ),
    ]);
    assert_eq!(
        RequestContentOverridePayload::decode_dictionary(&fields),
        Err(Error::Element {
            key: "requestedOverrides",
            index: 1
        })
    );
    fields.remove("requestedOverrides");
    assert_eq!(
        RequestContentOverridePayload::decode_dictionary(&fields),
        Err(Error::Missing("requestedOverrides"))
    );
    assert_eq!(
        RequestPreviewVariantsPayload::decode_dictionary(&fields)
            .unwrap()
            .content_override,
        None
    );
    fields.insert("contentOverride".into(), Value::String(String::new()));
    assert_eq!(
        RequestPreviewVariantsPayload::decode_dictionary(&fields)
            .unwrap()
            .content_override,
        Some(String::new())
    );
    fields.insert(
        "__unique_service_message_identifier".into(),
        Value::Integer(1),
    );
    assert_eq!(
        ServiceEnvelope::decode(&message("variants", Value::Dictionary(fields))),
        Err(canvas_core::service_envelope::Error::Type(
            "__unique_service_message_identifier"
        ))
    );
}
#[test]
fn inspector_bounds_override_previews_and_preserves_full_canonical_array() {
    let payload = RequestContentOverridePayload {
        content_category: "open-category".into(),
        requested_overrides: vec!["🦀\n\0".into(); 12],
    };
    let input = message(
        "contentOverride",
        Value::Dictionary(payload.to_dictionary()),
    );
    let bytes = binary_plist_writer::encode(&input).unwrap();
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
        child.stdin.take().unwrap().write_all(&bytes).unwrap();
        let out = child.wait_with_output().unwrap();
        assert!(out.status.success());
        assert!(out.stderr.is_empty());
        if canonical {
            assert_eq!(binary_plist::decode(&out.stdout).unwrap(), input);
        } else {
            let summary = String::from_utf8(out.stdout).unwrap();
            assert!(summary.contains("requestedOverrides=12\n"));
            assert!(summary.contains("requestedOverridesShown=8\n"));
            assert!(!summary.contains("requestedOverride8="));
            assert!(!summary.contains('\0'));
            assert!(summary.len() < 4096);
        }
    }
}
