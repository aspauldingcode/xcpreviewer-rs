use canvas_core::{
    binary_plist,
    built_artifact::{
        BuiltObjectFileDescription as Object, BuiltStaticArchiveDescription as Archive,
        PlatformVersion, SourceFilePaths,
    },
    payload_codec::Value,
};
fn ordered(mut value: Value) -> Value {
    if let Value::Dictionary(f) = &mut value {
        if let Some(Value::Array(a)) = f.get_mut("sourceFilePaths") {
            a.sort_by(|a, b| match (a, b) {
                (Value::String(a), Value::String(b)) => a.cmp(b),
                _ => panic!(),
            });
        }
    }
    value
}
#[test]
fn native_artifact_roundtrips_and_errors() {
    let Value::Dictionary(f) = binary_plist::decode(include_bytes!(
        "fixtures/native_built_artifact/native.bplist"
    ))
    .unwrap() else {
        panic!()
    };
    let Value::Array(rows) = &f["rows"] else {
        panic!()
    };
    assert_eq!(rows.len(), 90);
    let mut accepted = 0;
    for row in rows {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let Value::String(kind) = &row["kind"] else {
            panic!()
        };
        let result = match kind.as_str() {
            "built-object-file" => Object::decode(&row["input"]).map(|v| v.to_value()),
            "built-static-archive" => Archive::decode(&row["input"]).map(|v| v.to_value()),
            "platform-version" => PlatformVersion::decode(&row["input"]).map(|v| v.to_value()),
            _ => panic!(),
        };
        assert_eq!(result.is_ok(), row["accepted"] == Value::Boolean(true));
        if let Ok(v) = result {
            accepted += 1;
            assert_eq!(ordered(v), ordered(row["canonical"].clone()));
        }
    }
    assert_eq!(accepted, 35);
}
#[test]
fn source_set_uses_first_canonical_unicode_spelling() {
    for (input, expected) in [
        (vec!["é", "e\u{301}", "a"], vec!["a", "é"]),
        (vec!["e\u{301}", "é"], vec!["e\u{301}"]),
    ] {
        let paths = SourceFilePaths::new(input.into_iter().map(str::to_owned));
        assert_eq!(paths.paths().collect::<Vec<_>>(), expected);
    }
    assert!(SourceFilePaths::default().is_empty());
}
#[test]
fn artifact_types_require_dictionary() {
    let v = Value::Array(vec![]);
    assert!(Object::decode(&v).is_err());
    assert!(Archive::decode(&v).is_err());
    assert!(PlatformVersion::decode(&v).is_err());
}
