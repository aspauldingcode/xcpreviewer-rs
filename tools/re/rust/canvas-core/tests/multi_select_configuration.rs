use canvas_core::{
    binary_plist, binary_plist_writer,
    multi_select_configuration::{Error, MultiSelectConfiguration as Config},
    payload_codec::Value,
    variant_id_set::VariantIdSet,
};
use std::{
    collections::BTreeMap,
    io::Write,
    process::{Command, Stdio},
};
fn dict(value: Value) -> Value {
    Value::Dictionary(BTreeMap::from([("defaultVariants".into(), value)]))
}
fn rows() -> Vec<Value> {
    let Value::Array(rows) = binary_plist::decode(include_bytes!(
        "fixtures/multi_select_configuration/native.bplist"
    ))
    .unwrap() else {
        panic!()
    };
    rows
}
#[test]
fn complete_native_set_compositions_round_trip() {
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
            assert_eq!(value.to_value(), row["output"], "{:?}", row["name"]);
            assert_eq!(Config::decode(&value.to_value()), Ok(value));
        }
    }
    assert_eq!(accepts, 17);
}
fn text(hex: &str) -> String {
    hex.split(',')
        .map(|s| char::from_u32(u32::from_str_radix(s, 16).unwrap()).unwrap())
        .collect()
}
#[test]
fn native_qualified_unicode_equality_and_first_spelling() {
    assert_eq!(unicode_normalization::UNICODE_VERSION, (16, 0, 0));
    let mut count = 0;
    // Generated canonical decomposition and class-order pairs also checked by
    // actual native Swift String equality. The fixture is independent runtime evidence.
    for line in include_str!("fixtures/multi_select_configuration/unicode-pairs.tsv").lines() {
        let mut fields = line.split('\t');
        fields.next().unwrap();
        let a = text(fields.next().unwrap());
        let b = text(fields.next().unwrap());
        let mut set = VariantIdSet::new();
        assert!(set.insert(a.clone()));
        assert!(!set.insert(b.clone()));
        assert_eq!(set.len(), 1);
        assert!(set.contains(&b));
        assert_eq!(set.iter().next().unwrap().as_bytes(), a.as_bytes());
        let reverse: VariantIdSet = [b, a].into_iter().collect();
        assert_eq!(set, reverse);
        count += 1;
    }
    assert_eq!(count, 13670);
    for (a, b) in [
        ("ﬀ", "ff"),
        ("Ａ", "A"),
        ("A", "a"),
        ("a\u{5c8}\u{300}", "a\u{300}\u{5c8}"),
        ("a\u{10ef0}\u{300}", "a\u{300}\u{10ef0}"),
    ] {
        let set: VariantIdSet = [a.into(), b.into()].into_iter().collect();
        assert_eq!(set.len(), 2);
    }
}
#[test]
fn required_array_and_complete_validation_with_indexes() {
    assert_eq!(
        Config::decode(&Value::Dictionary(BTreeMap::new())),
        Err(Error::Missing("defaultVariants"))
    );
    assert_eq!(
        Config::decode(&dict(Value::String("id".into()))),
        Err(Error::Type("defaultVariants"))
    );
    assert_eq!(
        Config::decode(&dict(Value::Array(vec![
            Value::String("id".into()),
            Value::String("id".into()),
            Value::Boolean(true)
        ]))),
        Err(Error::Element {
            key: "defaultVariants",
            index: 2
        })
    );
    let empty = Config::decode(&dict(Value::Array(vec![]))).unwrap();
    assert!(empty.default_variants.is_empty());
}
#[test]
fn cli_explicit_mode_complete_output_and_bounded_summary() {
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
                .args(["multi-selection", "-"])
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
                    assert!(s.starts_with("result=multi-selection\n"));
                    assert!(s.len() < 3000);
                    if row["name"] == Value::String("many".into()) {
                        assert!(s.contains("defaultVariants=20"));
                        assert!(s.contains("defaultVariantsShown=8"));
                    }
                    if row["name"] == Value::String("long".into()) {
                        assert!(s.contains("defaultVariant0Truncated=true"));
                    }
                }
            } else {
                assert!(out.stdout.is_empty());
            }
        }
    }
}
