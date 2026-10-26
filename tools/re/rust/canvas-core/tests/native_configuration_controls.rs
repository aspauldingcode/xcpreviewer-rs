use canvas_core::{
    binary_plist, canvas_control_state::CanvasControlState, hashable_plist_box::HashablePlistBox,
    payload_codec::Value, plist_value_box::PlistValueBox, shell_control_states::ShellControlStates,
};
use std::collections::BTreeMap;
fn dict(v: &Value) -> &BTreeMap<String, Value> {
    let Value::Dictionary(v) = v else { panic!() };
    v
}
#[test]
fn actual_execution_point_keypath_getter_projection() {
    let fixture = binary_plist::decode(include_bytes!(
        "fixtures/native_configuration_controls/native.bplist"
    ))
    .unwrap();
    let f = dict(&fixture);
    assert_eq!(
        f["privateExecutionPointKeypathGetterInvoked"],
        Value::Boolean(true)
    );
    assert_eq!(f["keypathGetterCalls"], Value::Integer(29));
    assert_eq!(f["sourceWrapperDestructionReturns"], Value::Integer(14));
    let Value::Array(rows) = &f["rows"] else {
        panic!()
    };
    assert_eq!(rows.len(), 24);
    let input = dict(&f["input"]);
    let Value::Array(boxes) = &input["boxes"] else {
        panic!()
    };
    for row in rows {
        let r = dict(row);
        let Value::Array(indices) = &r["indices"] else {
            panic!()
        };
        let values = Value::Array(
            indices
                .iter()
                .map(|i| {
                    let Value::Integer(i) = i else { panic!() };
                    boxes[*i as usize].clone()
                })
                .collect(),
        );
        let state = CanvasControlState::decode(&values).unwrap();
        let controls = ShellControlStates::from_configuration_states(state.states());
        drop(state);
        let out = controls
            .write_to(&Value::Dictionary(BTreeMap::new()))
            .unwrap();
        assert_eq!(dict(&out)["controlStates"], r["values"]);
        assert!(controls.boxes().is_some());
    }
}
#[test]
fn equal_cached_keys_do_not_replace_original_wire_types() {
    let a = HashablePlistBox::new(PlistValueBox::from_value(Value::Integer(1))).unwrap();
    let b = HashablePlistBox::new(PlistValueBox::from_value(Value::Real(1.0))).unwrap();
    assert_eq!(a, b);
    let controls = ShellControlStates::from_configuration_states(&[a.clone(), b.clone(), a]);
    drop(b);
    let values = controls
        .boxes()
        .unwrap()
        .iter()
        .map(|b| b.value().unwrap().clone())
        .collect::<Vec<_>>();
    assert_eq!(
        values,
        vec![Value::Integer(1), Value::Real(1.0), Value::Integer(1)]
    );
    assert!(matches!(values[1], Value::Real(_)));
    assert!(matches!(values[0], Value::Integer(_)));
    let empty = ShellControlStates::from_configuration_states(&[]);
    assert_eq!(empty.boxes().unwrap().len(), 0);
}
