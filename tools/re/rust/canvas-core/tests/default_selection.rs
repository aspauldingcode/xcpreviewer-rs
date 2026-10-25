use canvas_core::{
    binary_plist, binary_plist_writer,
    overrides_configuration::PreviewOverridesConfiguration as Config, payload_codec::Value,
};
use std::{
    io::Write,
    process::{Command, Stdio},
};
fn rows() -> Vec<Value> {
    let Value::Array(v) =
        binary_plist::decode(include_bytes!("fixtures/default_selection/native.bplist")).unwrap()
    else {
        panic!()
    };
    v
}
fn output(config: &Config) -> Value {
    Value::Array(
        config
            .default_selection()
            .iter()
            .map(|s| Value::String(s.into()))
            .collect(),
    )
}
#[test]
fn complete_source_guided_calculation_controls() {
    let mut accepted = 0;
    for row in rows() {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let config = Config::decode(&row["input"]);
        assert_eq!(config.is_ok(), row["accepted"] == Value::Boolean(true));
        if let Ok(config) = config {
            accepted += 1;
            assert_eq!(output(&config), row["output"], "{:?}", row["name"]);
        }
    }
    assert_eq!(accepted, 20);
}
#[test]
fn calculation_preserves_configuration_and_returns_owned_set() {
    for row in rows() {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        if let Ok(config) = Config::decode(&row["input"]) {
            let before = config.to_value();
            let expected = output(&config);
            let mut selected = config.default_selection();
            selected.insert("result-only-mutation".into());
            assert_eq!(config.to_value(), before);
            assert_eq!(output(&config), expected);
        }
    }
}
#[test]
fn cli_derived_array_and_bounded_summary() {
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
                .args(["default-selection", "-"])
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
                    assert!(s.starts_with("result=default-selection\n"));
                    assert!(s.len() < 4000);
                    if row["name"] == Value::String("long".into()) {
                        assert!(s.contains("selected0Truncated=true"));
                    }
                    if row["name"] == Value::String("many".into()) {
                        assert!(s.contains("selected=20"));
                        assert!(s.contains("selectedShown=8"));
                    }
                }
            } else {
                assert!(out.stdout.is_empty());
            }
        }
    }
}
