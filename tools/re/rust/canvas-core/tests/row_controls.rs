use canvas_core::{
    binary_plist, binary_plist_writer,
    effective_overrides::{OverrideSettings, VariantGroupSettings},
    payload_codec::Value,
    variant_id_set::VariantIdSet,
    variants_reply::PreviewVariantGroup,
};
use std::{
    io::Write,
    process::{Command, Stdio},
};
fn rows() -> Vec<Value> {
    let Value::Array(rows) =
        binary_plist::decode(include_bytes!("fixtures/row_controls/native.bplist")).unwrap()
    else {
        panic!()
    };
    rows
}
fn decode(v: &Value) -> Option<(PreviewVariantGroup, OverrideSettings, Option<bool>)> {
    let Value::Dictionary(f) = v else {
        return None;
    };
    let group = PreviewVariantGroup::decode(f.get("group")?).ok()?;
    let mut settings = OverrideSettings::new();
    if let Some(v) = f.get("settings") {
        let Value::Dictionary(f) = v else {
            return None;
        };
        let (Some(Value::Boolean(enabled)), Some(Value::Array(ids))) =
            (f.get("isEnabled"), f.get("selection"))
        else {
            return None;
        };
        let selection = ids
            .iter()
            .map(|v| {
                if let Value::String(id) = v {
                    Some(id.clone())
                } else {
                    None
                }
            })
            .collect::<Option<VariantIdSet>>()?;
        settings.insert(
            group.id.clone(),
            VariantGroupSettings {
                is_enabled: *enabled,
                selection,
            },
        );
    }
    let requested = match f.get("requestedEnabled") {
        None => None,
        Some(Value::Boolean(v)) => Some(*v),
        _ => return None,
    };
    Some((group, settings, requested))
}
fn report(g: &PreviewVariantGroup, s: &OverrideSettings, requested: Option<bool>) -> Value {
    let state = s.row_settings(g);
    let read = g
        .overrides_configuration
        .as_ref()
        .and_then(|c| state.single_selection_candidates(c));
    let mut out = std::collections::BTreeMap::from([
        ("isStored".into(), Value::Boolean(s.get(&g.id).is_some())),
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
        (
            "enableWriteRequested".into(),
            Value::Boolean(requested.is_some()),
        ),
        (
            "singleSelectionAvailable".into(),
            Value::Boolean(read.is_some()),
        ),
    ]);
    if let Some(read) = read {
        out.insert("usesDefaults".into(), Value::Boolean(read.uses_defaults));
        out.insert(
            "portableValue".into(),
            Value::String(read.portable_value().unwrap().into()),
        );
        out.insert(
            "candidates".into(),
            Value::Array(
                read.candidates
                    .iter()
                    .map(|id| Value::String(id.into()))
                    .collect(),
            ),
        );
    }
    Value::Dictionary(out)
}
#[test]
fn complete_source_guided_control_compositions() {
    let mut accepted = 0;
    for row in rows() {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let inputs = decode(&row["input"]);
        assert_eq!(
            inputs.is_some(),
            row["accepted"] == Value::Boolean(true),
            "{:?}",
            row["name"]
        );
        if let Some((g, mut s, requested)) = inputs {
            accepted += 1;
            if let Some(enabled) = requested {
                s.set_row_enabled(&g, enabled);
            }
            assert_eq!(
                report(&g, &s, requested),
                row["output"],
                "{:?}",
                row["name"]
            );
        }
    }
    assert_eq!(accepted, 20);
}
#[test]
fn reads_do_not_install_and_writes_preserve_selection() {
    for row in rows() {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        if let Some((g, mut s, _)) = decode(&row["input"]) {
            let before = format!("{s:?}");
            let group_before = g.to_value();
            let state = s.row_settings(&g);
            let old: Vec<String> = state.selection.iter().map(str::to_owned).collect();
            let _ = report(&g, &s, None);
            assert_eq!(before, format!("{s:?}"));
            s.set_row_enabled(&g, false);
            let state = s.get(&g.id).unwrap();
            assert!(!state.is_enabled);
            assert_eq!(
                old,
                state
                    .selection
                    .iter()
                    .map(str::to_owned)
                    .collect::<Vec<_>>()
            );
            s.set_row_enabled(&g, true);
            assert!(s.get(&g.id).unwrap().is_enabled);
            assert_eq!(group_before, g.to_value());
        }
    }
    let mut s = OverrideSettings::new();
    let mut g = PreviewVariantGroup::decode(&Value::Dictionary(
        [("id".into(), Value::String("é".into()))]
            .into_iter()
            .collect(),
    ))
    .unwrap();
    s.insert(
        "e\u{301}".into(),
        VariantGroupSettings {
            is_enabled: false,
            selection: ["stored".into()].into_iter().collect(),
        },
    );
    s.set_row_enabled(&g, true);
    assert_eq!(s.iter().next().unwrap().0, "e\u{301}");
    g.id = "other".into();
    assert!(s.get(&g.id).is_none());
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
                .args(["row-controls", "-"])
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
                    assert!(s.starts_with("result=row-controls\n"));
                    assert!(s.len() < 18000);
                    if row["name"] == Value::String("long-many".into()) {
                        assert!(s.contains("Truncated=true"));
                        assert!(s.contains("candidates=13\n"));
                        assert!(s.contains("candidatesShown=8"));
                        assert!(s.contains("selectionShown=8"));
                    }
                }
            } else {
                assert!(out.stdout.is_empty());
            }
        }
    }
}
