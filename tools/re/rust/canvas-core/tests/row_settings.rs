use canvas_core::{
    binary_plist, binary_plist_writer,
    effective_overrides::{OverrideSettings, VariantGroupSettings},
    payload_codec::Value,
    variants_reply::PreviewVariantGroup,
};
use std::{
    io::Write,
    process::{Command, Stdio},
};
fn rows() -> Vec<Value> {
    let Value::Array(v) =
        binary_plist::decode(include_bytes!("fixtures/row_settings/native.bplist")).unwrap()
    else {
        panic!()
    };
    v
}
#[derive(Clone, Debug)]
struct Inputs {
    groups: Vec<PreviewVariantGroup>,
    settings: OverrideSettings,
    grid: Option<String>,
}
fn decode(v: &Value) -> Option<Inputs> {
    let Value::Dictionary(f) = v else {
        return None;
    };
    let Value::Array(groups) = f.get("groups")? else {
        return None;
    };
    let groups = groups
        .iter()
        .map(PreviewVariantGroup::decode)
        .collect::<Result<Vec<_>, _>>()
        .ok()?;
    let Value::Array(rows) = f.get("settings")? else {
        return None;
    };
    let mut settings = OverrideSettings::new();
    for row in rows {
        let Value::Dictionary(row) = row else {
            return None;
        };
        let (Some(Value::String(id)), Some(Value::Boolean(enabled)), Some(Value::Array(ids))) = (
            row.get("groupID"),
            row.get("isEnabled"),
            row.get("selection"),
        ) else {
            return None;
        };
        let selection = ids
            .iter()
            .map(|v| match v {
                Value::String(id) => Some(id.clone()),
                _ => None,
            })
            .collect::<Option<canvas_core::variant_id_set::VariantIdSet>>()?;
        settings.insert(
            id.clone(),
            VariantGroupSettings {
                is_enabled: *enabled,
                selection,
            },
        );
    }
    let grid = match f.get("gridGroupID") {
        None => None,
        Some(Value::String(id)) => Some(id.clone()),
        _ => return None,
    };
    Some(Inputs {
        groups,
        settings,
        grid,
    })
}
fn output(config: &Inputs) -> Value {
    Value::Array(
        config
            .groups
            .iter()
            .map(|group| {
                let state = config.settings.row_settings(group);
                Value::Dictionary(
                    [
                        ("groupID".into(), Value::String(group.id.clone())),
                        (
                            "isStored".into(),
                            Value::Boolean(config.settings.get(&group.id).is_some()),
                        ),
                        ("isEnabled".into(), Value::Boolean(state.is_enabled)),
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
                    ]
                    .into_iter()
                    .collect(),
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
        let config = decode(&row["input"]);
        assert_eq!(config.is_some(), row["accepted"] == Value::Boolean(true));
        if let Some(config) = config {
            accepted += 1;
            assert_eq!(output(&config), row["output"], "{:?}", row["name"]);
        }
    }
    assert_eq!(accepted, 18);
}
#[test]
fn row_reads_do_not_install_defaults_and_return_owned_selection() {
    for row in rows() {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        if let Some(config) = decode(&row["input"]) {
            let before = format!("{config:?}");
            let expected = output(&config);
            for group in &config.groups {
                let mut state = config.settings.row_settings(group);
                state.selection.insert("local-mutation-only".into());
                state.is_enabled = !state.is_enabled;
            }
            assert_eq!(format!("{config:?}"), before);
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
                .args(["row-settings", "-"])
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
                    assert!(s.starts_with("result=row-settings\n"));
                    assert!(s.len() < 16000);
                    if row["name"] == Value::String("long-many".into()) {
                        assert!(s.contains("row0.selected0Truncated=true"));
                        assert!(s.contains("rows=6\n"));
                        assert!(s.contains("rowsShown=4"));
                        assert!(s.contains("row0.selection=13\n"));
                        assert!(s.contains("row0.selectionShown=8"));
                    }
                }
            } else {
                assert!(out.stdout.is_empty());
            }
        }
    }
}
