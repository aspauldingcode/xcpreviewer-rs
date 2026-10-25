use canvas_core::{
    binary_plist, binary_plist_writer, content_requests::RequestContentOverridePayload,
    payload_codec::Value,
};
use std::{
    collections::HashMap,
    io::Write,
    process::{Command, Stdio},
};
fn rows() -> Vec<Value> {
    let Value::Array(rows) =
        binary_plist::decode(include_bytes!("fixtures/override_cache_keys/native.bplist")).unwrap()
    else {
        panic!()
    };
    rows
}
fn decode(v: &Value) -> Option<Vec<RequestContentOverridePayload>> {
    let Value::Array(a) = v else {
        return None;
    };
    a.iter()
        .map(|v| {
            let Value::Dictionary(f) = v else {
                return None;
            };
            RequestContentOverridePayload::decode_dictionary(f).ok()
        })
        .collect()
}
fn report(requests: &[RequestContentOverridePayload]) -> Value {
    let mut keys = HashMap::new();
    let indices = requests
        .iter()
        .enumerate()
        .map(|(i, r)| Value::Integer(*keys.entry(r.cache_key()).or_insert(i) as i64))
        .collect();
    Value::Dictionary(
        [
            ("representatives".into(), Value::Array(indices)),
            ("uniqueKeys".into(), Value::Integer(keys.len() as i64)),
        ]
        .into_iter()
        .collect(),
    )
}
#[test]
fn complete_public_hashable_dictionary_comparisons() {
    let mut accepted = 0;
    for row in rows() {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let requests = decode(&row["input"]);
        assert_eq!(requests.is_some(), row["accepted"] == Value::Boolean(true));
        if let Some(requests) = requests {
            accepted += 1;
            assert_eq!(report(&requests), row["output"], "{:?}", row["name"]);
        }
    }
    assert_eq!(accepted, 20);
}
#[test]
fn immutable_keys_preserve_wire_spelling_and_hash_consistency() {
    use std::hash::{Hash, Hasher};
    for row in rows() {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        if let Some(requests) = decode(&row["input"]) {
            let original: Vec<_> = requests.iter().map(|r| r.to_dictionary()).collect();
            let keys: Vec<_> = requests.iter().map(|r| r.cache_key()).collect();
            for a in &keys {
                for b in &keys {
                    if a == b {
                        let mut x = std::collections::hash_map::DefaultHasher::new();
                        let mut y = std::collections::hash_map::DefaultHasher::new();
                        a.hash(&mut x);
                        b.hash(&mut y);
                        assert_eq!(x.finish(), y.finish());
                    }
                }
            }
            assert_eq!(
                original,
                requests
                    .iter()
                    .map(|r| r.to_dictionary())
                    .collect::<Vec<_>>()
            );
        }
    }
    let a = RequestContentOverridePayload {
        content_category: "é".into(),
        requested_overrides: vec!["e\u{301}".into()],
    };
    let b = RequestContentOverridePayload {
        content_category: "e\u{301}".into(),
        requested_overrides: vec!["é".into()],
    };
    assert_ne!(a, b);
    assert_eq!(a.cache_key(), b.cache_key());
    let key = a.cache_key();
    let mut changed = a.clone();
    changed.requested_overrides.push("another".into());
    assert_ne!(key, changed.cache_key());
}
#[test]
fn cli_classes_and_bounded_summary() {
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
                .args(["override-cache-keys", "-"])
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
                    assert!(s.starts_with("result=override-cache-keys\n"));
                    assert!(s.len() < 1000);
                    if row["name"] == Value::String("long-many".into()) {
                        assert!(s.contains("requests=24\n"));
                        assert!(s.contains("uniqueKeys=3\n"));
                        assert!(s.contains("representativesShown=8"));
                        assert!(!s.contains("request8."));
                    }
                }
            } else {
                assert!(out.stdout.is_empty());
            }
        }
    }
}
