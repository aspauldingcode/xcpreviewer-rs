use canvas_core::{
    binary_plist,
    canvas_control_state::CanvasControlState,
    payload_codec::Value,
    plist_value_box::{ArrayError, Error as BoxError},
    shell_control_states::{Error, ShellControlStates},
};
use std::collections::BTreeMap;
fn dict(value: &Value) -> &BTreeMap<String, Value> {
    let Value::Dictionary(v) = value else {
        panic!()
    };
    v
}
fn envelope() -> Value {
    Value::Dictionary(
        [("opaque".into(), Value::String("keep".into()))]
            .into_iter()
            .collect(),
    )
}
#[test]
fn actual_native_shell_field_roundtrips_and_present_errors() {
    let fixture = binary_plist::decode(include_bytes!(
        "fixtures/native_shell_control_states/native.bplist"
    ))
    .unwrap();
    let Value::Array(rows) = &dict(&fixture)["rows"] else {
        panic!()
    };
    assert_eq!(rows.len(), 21);
    let mut accepts = 0;
    for row in rows {
        let r = dict(row);
        let input = &r["input"];
        let before = input.clone();
        let result = ShellControlStates::read_from(input);
        assert_eq!(result.is_ok(), r["accepted"] == Value::Boolean(true));
        if let Ok(states) = result {
            accepts += 1;
            let canonical = dict(&r["canonical"]);
            let projected = states
                .boxes()
                .map(|b| Value::Array(b.iter().map(|v| v.to_value()).collect()));
            assert_eq!(projected.as_ref(), canonical.get("controlStates"));
            assert_eq!(states.write_to(input).unwrap(), *input);
        }
        assert_eq!(*input, before);
    }
    assert_eq!(accepts, 13);
    for name in ["destroyedShells", "destroyedPlists"] {
        assert_eq!(dict(&fixture)[name], Value::Integer(13));
    }
    assert_eq!(dict(&fixture)["releasedShellErrors"], Value::Integer(8));
}
#[test]
fn canvas_projection_preserves_original_values_and_explicit_presence() {
    let array = Value::Array(vec![
        Value::Dictionary(
            [
                ("value".into(), Value::String("e\u{301}".into())),
                ("future".into(), Value::Boolean(false)),
            ]
            .into_iter()
            .collect(),
        ),
        Value::Dictionary(BTreeMap::new()),
    ]);
    let state = CanvasControlState::decode(&array).unwrap();
    let projected = ShellControlStates::from_canvas_state(&state);
    drop(state);
    let source = envelope();
    let installed = projected.write_to(&source).unwrap();
    assert_eq!(dict(&installed)["controlStates"], array);
    assert_eq!(dict(&installed)["opaque"], dict(&source)["opaque"]);
    let cleared = ShellControlStates::Absent.write_to(&installed).unwrap();
    assert_eq!(cleared, source);
    let empty = ShellControlStates::from_canvas_state(&CanvasControlState::default())
        .write_to(&source)
        .unwrap();
    assert_eq!(dict(&empty)["controlStates"], Value::Array(vec![]));
    assert_ne!(empty, cleared);
    assert!(ShellControlStates::read_from(&source)
        .unwrap()
        .boxes()
        .is_none());
    // A malformed old field can be replaced explicitly without decoding it.
    let bad = Value::Dictionary(
        [("controlStates".into(), Value::Boolean(false))]
            .into_iter()
            .collect(),
    );
    assert!(ShellControlStates::read_from(&bad).is_err());
    assert!(ShellControlStates::Absent.write_to(&bad).is_ok());
}
#[test]
fn facet_scope_and_indexed_errors_are_explicit() {
    let input = Value::Dictionary(
        [(
            "controlStates".into(),
            Value::Array(vec![Value::Dictionary(BTreeMap::new()), Value::Integer(1)]),
        )]
        .into_iter()
        .collect(),
    );
    assert!(matches!(
        ShellControlStates::read_from(&input),
        Err(Error::States(ArrayError::Element {
            index: 1,
            cause: BoxError::Dictionary
        }))
    ));
    assert!(matches!(
        ShellControlStates::read_from(&Value::Array(vec![])),
        Err(Error::Envelope(BoxError::Dictionary))
    ));
    let collision = Value::Dictionary(
        [
            ("é".into(), Value::Integer(1)),
            ("e\u{301}".into(), Value::Integer(2)),
        ]
        .into_iter()
        .collect(),
    );
    assert!(matches!(
        ShellControlStates::read_from(&collision),
        Err(Error::Envelope(BoxError::CanonicalKeyCollision))
    ));
    // This facet deliberately accepts an empty envelope; full shell decoding
    // requires additional fields and is outside this API's contract.
    assert!(ShellControlStates::read_from(&Value::Dictionary(BTreeMap::new())).is_ok());
}
