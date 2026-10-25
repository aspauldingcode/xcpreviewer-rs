use canvas_core::{
    binary_plist, binary_plist_writer, payload_codec::Value,
    variants_reply::PreviewVariantGroup as Config,
};
use std::{
    io::Write,
    process::{Command, Stdio},
};
fn rows() -> Vec<Value> {
    let Value::Array(v) =
        binary_plist::decode(include_bytes!("fixtures/group_variants/native.bplist")).unwrap()
    else {
        panic!()
    };
    v
}
fn output(config: &Config) -> Value {
    Value::Dictionary(
        [
            ("overrides", config.overrides_variants().to_vec()),
            ("grid", config.grid_variants()),
            ("all", config.all_variants()),
        ]
        .into_iter()
        .map(|(k, v)| {
            (
                k.into(),
                Value::Array(v.iter().map(|v| v.to_value()).collect()),
            )
        })
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
    assert_eq!(accepted, 11);
}
#[test]
fn enumeration_preserves_configuration_and_returns_owned_values() {
    for row in rows() {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        if let Ok(config) = Config::decode(&row["input"]) {
            let before = config.to_value();
            let expected = output(&config);
            let mut selected = config.all_variants();
            if let Some(first) = selected.first_mut() {
                first.id = "result-only-mutation".into();
            }
            assert_eq!(config.to_value(), before);
            assert_eq!(output(&config), expected);
        }
    }
}
#[test]
fn cli_derived_lists_and_bounded_summary() {
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
                .args(["group-variants", "-"])
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
                    assert!(s.starts_with("result=group-variants\n"));
                    assert!(s.len() < 40000);
                    if row["name"] == Value::String("many-long".into()) {
                        assert!(s.contains("overrides0.displayNameTruncated=true"));
                        assert!(s.contains("overrides=12\n"));
                        assert!(s.contains("overridesShown=8"));
                        assert!(s.contains("allShown=8"));
                    }
                }
            } else {
                assert!(out.stdout.is_empty());
            }
        }
    }
}
