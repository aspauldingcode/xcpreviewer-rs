use canvas_core::{
    binary_plist, binary_plist_writer, multi_select_configuration,
    payload_codec::Value,
    selection_behavior::{Error, SelectionBehavior as Behavior},
    single_select_configuration,
};
use std::{
    collections::BTreeMap,
    io::Write,
    process::{Command, Stdio},
};
fn dict(fields: &[(&str, Value)]) -> Value {
    Value::Dictionary(
        fields
            .iter()
            .map(|(k, v)| (k.to_string(), v.clone()))
            .collect::<BTreeMap<_, _>>(),
    )
}
fn text(s: &str) -> Value {
    Value::String(s.into())
}
fn rows() -> Vec<Value> {
    let Value::Array(rows) =
        binary_plist::decode(include_bytes!("fixtures/selection_behavior/native.bplist")).unwrap()
    else {
        panic!()
    };
    rows
}
#[test]
fn complete_foundation_compositions_and_round_trips() {
    let mut accepted = 0;
    for row in rows() {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let decoded = Behavior::decode(&row["input"]);
        assert_eq!(
            decoded.is_ok(),
            row["accepted"] == Value::Boolean(true),
            "{:?}",
            row["name"]
        );
        if let Ok(value) = decoded {
            accepted += 1;
            assert_eq!(value.to_value(), row["output"]);
            assert_eq!(Behavior::decode(&value.to_value()), Ok(value));
        }
    }
    assert_eq!(accepted, 11);
}
#[test]
fn discriminator_precedes_branch_and_selected_errors_propagate() {
    assert_eq!(
        Behavior::decode(&dict(&[])),
        Err(Error::Missing("discriminant"))
    );
    assert_eq!(
        Behavior::decode(&dict(&[("discriminant", Value::Boolean(true))])),
        Err(Error::Type("discriminant"))
    );
    assert_eq!(
        Behavior::decode(&dict(&[("discriminant", text("unknown"))])),
        Err(Error::InvalidDiscriminant)
    );
    assert_eq!(
        Behavior::decode(&dict(&[("discriminant", text("singleSelect"))])),
        Err(Error::Missing("singleSelectConfiguration"))
    );
    assert_eq!(
        Behavior::decode(&dict(&[("discriminant", text("multiSelect"))])),
        Err(Error::Missing("multiSelectConfiguration"))
    );
    assert_eq!(
        Behavior::decode(&dict(&[
            ("discriminant", text("singleSelect")),
            ("singleSelectConfiguration", dict(&[]))
        ])),
        Err(Error::SingleSelect(
            single_select_configuration::Error::Missing("style")
        ))
    );
    assert_eq!(
        Behavior::decode(&dict(&[
            ("discriminant", text("multiSelect")),
            (
                "multiSelectConfiguration",
                dict(&[(
                    "defaultVariants",
                    Value::Array(vec![text("id"), Value::Boolean(true)])
                )])
            )
        ])),
        Err(Error::MultiSelect(
            multi_select_configuration::Error::Element {
                key: "defaultVariants",
                index: 1
            }
        ))
    );
}
#[test]
fn explicit_cli_active_summary_and_complete_canonical() {
    for row in rows() {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let bytes = binary_plist_writer::encode(&row["input"]).unwrap();
        for canonical in [false, true] {
            let mut command = Command::new(env!("CARGO_BIN_EXE_inspect-content-result"));
            if canonical {
                command.arg("--canonical");
            }
            let mut child = command
                .args(["selection-behavior", "-"])
                .stdin(Stdio::piped())
                .stdout(Stdio::piped())
                .stderr(Stdio::piped())
                .spawn()
                .unwrap();
            child.stdin.take().unwrap().write_all(&bytes).unwrap();
            let out = child.wait_with_output().unwrap();
            assert_eq!(
                out.status.success(),
                row["accepted"] == Value::Boolean(true)
            );
            if out.status.success() {
                if canonical {
                    assert_eq!(binary_plist::decode(&out.stdout).unwrap(), row["output"]);
                } else {
                    let s = String::from_utf8(out.stdout).unwrap();
                    assert!(s.starts_with("result=selection-behavior\ndiscriminant="));
                    assert!(s.len() < 3000);
                    if row["name"] == text("long-single") {
                        assert!(s.contains("defaultVariantTruncated=true"));
                    }
                    if row["name"] == text("many-multi") {
                        assert!(s.contains("defaultVariants=20"));
                        assert!(s.contains("defaultVariantsShown=8"));
                    }
                }
            } else {
                assert!(out.stdout.is_empty());
            }
        }
    }
}
