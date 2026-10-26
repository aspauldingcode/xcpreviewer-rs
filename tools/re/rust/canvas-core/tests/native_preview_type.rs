use canvas_core::{
    binary_plist,
    payload_codec::Value,
    preview_type::{Error, HostLocation, PreviewType},
};
use std::collections::BTreeMap;
fn dict(v: &Value) -> &BTreeMap<String, Value> {
    let Value::Dictionary(v) = v else { panic!() };
    v
}
#[test]
fn actual_native_preview_and_location_codec_cases() {
    let fixture =
        binary_plist::decode(include_bytes!("fixtures/native_preview_type/native.bplist")).unwrap();
    let f = dict(&fixture);
    let Value::Array(rows) = &f["rows"] else {
        panic!()
    };
    assert_eq!(rows.len(), 41);
    let mut accepted = 0;
    for row in rows {
        let r = dict(row);
        let input = &r["input"];
        let before = input.clone();
        let result = if r["kind"] == Value::String("preview-type".into()) {
            PreviewType::decode(input).map(|v| v.to_value())
        } else {
            HostLocation::decode(input).map(|v| v.to_value())
        };
        assert_eq!(result.is_ok(), r["accepted"] == Value::Boolean(true));
        if let Ok(value) = result {
            accepted += 1;
            assert_eq!(value, r["canonical"]);
        }
        assert_eq!(*input, before);
    }
    assert_eq!(accepted, 26);
    assert_eq!(f["destroyedEnums"], Value::Integer(26));
    assert_eq!(f["destroyedPlists"], Value::Integer(26));
    assert_eq!(f["releasedErrors"], Value::Integer(15));
}
#[test]
fn owned_active_payload_and_scope_errors() {
    let location = HostLocation::InjectedScene {
        scene_identifier: "e\u{301}\0🧪".into(),
    };
    let source = PreviewType::Hosted(location.clone()).to_value();
    let preview = PreviewType::decode(&source).unwrap();
    drop(source);
    assert_eq!(preview, PreviewType::Hosted(location));
    assert!(matches!(
        PreviewType::decode(&Value::Array(vec![])),
        Err(Error::Dictionary)
    ));
    let value = Value::Dictionary(
        [
            ("discriminant".into(), Value::String("hosted".into())),
            ("hostLocation".into(), Value::Boolean(false)),
        ]
        .into_iter()
        .collect(),
    );
    assert!(
        matches!(PreviewType::decode(&value),Err(Error::HostLocation(e)) if *e==Error::Dictionary)
    );
}
