use canvas_core::{
    binary_plist, binary_plist_writer, effective_overrides::VariantGroupSettings,
    overrides_configuration::PreviewOverridesConfiguration, payload_codec::Value,
    variant_id_set::VariantIdSet,
};
use std::{
    io::Write,
    process::{Command, Stdio},
};
fn rows() -> Vec<Value> {
    let Value::Array(rows) =
        binary_plist::decode(include_bytes!("fixtures/selection_update/native.bplist")).unwrap()
    else {
        panic!()
    };
    rows
}
fn calculate(v: &Value) -> Option<Value> {
    let Value::Dictionary(f) = v else {
        return None;
    };
    let config = PreviewOverridesConfiguration::decode(f.get("configuration")?).ok()?;
    let Value::Boolean(enabled) = f.get("isEnabled")? else {
        return None;
    };
    let ids = |key: &str| -> Option<VariantIdSet> {
        let Value::Array(a) = f.get(key)? else {
            return None;
        };
        a.iter()
            .map(|v| {
                if let Value::String(id) = v {
                    Some(id.clone())
                } else {
                    None
                }
            })
            .collect()
    };
    let mut state = VariantGroupSettings {
        is_enabled: *enabled,
        selection: ids("selection")?,
    };
    let before = config.to_value();
    let update = state.update_multi_selection(&config, ids("requestedSelection")?);
    assert_eq!(config.to_value(), before);
    Some(Value::Dictionary(
        [
            ("isEnabled".into(), Value::Boolean(state.is_enabled)),
            (
                "selectionChanged".into(),
                Value::Boolean(update.selection_changed),
            ),
            (
                "selection".into(),
                Value::Array(
                    state
                        .selection
                        .iter()
                        .map(|id| Value::String(id.into()))
                        .collect(),
                ),
            ),
            (
                "childConfigurations".into(),
                Value::Array(
                    update
                        .child_configurations
                        .iter()
                        .map(|c| c.to_value())
                        .collect(),
                ),
            ),
        ]
        .into_iter()
        .collect(),
    ))
}
#[test]
fn complete_source_guided_transition_controls() {
    let mut accepted = 0;
    for row in rows() {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let out = calculate(&row["input"]);
        assert_eq!(
            out.is_some(),
            row["accepted"] == Value::Boolean(true),
            "{:?}",
            row["name"]
        );
        if let Some(out) = out {
            accepted += 1;
            assert_eq!(out, row["output"], "{:?}", row["name"]);
        }
    }
    assert_eq!(accepted, 20);
}
#[test]
fn repeated_update_rebuilds_children_but_preserves_equal_membership() {
    for row in rows() {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        if row["accepted"] != Value::Boolean(true) {
            continue;
        }
        let Value::Dictionary(f) = &row["input"] else {
            panic!()
        };
        let c = PreviewOverridesConfiguration::decode(&f["configuration"]).unwrap();
        let Value::Dictionary(expected) = &row["output"] else {
            panic!()
        };
        let Value::Array(a) = &expected["selection"] else {
            panic!()
        };
        let selection: VariantIdSet = a
            .iter()
            .map(|v| {
                if let Value::String(s) = v {
                    s.clone()
                } else {
                    panic!()
                }
            })
            .collect();
        // Same requested IDs, new child rows every time; once settled no state write.
        let Value::Array(requested) = &f["requestedSelection"] else {
            panic!()
        };
        let requested: VariantIdSet = requested
            .iter()
            .map(|v| {
                if let Value::String(s) = v {
                    s.clone()
                } else {
                    panic!()
                }
            })
            .collect();
        let mut state = VariantGroupSettings {
            is_enabled: false,
            selection,
        };
        let before: Vec<String> = state.selection.iter().map(str::to_owned).collect();
        let update = state.update_multi_selection(&c, requested);
        assert!(!update.selection_changed);
        assert!(!state.is_enabled);
        assert_eq!(
            before,
            state
                .selection
                .iter()
                .map(str::to_owned)
                .collect::<Vec<_>>()
        );
        assert_eq!(
            Value::Array(
                update
                    .child_configurations
                    .iter()
                    .map(|c| c.to_value())
                    .collect()
            ),
            expected["childConfigurations"]
        );
    }
}
#[test]
fn cli_transition_report_and_bounded_summary() {
    for row in rows() {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let input = binary_plist_writer::encode(&row["input"]).unwrap();
        for canonical in [false, true] {
            let mut cmd = Command::new(env!("CARGO_BIN_EXE_inspect-content-result"));
            if canonical {
                cmd.arg("--canonical");
            }
            let mut child = cmd
                .args(["update-multi-selection", "-"])
                .stdin(Stdio::piped())
                .stdout(Stdio::piped())
                .stderr(Stdio::piped())
                .spawn()
                .unwrap();
            child.stdin.take().unwrap().write_all(&input).unwrap();
            let out = child.wait_with_output().unwrap();
            assert_eq!(
                out.status.success(),
                row["accepted"] == Value::Boolean(true)
            );
            if out.status.success() {
                if canonical {
                    assert_eq!(
                        binary_plist::decode(&out.stdout).unwrap(),
                        row["output"],
                        "{:?}",
                        row["name"]
                    );
                } else {
                    let s = String::from_utf8(out.stdout).unwrap();
                    assert!(s.starts_with("result=update-multi-selection\n"));
                    assert!(s.len() < 18000);
                    if row["name"] == Value::String("long-many".into()) {
                        assert!(s.contains("Truncated=true"));
                        assert!(s.contains("childConfigurations=6\n"));
                        assert!(s.contains("childConfigurationsShown=4"));
                        assert!(s.contains("selectionShown=8"));
                    }
                }
            } else {
                assert!(out.stdout.is_empty());
            }
        }
    }
}
