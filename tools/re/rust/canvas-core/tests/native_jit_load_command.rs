use canvas_core::{
    binary_plist,
    jit_load_command::{JitLoadCommand as Command, LoadDylib},
    payload_codec::Value,
};
#[test]
fn native_jit_values_roundtrip_and_reject() {
    let Value::Dictionary(f) = binary_plist::decode(include_bytes!(
        "fixtures/native_jit_load_command/native.bplist"
    ))
    .unwrap() else {
        panic!()
    };
    let Value::Array(rows) = &f["rows"] else {
        panic!()
    };
    assert_eq!(rows.len(), 65);
    let mut accepted = 0;
    for row in rows {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let Value::String(kind) = &row["kind"] else {
            panic!()
        };
        let result = match kind.as_str() {
            "jit-load-command" => Command::decode(&row["input"]).map(|v| v.to_value()),
            "jit-load-dylib" => LoadDylib::decode(&row["input"]).map(|v| v.to_value()),
            _ => panic!(),
        };
        assert_eq!(result.is_ok(), row["accepted"] == Value::Boolean(true));
        if let Ok(v) = result {
            accepted += 1;
            assert_eq!(v, row["canonical"]);
        }
    }
    assert_eq!(accepted, 17);
}
#[test]
fn jit_types_require_dictionary() {
    let v = Value::Array(vec![]);
    assert!(Command::decode(&v).is_err());
    assert!(LoadDylib::decode(&v).is_err());
}
