use canvas_core::{
    binary_plist, binary_plist_writer, overrides_configuration,
    payload_codec::Value,
    variants_reply::{Error, PreviewVariantGroup as Group, PreviewVariantsPayload as Reply},
};
use std::{
    collections::BTreeMap,
    io::Write,
    process::{Command, Stdio},
};
fn text(s: &str) -> Value {
    Value::String(s.into())
}
fn dict(f: &[(&str, Value)]) -> Value {
    Value::Dictionary(
        f.iter()
            .map(|(k, v)| (k.to_string(), v.clone()))
            .collect::<BTreeMap<_, _>>(),
    )
}
fn rows() -> Vec<Value> {
    let Value::Array(v) =
        binary_plist::decode(include_bytes!("fixtures/variants_reply/native.bplist")).unwrap()
    else {
        panic!()
    };
    v
}
#[test]
fn complete_source_guided_group_and_reply_controls() {
    let mut accepted = 0;
    for row in rows() {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let result = if row["kind"] == text("group") {
            Group::decode(&row["input"]).map(|v| {
                assert_eq!(Group::decode(&v.to_value()), Ok(v.clone()));
                v.to_value()
            })
        } else {
            Reply::decode(&row["input"]).map(|v| {
                assert_eq!(Reply::decode(&v.to_value()), Ok(v.clone()));
                v.to_value()
            })
        };
        assert_eq!(
            result.is_ok(),
            row["accepted"] == Value::Boolean(true),
            "{:?}",
            row["name"]
        );
        if let Ok(value) = result {
            accepted += 1;
            assert_eq!(value, row["output"]);
        }
    }
    assert_eq!(accepted, 16);
}
#[test]
fn validation_order_and_nested_group_indexes() {
    assert_eq!(Reply::decode(&dict(&[])), Err(Error::Missing("groups")));
    assert_eq!(Group::decode(&dict(&[])), Err(Error::Missing("id")));
    assert_eq!(
        Group::decode(&dict(&[
            ("id", text("id")),
            (
                "associatedGroupIDsArray",
                Value::Array(vec![text("id"), Value::Boolean(true)])
            ),
            ("overridesConfiguration", Value::Boolean(true))
        ])),
        Err(Error::AssociatedId { index: 1 })
    );
    assert_eq!(
        Group::decode(&dict(&[
            ("id", text("id")),
            ("overridesConfiguration", Value::Boolean(true)),
            ("variantsConfiguration", Value::Boolean(true))
        ])),
        Err(Error::Overrides(overrides_configuration::Error::Type(
            "dictionary"
        )))
    );
    assert_eq!(
        Reply::decode(&dict(&[(
            "groups",
            Value::Array(vec![dict(&[("id", text("ok"))]), Value::Boolean(true)])
        )])),
        Err(Error::Group {
            index: 1,
            cause: Box::new(Error::Type("dictionary"))
        })
    );
}
#[test]
fn references_are_opaque_sets_and_raw_child_boundary_propagates() {
    let input = dict(&[
        ("id", text("self")),
        (
            "associatedGroupIDsArray",
            Value::Array(vec![
                text("self"),
                text("missing"),
                text("e\u{301}"),
                text("é"),
            ]),
        ),
    ]);
    let group = Group::decode(&input).unwrap();
    assert_eq!(group.associated_group_ids.len(), 3);
    assert!(group.associated_group_ids.contains("é"));
    assert!(group.associated_group_ids.contains("missing"));
    let Value::Dictionary(row) = rows()
        .into_iter()
        .find(|r| matches!(r,Value::Dictionary(f) if f["name"]==text("both")))
        .unwrap()
    else {
        panic!()
    };
    let Value::Dictionary(mut group) = row["input"].clone() else {
        panic!()
    };
    let Value::Dictionary(mut config) = group["overridesConfiguration"].clone() else {
        panic!()
    };
    let child = config.clone();
    config.insert(
        "childVariantConfigurations".into(),
        dict(&[
            ("é", Value::Dictionary(child.clone())),
            ("e\u{301}", Value::Dictionary(child)),
        ]),
    );
    group.insert("overridesConfiguration".into(), Value::Dictionary(config));
    assert_eq!(
        Group::decode(&Value::Dictionary(group)),
        Err(Error::Overrides(
            overrides_configuration::Error::CanonicalKeyCollision
        ))
    );
}
#[test]
fn cli_complete_payload_and_bounded_group_summaries() {
    for row in rows() {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let bytes = binary_plist_writer::encode(&row["input"]).unwrap();
        let Value::String(kind) = &row["kind"] else {
            panic!()
        };
        for canonical in [false, true] {
            let mut command = Command::new(env!("CARGO_BIN_EXE_inspect-content-result"));
            if canonical {
                command.arg("--canonical");
            }
            let mut child = command
                .args([kind.as_str(), "-"])
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
                    assert!(s.starts_with(&format!("result={kind}\n")));
                    assert!(s.len() < 16000);
                    if row["name"] == text("long-id") {
                        assert!(s.contains("group.idTruncated=true"));
                    }
                    if row["name"] == text("many-groups") {
                        assert!(s.contains("groups=6"));
                        assert!(s.contains("groupsShown=4"));
                    }
                    if row["name"] == text("many-associations") {
                        assert!(s.contains("associatedGroupIDs=12"));
                        assert!(s.contains("associatedGroupIDsShown=4"));
                    }
                }
            } else {
                assert!(out.stdout.is_empty());
            }
        }
    }
}
