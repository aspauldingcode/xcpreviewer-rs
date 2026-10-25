use canvas_core::{
    binary_plist,
    payload_codec::Value,
    single_select_configuration::{Error, SingleSelectConfiguration as Config, Style},
};
use std::{
    collections::BTreeMap,
    io::Write,
    process::{Command, Stdio},
};
fn dict(entries: &[(&str, Value)]) -> Value {
    Value::Dictionary(
        entries
            .iter()
            .map(|(k, v)| (k.to_string(), v.clone()))
            .collect::<BTreeMap<_, _>>(),
    )
}
fn string(v: &str) -> Value {
    Value::String(v.into())
}
fn rows() -> Vec<Value> {
    match binary_plist::decode(include_bytes!(
        "fixtures/single_select_configuration/native.bplist"
    ))
    .unwrap()
    {
        Value::Array(rows) => rows,
        _ => panic!(),
    }
}
#[test]
fn foundation_compositions_and_complete_round_trips() {
    let mut accepted = 0;
    for row in rows() {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let decoded = Config::decode(&row["input"]);
        assert_eq!(
            decoded.is_ok(),
            row["accepted"] == Value::Boolean(true),
            "{:?}",
            row["name"]
        );
        if let Ok(value) = decoded {
            accepted += 1;
            assert_eq!(value.to_value(), row["output"]);
            assert_eq!(Config::decode(&value.to_value()), Ok(value));
        }
    }
    assert_eq!(accepted, 6);
}
#[test]
fn style_precedes_default_and_does_not_validate_membership() {
    assert_eq!(Config::decode(&dict(&[])), Err(Error::Missing("style")));
    assert_eq!(
        Config::decode(&dict(&[("style", string("bad"))])),
        Err(Error::InvalidStyle)
    );
    assert_eq!(
        Config::decode(&dict(&[("style", Value::Boolean(true))])),
        Err(Error::Type("style"))
    );
    assert_eq!(
        Config::decode(&dict(&[("style", string("list"))])),
        Err(Error::Missing("defaultVariant"))
    );
    assert_eq!(
        Config::decode(&dict(&[
            ("style", string("range")),
            ("defaultVariant", Value::Integer(1))
        ])),
        Err(Error::Type("defaultVariant"))
    );
    assert_eq!(
        Config::decode(&dict(&[
            ("style", string("range")),
            ("defaultVariant", string("not-a-member"))
        ])),
        Ok(Config {
            style: Style::Range,
            default_variant: "not-a-member".into()
        })
    );
}
#[test]
fn cli_explicit_mode_bounded_summary_and_complete_canonical() {
    let cli = env!("CARGO_BIN_EXE_inspect-content-result");
    for row in rows() {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let bytes = canvas_core::binary_plist_writer::encode(&row["input"]).unwrap();
        for canonical in [false, true] {
            let mut command = Command::new(cli);
            if canonical {
                command.arg("--canonical");
            }
            let mut child = command
                .args(["single-selection", "-"])
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
                if canonical {
                    assert_eq!(binary_plist::decode(&output.stdout).unwrap(), row["output"]);
                } else {
                    let out = String::from_utf8(output.stdout).unwrap();
                    assert!(out.starts_with("result=single-selection\nstyle="));
                    assert!(out.len() < 2000);
                    if row["name"] == string("long-id") {
                        assert!(out.contains("defaultVariantTruncated=true"));
                    }
                    if row["name"] == string("opaque-id") {
                        assert!(out.contains("\\n\\\""));
                    }
                }
            } else {
                assert!(output.stdout.is_empty());
            }
        }
    }
}
