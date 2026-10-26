use canvas_core::{
    binary_plist, built_target::BuiltTargetDescription as Target, payload_codec::Value,
};
fn ordered(mut value: Value) -> Value {
    match &mut value {
        Value::Dictionary(f) => {
            for (k, v) in f {
                if k == "sourceFilePaths" || k == "linkerFlags" {
                    if let Value::Array(a) = v {
                        a.sort_by(|a, b| match (a, b) {
                            (Value::String(a), Value::String(b)) => a.cmp(b),
                            _ => panic!(),
                        });
                    }
                } else {
                    *v = ordered(v.clone());
                }
            }
        }
        Value::Array(a) => {
            for v in a {
                *v = ordered(v.clone());
            }
        }
        _ => {}
    }
    value
}
fn rows() -> Vec<Value> {
    let Value::Dictionary(mut f) =
        binary_plist::decode(include_bytes!("fixtures/native_built_target/native.bplist")).unwrap()
    else {
        panic!()
    };
    let Value::Array(rows) = f.remove("rows").unwrap() else {
        panic!()
    };
    rows
}
#[test]
fn native_built_target_values_and_nested_errors() {
    let rows = rows();
    assert_eq!(rows.len(), 164);
    let mut accepted = 0;
    for row in rows {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let decoded = Target::decode(&row["input"]);
        assert_eq!(decoded.is_ok(), row["accepted"] == Value::Boolean(true));
        if let Ok(target) = decoded {
            accepted += 1;
            assert!(target.merged_module_names.is_empty());
            assert_eq!(
                ordered(target.to_value()),
                ordered(row["canonical"].clone())
            );
        }
    }
    assert_eq!(accepted, 62);
}
#[test]
fn native_nonwire_merged_field_survives_encoding() {
    let mut controls = 0;
    for row in rows() {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        if row
            .get("mergedBeforeEncoding")
            .is_some_and(|v| v != &Value::Array(vec![]))
        {
            controls += 1;
            assert_eq!(row["decodedMergedModuleNames"], Value::Array(vec![]));
            assert_eq!(row["mergedBeforeEncoding"], row["mergedAfterEncoding"]);
            let mut target = Target::decode(&row["input"]).unwrap();
            let Value::Array(values) = &row["mergedBeforeEncoding"] else {
                panic!()
            };
            target.merged_module_names = values
                .iter()
                .map(|v| {
                    let Value::String(s) = v else { panic!() };
                    s.clone()
                })
                .collect();
            assert_eq!(
                ordered(target.to_value()),
                ordered(row["canonical"].clone())
            );
            assert_eq!(target.merged_module_names.len(), 3);
        }
    }
    assert_eq!(controls, 1);
}
#[test]
fn built_target_requires_dictionary() {
    assert!(Target::decode(&Value::Array(vec![])).is_err());
}
