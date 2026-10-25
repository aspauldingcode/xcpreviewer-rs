use canvas_core::{
    binary_plist, binary_plist_writer,
    content_results::{ContentOverridePayload, Error, PreviewVariant},
    payload_codec::Value,
};
use std::{
    collections::BTreeMap,
    io::Write,
    process::{Command, Output, Stdio},
};
fn rows() -> Vec<Value> {
    let Value::Array(rows) =
        binary_plist::decode(include_bytes!("fixtures/content_results/native.bplist")).unwrap()
    else {
        panic!()
    };
    rows
}
fn invoke(args: &[&str], bytes: &[u8]) -> Output {
    let mut child = Command::new(env!("CARGO_BIN_EXE_inspect-content-result"))
        .args(args)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    child.stdin.take().unwrap().write_all(bytes).unwrap();
    child.wait_with_output().unwrap()
}
fn value(fields: Vec<(&str, Value)>) -> Value {
    Value::Dictionary(
        fields
            .into_iter()
            .map(|(k, v)| (k.into(), v))
            .collect::<BTreeMap<_, _>>(),
    )
}
#[test]
fn full_foundation_controls_and_canonical_roundtrips_match() {
    let rows = rows();
    assert_eq!(rows.len(), 29);
    let mut accepted = 0;
    for row in rows {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let Value::String(kind) = &row["kind"] else {
            panic!()
        };
        let normalized = if kind == "variant" {
            PreviewVariant::decode(&row["input"]).map(|value| value.to_value())
        } else {
            ContentOverridePayload::decode(&row["input"]).map(|value| value.to_value())
        };
        assert_eq!(
            normalized.is_ok(),
            row["accepted"] == Value::Boolean(true),
            "{:?}",
            row["name"]
        );
        if let Ok(normalized) = normalized {
            accepted += 1;
            assert_eq!(normalized, row["output"], "{:?}", row["name"]);
            let redecoded =
                binary_plist::decode(&binary_plist_writer::encode(&normalized).unwrap()).unwrap();
            let again = if kind == "variant" {
                PreviewVariant::decode(&redecoded).map(|value| value.to_value())
            } else {
                ContentOverridePayload::decode(&redecoded).map(|value| value.to_value())
            };
            assert_eq!(again.unwrap(), normalized);
        }
    }
    assert_eq!(accepted, 16);
}
#[test]
fn modern_presence_and_missing_compatibility_effect_remain_distinct() {
    assert_eq!(
        PreviewVariant::decode(&value(vec![])),
        Err(Error::Missing("renderEffect"))
    );
    let empty = value(vec![
        ("renderEffects", Value::Array(vec![])),
        ("id", Value::String("v".into())),
        ("displayName", Value::String("V".into())),
        ("renderEffect", Value::Integer(7)),
    ]);
    let decoded = PreviewVariant::decode(&empty).unwrap();
    assert!(decoded.render_effects.is_empty());
    let Value::Dictionary(canonical) = decoded.to_value() else {
        panic!()
    };
    assert_eq!(
        canonical["renderEffect"],
        value(vec![("id", Value::String("Missing".into()))])
    );
    assert_eq!(
        ContentOverridePayload::decode(&value(vec![]))
            .unwrap()
            .content_override,
        None
    );
    assert_eq!(
        ContentOverridePayload::decode(&value(vec![(
            "contentOverride",
            Value::String(String::new())
        )]))
        .unwrap()
        .content_override,
        Some(String::new())
    );
}
#[test]
fn cli_summaries_escape_controls_and_cap_effect_list() {
    for row in rows() {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let Value::String(kind) = &row["kind"] else {
            panic!()
        };
        let bytes = binary_plist_writer::encode(&row["input"]).unwrap();
        let out = invoke(&["--canonical", kind, "-"], &bytes);
        assert_eq!(
            out.status.success(),
            row["accepted"] == Value::Boolean(true)
        );
        if row["accepted"] == Value::Boolean(true) {
            assert!(out.stderr.is_empty());
            assert_eq!(binary_plist::decode(&out.stdout).unwrap(), row["output"]);
            let out = invoke(&[kind, "-"], &bytes);
            assert!(out.status.success());
            let summary = String::from_utf8(out.stdout).unwrap();
            assert!(summary.starts_with(&format!("result={kind}\n")));
            assert!(!summary.contains('\0'));
            assert!(summary.len() < 8192);
            if row["name"] == Value::String("long-effects".into()) {
                assert!(summary.contains("renderEffects=12\n"));
                assert!(summary.contains("renderEffectsShown=8\n"));
                assert!(!summary.contains("effect8="));
            }
        } else {
            assert!(out.stdout.is_empty());
            assert!(!out.stderr.is_empty());
        }
    }
}
#[test]
fn cli_argument_file_stdin_and_size_boundaries() {
    for args in [
        vec![],
        vec!["groups", "-"],
        vec!["variant"],
        vec!["--canonical", "override"],
        vec!["override", "-", "extra"],
    ] {
        let out = invoke(&args, &[]);
        assert!(!out.status.success());
        assert!(out.stdout.is_empty());
        assert!(String::from_utf8(out.stderr).unwrap().contains("usage:"));
    }
    let bytes = binary_plist_writer::encode(&value(vec![])).unwrap();
    let path = std::env::temp_dir().join(format!("content-result-{}.bplist", std::process::id()));
    std::fs::write(&path, &bytes).unwrap();
    let out = invoke(&["override", path.to_str().unwrap()], &[]);
    std::fs::remove_file(path).unwrap();
    assert!(out.status.success());
    assert_eq!(out.stdout, invoke(&["override", "-"], &bytes).stdout);
    let out = invoke(
        &["--canonical", "override", "-"],
        &vec![0; 64 * 1024 * 1024 + 1],
    );
    assert!(!out.status.success());
    assert!(out.stdout.is_empty());
    assert_eq!(out.stderr, b"input exceeds 64 MiB\n");
}
