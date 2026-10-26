use canvas_core::{
    binary_plist, binary_plist_writer,
    content_results::PreviewVariant,
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
        binary_plist::decode(include_bytes!("fixtures/request_projection/native.bplist")).unwrap()
    else {
        panic!()
    };
    v
}
#[derive(Clone, Debug)]
struct Inputs {
    groups: Vec<PreviewVariantGroup>,
    settings: OverrideSettings,
    grid: Option<PreviewVariantGroup>,
    mode: String,
    host: canvas_core::request_projection::HostLocation,
    caps: canvas_core::request_projection::Capabilities,
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
    use canvas_core::request_projection::{Capabilities, HostLocation};
    let Value::Dictionary(m) = f.get("mode")? else {
        return None;
    };
    let Value::String(mode) = m.get("discriminant")? else {
        return None;
    };
    let grid = if mode == "grid" {
        Some(PreviewVariantGroup::decode(m.get("group")?).ok()?)
    } else {
        None
    };
    let host = match mode.as_str() {
        "live" => match m.get("hostLocation")? {
            Value::String(s) if s == "inCanvas" => HostLocation::InCanvas,
            Value::String(s) if s == "external" => HostLocation::External,
            _ => return None,
        },
        "grid" | "static" => HostLocation::InCanvas,
        _ => return None,
    };
    let Value::Dictionary(c) = f.get("capabilities")? else {
        return None;
    };
    let (Some(Value::Boolean(continuous)), Some(Value::Boolean(statics))) = (
        c.get("supportsContinuousLivePreview"),
        c.get("supportsStaticPreviews"),
    ) else {
        return None;
    };
    Some(Inputs {
        groups,
        settings,
        grid,
        mode: mode.clone(),
        host,
        caps: Capabilities {
            supports_continuous_live_preview: *continuous,
            supports_static_previews: *statics,
        },
    })
}
fn projections(config: &Inputs) -> Vec<canvas_core::request_projection::RequestProjection> {
    use canvas_core::request_projection::{admitted_request_projections, CanvasMode};
    let mode = match config.mode.as_str() {
        "live" => CanvasMode::Live(config.host),
        "grid" => CanvasMode::Grid(config.grid.as_ref().unwrap()),
        _ => CanvasMode::Static,
    };
    admitted_request_projections(&config.groups, &config.settings, mode, config.caps)
}
fn output(config: &Inputs) -> Value {
    use canvas_core::request_projection::DisplayMode;
    Value::Array(
        projections(config)
            .iter()
            .map(|p| {
                let mut display = std::collections::BTreeMap::new();
                match p.display_mode {
                    DisplayMode::Interactive(value) => {
                        display.insert("discriminant".into(), Value::String("interactive".into()));
                        display.insert("value".into(), Value::Boolean(value));
                    }
                    DisplayMode::Static => {
                        display.insert("discriminant".into(), Value::String("static".into()));
                    }
                }
                let mut fields: std::collections::BTreeMap<String, Value> = [
                    ("displayMode".into(), Value::Dictionary(display)),
                    (
                        "overrides".into(),
                        Value::Array(p.overrides.iter().map(PreviewVariant::to_value).collect()),
                    ),
                ]
                .into_iter()
                .collect();
                if let Some(v) = &p.variant {
                    fields.insert("variant".into(), v.to_value());
                }
                Value::Dictionary(fields)
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
    assert_eq!(accepted, 28);
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
            let mut requests = projections(&config);
            for request in &mut requests {
                if let Some(variant) = &mut request.variant {
                    variant.id = "result-only-mutation".into();
                }
                for variant in &mut request.overrides {
                    variant.id = "owned-override-mutation".into();
                }
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
                .args(["request-projections", "-"])
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
                    assert!(s.starts_with("result=request-projections\n"));
                    assert!(s.len() < 16000);
                    if row["name"] == Value::String("long-many".into()) {
                        assert!(s.contains("request1.variantTruncated=true"));
                        assert!(s.contains("requests=14\n"));
                        assert!(s.contains("requestsShown=8"));
                    }
                }
            } else {
                assert!(out.stdout.is_empty());
            }
        }
    }
}
