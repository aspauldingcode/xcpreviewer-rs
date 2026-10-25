use canvas_core::{
    binary_plist, binary_plist_writer,
    content_results::PreviewVariant,
    effective_overrides::{self, OverrideSettings, VariantGroupSettings},
    payload_codec::Value,
    variants_reply::PreviewVariantGroup,
};
use std::{
    io::Write,
    process::{Command, Stdio},
};
fn rows() -> Vec<Value> {
    let Value::Array(v) =
        binary_plist::decode(include_bytes!("fixtures/effective_overrides/native.bplist")).unwrap()
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
        effective_overrides::effective_groups_and_overrides(
            &config.groups,
            &config.settings,
            config.grid.as_deref(),
        )
        .iter()
        .map(|e| {
            Value::Dictionary(
                [
                    ("group".into(), e.group.to_value()),
                    (
                        "overrides".into(),
                        Value::Array(e.overrides.iter().map(PreviewVariant::to_value).collect()),
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
fn resolution_preserves_inputs_and_returns_owned_overrides() {
    for row in rows() {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        if let Some(config) = decode(&row["input"]) {
            let before = format!("{config:?}");
            let expected = output(&config);
            let mut effects = effective_overrides::effective_groups_and_overrides(
                &config.groups,
                &config.settings,
                config.grid.as_deref(),
            );
            if let Some(first) = effects.iter_mut().flat_map(|e| &mut e.overrides).next() {
                first.id = "result-only-mutation".into();
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
                .args(["effective-overrides", "-"])
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
                    assert!(s.starts_with("result=effective-overrides\n"));
                    assert!(s.len() < 16000);
                    if row["name"] == Value::String("long-many".into()) {
                        assert!(s.contains("group0.override0Truncated=true"));
                        assert!(s.contains("groups=6\n"));
                        assert!(s.contains("groupsShown=4"));
                        assert!(s.contains("group0.overrides=13\n"));
                        assert!(s.contains("group0.overridesShown=8"));
                    }
                }
            } else {
                assert!(out.stdout.is_empty());
            }
        }
    }
}
