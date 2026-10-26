use canvas_core::{
    binary_plist,
    incremental_update::Error as UpdateError,
    payload_codec::Value,
    setup_payload::{Error, UpdateSetupPayload as Setup},
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
fn native_setup_record_and_nested_validation() {
    let Value::Dictionary(f) = binary_plist::decode(include_bytes!(
        "fixtures/native_setup_payload/native.bplist"
    ))
    .unwrap() else {
        panic!()
    };
    let Value::Array(rows) = &f["rows"] else {
        panic!()
    };
    assert_eq!(rows.len(), 114);
    let (mut accepted, mut rejected, mut ambiguous) = (0, 0, 0);
    for row in rows {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let result = Setup::decode_single_entry_updates(&row["input"]);
        if let Err(Error::Update {
            error: UpdateError::AmbiguousNativeSelection { .. },
            ..
        }) = result
        {
            assert_eq!(row["accepted"], Value::Boolean(true));
            ambiguous += 1;
            continue;
        }
        assert_eq!(result.is_ok(), row["accepted"] == Value::Boolean(true));
        if let Ok(setup) = result {
            accepted += 1;
            assert!(equal(
                &ordered(setup.to_value()),
                &ordered(row["canonical"].clone())
            ));
            assert!(equal(
                &binary_plist::decode(&setup.to_binary_plist().unwrap()).unwrap(),
                &setup.to_value()
            ))
        } else {
            rejected += 1
        }
    }
    assert_eq!((accepted, rejected, ambiguous), (44, 65, 5));
}
#[test]
fn setup_default_and_outer_schema() {
    let default = Setup::default();
    let Value::Dictionary(f) = default.to_value() else {
        panic!()
    };
    assert_eq!(f.len(), 4);
    assert_eq!(f["shellDidLoadStaticProducts"], Value::Boolean(false));
    assert_eq!(
        Setup::decode_single_entry_updates(&Value::Array(vec![])).unwrap_err(),
        Error::Dictionary
    );
}
