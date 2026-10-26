use canvas_core::{
    binary_plist,
    incremental_update::Error as UpdateError,
    payload_codec::Value,
    setup_payload::Error as SetupError,
    shell_payload::{Error, ShellUpdatePayload as Shell},
};
fn equal(a: &Value, b: &Value) -> bool {
    match (a, b) {
        (Value::Real(a), Value::Real(b)) => a.to_bits() == b.to_bits(),
        (Value::Dictionary(a), Value::Dictionary(b)) => {
            a.len() == b.len() && a.iter().all(|(k, v)| b.get(k).is_some_and(|x| equal(v, x)))
        }
        (Value::Array(a), Value::Array(b)) => {
            a.len() == b.len() && a.iter().zip(b).all(|(a, b)| equal(a, b))
        }
        _ => a == b,
    }
}
fn ordered(mut v: Value) -> Value {
    match &mut v {
        Value::Dictionary(f) => {
            for (k, v) in f {
                if k == "sourceFilePaths" || k == "linkerFlags" {
                    if let Value::Array(a) = v {
                        a.sort_by(|a, b| match (a, b) {
                            (Value::String(a), Value::String(b)) => a.cmp(b),
                            _ => panic!(),
                        })
                    }
                } else {
                    *v = ordered(v.clone())
                }
            }
        }
        Value::Array(a) => {
            for v in a {
                *v = ordered(v.clone())
            }
        }
        _ => {}
    }
    v
}
#[test]
fn native_complete_shell_fields_with_portable_limits() {
    let Value::Dictionary(f) = binary_plist::decode(include_bytes!(
        "fixtures/native_shell_payload/native.bplist"
    ))
    .unwrap() else {
        panic!()
    };
    let Value::Array(rows) = &f["rows"] else {
        panic!()
    };
    assert_eq!(rows.len(), 372);
    let (mut accepted, mut rejected, mut ambiguous) = (0, 0, 0);
    for row in rows {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let result = Shell::decode_single_entry_updates(&row["input"]);
        if let Err(Error::Setup(SetupError::Update {
            error: UpdateError::AmbiguousNativeSelection { .. },
            ..
        })) = result
        {
            assert_eq!(row["accepted"], Value::Boolean(true));
            ambiguous += 1;
            continue;
        }
        assert_eq!(result.is_ok(), row["accepted"] == Value::Boolean(true));
        if let Ok(shell) = result {
            accepted += 1;
            assert!(equal(
                &ordered(shell.to_value()),
                &ordered(row["canonical"].clone())
            ));
            assert!(equal(
                &binary_plist::decode(&shell.to_binary_plist().unwrap()).unwrap(),
                &shell.to_value()
            ))
        } else {
            rejected += 1
        }
    }
    assert_eq!((accepted, rejected, ambiguous), (129, 237, 6));
}
#[test]
fn shell_outer_schema_and_optional_presence() {
    assert_eq!(
        Shell::decode_single_entry_updates(&Value::Array(vec![])).unwrap_err(),
        Error::Dictionary
    );
    let Value::Dictionary(f) = binary_plist::decode(include_bytes!(
        "fixtures/native_shell_payload/native.bplist"
    ))
    .unwrap() else {
        panic!()
    };
    let Value::Array(rows) = &f["rows"] else {
        panic!()
    };
    let Value::Dictionary(row) = &rows[0] else {
        panic!()
    };
    let shell = Shell::decode_single_entry_updates(&row["input"]).unwrap();
    assert!(shell.control_states.boxes().is_none());
    assert!(shell.host_update_seed.is_none());
    assert!(shell.host_update_group_seed.is_none());
    assert!(shell.content_override.is_none());
    let Value::Dictionary(mut value) = shell.to_value() else {
        panic!()
    };
    value.insert("controlStates".into(), Value::Array(vec![]));
    let present = Shell::decode_single_entry_updates(&Value::Dictionary(value)).unwrap();
    assert_eq!(present.control_states.boxes().unwrap().len(), 0);
}
