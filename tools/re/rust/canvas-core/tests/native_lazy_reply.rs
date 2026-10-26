use canvas_core::{
    binary_plist,
    payload_codec::Value,
    shell_payload::ShellUpdatePayload,
    transport_reply::{decode_reply_with, LazyReply},
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

fn rows() -> Vec<Value> {
    let Value::Dictionary(f) =
        binary_plist::decode(include_bytes!("fixtures/native_lazy_reply/native.bplist")).unwrap()
    else {
        panic!()
    };
    let Value::Array(rows) = &f["rows"] else {
        panic!()
    };
    rows.clone()
}
#[test]
fn native_lazy_resolution_and_explicit_xml_boundary() {
    let rows = rows();
    assert_eq!(rows.len(), 20);
    let (mut successes, mut failures, mut xml) = (0, 0, 0);
    for row in &rows[..19] {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        assert_eq!(row["sourceDestroyedBeforeRead"], Value::Boolean(true));
        assert_eq!(row["dataError"], Value::Boolean(false));
        let Value::Data(data) = &row["data"] else {
            panic!()
        };
        let lazy = LazyReply::Serialized(data.clone());
        if data.starts_with(b"<?xml") {
            xml += 1;
            assert!(lazy.property_list().is_err());
            continue;
        }
        for _ in 0..2 {
            let result = lazy.property_list();
            assert_eq!(result.is_ok(), row["accepted"] == Value::Boolean(true));
            if let Ok(fields) = result {
                let Value::Array(native) = &row["decoded"] else {
                    panic!()
                };
                assert!(equal(&Value::Dictionary(fields), &native[0]));
            }
        }
        if row["accepted"] == Value::Boolean(true) {
            successes += 1
        } else {
            failures += 1
        }
    }
    assert_eq!((successes, failures, xml), (8, 9, 2));
}
#[test]
fn native_lazy_typed_shell_composition_and_buffer_receipt() {
    let rows = rows();
    let mut shells = 0;
    for row in &rows[..19] {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let Value::Array(decoded) = &row["decoded"] else {
            panic!()
        };
        let Some(Value::Dictionary(fields)) = decoded.first() else {
            continue;
        };
        if !fields.contains_key("setupPayload") {
            continue;
        }
        let Value::Data(data) = &row["data"] else {
            panic!()
        };
        let shell = decode_reply_with(
            Some(LazyReply::Serialized(data.clone())),
            None::<()>,
            ShellUpdatePayload::decode_single_entry_updates,
        )
        .unwrap();
        assert!(equal(
            &ordered(shell.to_value()),
            &ordered(decoded[0].clone())
        ));
        shells += 1;
    }
    assert_eq!(shells, 4);
    let Value::Dictionary(lifetime) = &rows[19] else {
        panic!()
    };
    assert_eq!(lifetime["ownedBytes"], Value::Integer(8192));
    assert_eq!(
        lifetime["aliveAfterSourceAndCopyDestroyed"],
        Value::Boolean(true)
    );
    assert_eq!(lifetime["allReturnedBytesMatched"], Value::Boolean(true));
    assert_eq!(lifetime["finalCustomDeallocatorCalls"], Value::Integer(1));
}
