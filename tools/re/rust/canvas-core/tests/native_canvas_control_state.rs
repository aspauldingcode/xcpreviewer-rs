//! Actual shipped Pipeline CanvasControlState controls from an owned helper.
use canvas_core::{
    binary_plist,
    canvas_control_state::{CanvasControlState, Error},
    payload_codec::Value,
    plist_value_box::Error as BoxError,
};
use std::{
    collections::hash_map::DefaultHasher,
    hash::{Hash, Hasher},
};
fn hash(value: &CanvasControlState) -> u64 {
    let mut h = DefaultHasher::new();
    value.hash(&mut h);
    h.finish()
}
#[test]
fn native_order_empty_multiplicity_and_source_copy_survival() {
    let Value::Dictionary(v) = binary_plist::decode(include_bytes!(
        "fixtures/native_canvas_control_state/native.bplist"
    ))
    .unwrap() else {
        panic!()
    };
    assert_eq!(
        v["privateCanvasControlStateMethodsInvoked"],
        Value::Boolean(true)
    );
    assert_eq!(v["sourceWrapperDestructionReturns"], Value::Integer(14));
    let Value::Array(rows) = &v["rows"] else {
        panic!()
    };
    let states: Vec<_> = rows
        .iter()
        .map(|row| {
            let Value::Dictionary(row) = row else {
                panic!()
            };
            let state = CanvasControlState::decode(&row["values"]).unwrap();
            assert_eq!(state.to_value(), row["values"]);
            if row["nativeEmptyGetter"] == Value::Boolean(true) {
                assert_eq!(state, CanvasControlState::default());
            }
            state
        })
        .collect();
    let Value::Array(pairs) = &v["pairs"] else {
        panic!()
    };
    for pair in pairs {
        let Value::Dictionary(pair) = pair else {
            panic!()
        };
        let (Value::Integer(i), Value::Integer(j)) = (&pair["left"], &pair["right"]) else {
            panic!()
        };
        let (a, b) = (&states[*i as usize], &states[*j as usize]);
        assert_eq!(
            a == b,
            pair["equal"] == Value::Boolean(true),
            "native pair{i}/{j}"
        );
        if a == b {
            assert_eq!(hash(a), hash(b));
            assert_eq!(pair["sameHash"], Value::Boolean(true));
        }
    }
    assert_eq!(states.len(), 24);
    assert_eq!(pairs.len(), 576);
    assert_ne!(states[5], states[6]);
    assert_ne!(states[2], states[7]);
    assert_ne!(states[0], states[19]);
}
#[test]
fn full_sequence_validation_reports_element_position() {
    assert_eq!(
        CanvasControlState::decode(&Value::Integer(0)).unwrap_err(),
        Error::Array
    );
    let value = Value::Array(vec![
        Value::Dictionary(Default::default()),
        Value::Integer(0),
    ]);
    assert_eq!(
        CanvasControlState::decode(&value).unwrap_err(),
        Error::Box {
            index: 1,
            cause: BoxError::Dictionary
        }
    );
    let value = Value::Array(vec![
        Value::Dictionary(Default::default()),
        Value::Dictionary([("value".into(), Value::Null)].into_iter().collect()),
    ]);
    assert!(matches!(
        CanvasControlState::decode(&value),
        Err(Error::Snapshot { index: 1, .. })
    ));
}
