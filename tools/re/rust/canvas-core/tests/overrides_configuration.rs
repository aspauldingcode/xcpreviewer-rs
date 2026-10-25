use canvas_core::{
    binary_plist, binary_plist_writer,
    overrides_configuration::{
        ChildConfigurations, Error, PreviewOverridesConfiguration as Config,
    },
    payload_codec::Value,
    selection_behavior,
};
use std::{
    collections::BTreeMap,
    io::Write,
    process::{Command, Stdio},
};
fn text(v: &str) -> Value {
    Value::String(v.into())
}
fn dict(v: &[(&str, Value)]) -> Value {
    Value::Dictionary(
        v.iter()
            .map(|(k, v)| (k.to_string(), v.clone()))
            .collect::<BTreeMap<_, _>>(),
    )
}
fn rows() -> Vec<Value> {
    let Value::Array(v) = binary_plist::decode(include_bytes!(
        "fixtures/overrides_configuration/native.bplist"
    ))
    .unwrap() else {
        panic!()
    };
    v
}
fn bare() -> Value {
    let Value::Dictionary(row) = rows().remove(0) else {
        panic!()
    };
    row["input"].clone()
}
fn children(input: Value) -> Value {
    let Value::Dictionary(mut root) = bare() else {
        panic!()
    };
    root.insert("childVariantConfigurations".into(), input);
    Value::Dictionary(root)
}
#[test]
fn complete_native_tree_compositions_and_canonical_defaults() {
    let mut accepts = 0;
    for row in rows() {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let decoded = Config::decode(&row["input"]);
        assert_eq!(
            decoded.is_ok(),
            row["accepted"] == Value::Boolean(true),
            "{:?}",
            row["name"]
        );
        if let Ok(value) = decoded {
            accepts += 1;
            assert_eq!(value.to_value(), row["output"]);
            assert_eq!(Config::decode(&value.to_value()), Ok(value));
        }
    }
    assert_eq!(accepts, 13);
}
#[test]
fn typed_map_canonical_lookup_replaces_value_keeps_first_key() {
    let first = Config::decode(&bare()).unwrap();
    let mut last = first.clone();
    last.title = "Last".into();
    let mut map = ChildConfigurations::new();
    assert!(map.insert("e\u{301}".into(), first.clone()).is_none());
    assert_eq!(map.insert("é".into(), last.clone()), Some(first));
    assert_eq!(map.len(), 1);
    assert_eq!(map.get("é"), Some(&last));
    assert_eq!(
        map.iter().next().unwrap().0.as_bytes(),
        "e\u{301}".as_bytes()
    );
    let mut alternate = ChildConfigurations::new();
    alternate.insert("é".into(), last);
    assert_eq!(map, alternate);
}
#[test]
fn error_order_recursive_failure_and_explicit_raw_domain_boundary() {
    assert_eq!(Config::decode(&dict(&[])), Err(Error::Missing("title")));
    assert_eq!(
        Config::decode(&dict(&[("title", text("x"))])),
        Err(Error::Missing("selectionBehavior"))
    );
    assert_eq!(
        Config::decode(&dict(&[
            ("title", text("x")),
            ("selectionBehavior", dict(&[]))
        ])),
        Err(Error::Selection(selection_behavior::Error::Missing(
            "discriminant"
        )))
    );
    assert_eq!(
        Config::decode(&children(dict(&[("id", dict(&[]))]))),
        Err(Error::Child {
            index: 0,
            cause: Box::new(Error::Missing("title"))
        })
    );
    assert_eq!(
        Config::decode(&children(dict(&[("é", bare()), ("e\u{301}", bare())]))),
        Err(Error::CanonicalKeyCollision)
    );
    // Beyond the binary parser's structural depth: bound direct Value callers too.
    let mut deep = bare();
    for _ in 0..66 {
        deep = children(dict(&[("id", deep)]));
    }
    let mut error = Config::decode(&deep).unwrap_err();
    while let Error::Child { cause, .. } = error {
        error = *cause;
    }
    assert_eq!(error, Error::Depth);
}
#[test]
fn explicit_cli_complete_tree_bounded_nonrecursive_summary() {
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
                .args(["overrides-configuration", "-"])
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
                    assert!(s.starts_with("result=overrides-configuration\n"));
                    assert!(s.len() < 8000);
                    if row["name"] == text("long") {
                        assert!(s.contains("titleTruncated=true"));
                        assert!(s.contains("child0.idTruncated=true"));
                    }
                    if row["name"] == text("many") {
                        assert!(s.contains("children=6"));
                        assert!(s.contains("childrenShown=4"));
                        assert!(s.contains("variantsShown=4"));
                    }
                }
            } else {
                assert!(out.stdout.is_empty());
            }
        }
    }
}
