//! Actual pinned framework value-method outputs from the owned ARM64 helper.
//! This fixture does not establish UI, transport or global resource settlement.
use canvas_core::{
    binary_plist, binary_plist_writer, payload_codec::Value, plist_value_box::PlistValueBox,
};
use std::{
    io::Write,
    process::{Command, Stdio},
};
#[test]
fn private_framework_value_method_controls() {
    let Value::Array(rows) =
        binary_plist::decode(include_bytes!("fixtures/native_plist_box/native.bplist")).unwrap()
    else {
        panic!()
    };
    let mut accepted = 0;
    for row in rows {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let Value::String(kind) = &row["kind"] else {
            panic!()
        };
        let b = PlistValueBox::decode(&row["input"]).unwrap();
        let decode = |v: &Value| match v {
            Value::String(s) => Ok(s.clone()),
            _ => Err(()),
        };
        let value = if kind == "plist-box" {
            Ok(b.to_value())
        } else {
            let decoded = if kind == "unbox-string" {
                b.required_with(decode).map(Some).map_err(|_| ())
            } else {
                b.optional_with(decode)
            };
            decoded.map(|value| {
                let mut d = std::collections::BTreeMap::new();
                d.insert("isPresent".into(), Value::Boolean(value.is_some()));
                if let Some(value) = value {
                    d.insert("value".into(), Value::String(value));
                }
                Value::Dictionary(d)
            })
        };
        assert_eq!(value.is_ok(), row["accepted"] == Value::Boolean(true));
        if let Ok(value) = value {
            accepted += 1;
            assert_eq!(value, row["output"], "{:?}", row["name"]);
        }
        let bytes = binary_plist_writer::encode(&row["input"]).unwrap();
        let mut child = Command::new(env!("CARGO_BIN_EXE_inspect-content-result"))
            .args(["--canonical", kind, "-"])
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .unwrap();
        child.stdin.take().unwrap().write_all(&bytes).unwrap();
        let output = child.wait_with_output().unwrap();
        assert_eq!(
            output.status.success(),
            row["accepted"] == Value::Boolean(true)
        );
        if output.status.success() {
            assert_eq!(binary_plist::decode(&output.stdout).unwrap(), row["output"]);
        } else {
            assert!(output.stdout.is_empty());
        }
    }
    assert_eq!(accepted, 21);
}
