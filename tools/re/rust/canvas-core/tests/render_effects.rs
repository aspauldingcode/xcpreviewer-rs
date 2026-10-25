use canvas_core::{
    binary_plist, binary_plist_writer, content_results::PreviewVariant, payload_codec::Value,
    render_effects,
};
use std::{
    io::Write,
    process::{Command, Stdio},
};
fn rows() -> Vec<Value> {
    let Value::Array(v) =
        binary_plist::decode(include_bytes!("fixtures/render_effects/native.bplist")).unwrap()
    else {
        panic!()
    };
    v
}
type Inputs = (Vec<PreviewVariant>, Option<PreviewVariant>);
fn decode(v: &Value) -> Option<Inputs> {
    let Value::Dictionary(f) = v else {
        return None;
    };
    let Value::Array(a) = f.get("overrides")? else {
        return None;
    };
    let overrides = a
        .iter()
        .map(PreviewVariant::decode)
        .collect::<Result<Vec<_>, _>>()
        .ok()?;
    let variant = f
        .get("variant")
        .map(PreviewVariant::decode)
        .transpose()
        .ok()?;
    Some((overrides, variant))
}
fn output(config: &Inputs) -> Value {
    Value::Array(
        render_effects::assemble(&config.0, config.1.as_ref())
            .iter()
            .map(|e| e.to_value())
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
        let config = decode(&row["input"]);
        assert_eq!(config.is_some(), row["accepted"] == Value::Boolean(true));
        if let Some(config) = config {
            accepted += 1;
            assert_eq!(output(&config), row["output"], "{:?}", row["name"]);
        }
    }
    assert_eq!(accepted, 14);
}
#[test]
fn assembly_preserves_inputs_and_returns_owned_effects() {
    for row in rows() {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        if let Some(config) = decode(&row["input"]) {
            let before = config.clone();
            let expected = output(&config);
            let mut effects = render_effects::assemble(&config.0, config.1.as_ref());
            if let Some(first) = effects.first_mut() {
                first.id = "result-only-mutation".into();
            }
            assert_eq!(config, before);
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
                .args(["render-effects", "-"])
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
                    assert!(s.starts_with("result=render-effects\n"));
                    assert!(s.len() < 4000);
                    if row["name"] == Value::String("long".into()) {
                        assert!(s.contains("effect0Truncated=true"));
                    }
                    if row["name"] == Value::String("many".into()) {
                        assert!(s.contains("effects=20"));
                        assert!(s.contains("effectsShown=8"));
                    }
                }
            } else {
                assert!(out.stdout.is_empty());
            }
        }
    }
}
