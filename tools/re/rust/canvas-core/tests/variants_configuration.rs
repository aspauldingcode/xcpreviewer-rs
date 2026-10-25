use canvas_core::{
    binary_plist, binary_plist_writer,
    payload_codec::Value,
    variants_configuration::{Error, PreviewVariantsConfiguration, Section},
};
use std::{
    collections::BTreeMap,
    io::Write,
    process::{Command, Stdio},
};
fn rows() -> Vec<Value> {
    let Value::Array(rows) = binary_plist::decode(include_bytes!(
        "fixtures/variants_configuration/native.bplist"
    ))
    .unwrap() else {
        panic!()
    };
    rows
}
fn value(items: Vec<(&str, Value)>) -> Value {
    Value::Dictionary(
        items
            .into_iter()
            .map(|(k, v)| (k.into(), v))
            .collect::<BTreeMap<_, _>>(),
    )
}
#[test]
fn complete_foundation_controls_preserve_sections_titles_order_and_compatibility() {
    let rows = rows();
    assert_eq!(rows.len(), 24);
    let mut accepted = 0;
    for row in rows {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let Value::String(kind) = &row["kind"] else {
            panic!()
        };
        let decoded = if kind == "configuration" {
            PreviewVariantsConfiguration::decode(&row["input"]).map(|v| v.to_value())
        } else {
            Section::decode(&row["input"]).map(|v| v.to_value())
        };
        assert_eq!(
            decoded.is_ok(),
            row["accepted"] == Value::Boolean(true),
            "{:?}",
            row["name"]
        );
        if let Ok(decoded) = decoded {
            accepted += 1;
            assert_eq!(decoded, row["output"], "{:?}", row["name"]);
            let again =
                binary_plist::decode(&binary_plist_writer::encode(&decoded).unwrap()).unwrap();
            let again = if kind == "configuration" {
                PreviewVariantsConfiguration::decode(&again).map(|v| v.to_value())
            } else {
                Section::decode(&again).map(|v| v.to_value())
            };
            assert_eq!(again.unwrap(), decoded);
        }
    }
    assert_eq!(accepted, 11);
}
#[test]
fn required_optional_titles_and_indexed_failures_are_distinct() {
    assert_eq!(
        PreviewVariantsConfiguration::decode(&value(vec![])),
        Err(Error::Missing("title"))
    );
    assert_eq!(
        Section::decode(&value(vec![("title", Value::Integer(1))])),
        Err(Error::Type("title"))
    );
    assert_eq!(
        Section::decode(&value(vec![])),
        Err(Error::Missing("variants"))
    );
    let config = value(vec![
        ("title", Value::String("Grid".into())),
        (
            "sections",
            Value::Array(vec![
                value(vec![("variants", Value::Array(vec![]))]),
                Value::Integer(7),
            ]),
        ),
    ]);
    assert_eq!(
        PreviewVariantsConfiguration::decode(&config),
        Err(Error::Section {
            index: 1,
            cause: Box::new(Error::Type("dictionary"))
        })
    );
    let section = value(vec![("variants", Value::Array(vec![Value::Integer(7)]))]);
    assert!(matches!(
        Section::decode(&section),
        Err(Error::Variant { index: 0, .. })
    ));
    let absent = Section::decode(&value(vec![("variants", Value::Array(vec![]))])).unwrap();
    let present = Section::decode(&value(vec![
        ("variants", Value::Array(vec![])),
        ("title", Value::String(String::new())),
    ]))
    .unwrap();
    assert_eq!(absent.title, None);
    assert_eq!(present.title, Some(String::new()));
    assert_ne!(absent.to_value(), present.to_value());
}
#[test]
fn inspector_supports_both_modes_and_bounds_nested_previews() {
    for row in rows() {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let Value::String(kind) = &row["kind"] else {
            panic!()
        };
        let bytes = binary_plist_writer::encode(&row["input"]).unwrap();
        for canonical in [true, false] {
            let mut command = Command::new(env!("CARGO_BIN_EXE_inspect-content-result"));
            if canonical {
                command.arg("--canonical");
            }
            command.arg(kind).arg("-");
            let mut child = command
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
            if row["accepted"] == Value::Boolean(true) {
                assert!(out.stderr.is_empty());
                if canonical {
                    assert_eq!(binary_plist::decode(&out.stdout).unwrap(), row["output"]);
                } else {
                    let summary = String::from_utf8(out.stdout).unwrap();
                    assert!(summary.starts_with(&format!("result={kind}\n")));
                    assert!(!summary.contains('\0'));
                    assert!(summary.len() < 50000);
                    if row["name"] == Value::String("bounded-summary".into()) {
                        assert!(summary.contains("sections=6\n"));
                        assert!(summary.contains("sectionsShown=4\n"));
                        assert!(summary.contains("section0.variantsShown=4\n"));
                        assert!(!summary.contains("section4.title="));
                        assert!(!summary.contains(".variant4.id="));
                        assert!(summary.contains("section0.titleTruncated=true\n"));
                    }
                }
            } else {
                assert!(out.stdout.is_empty());
                assert!(!out.stderr.is_empty());
            }
        }
    }
}
