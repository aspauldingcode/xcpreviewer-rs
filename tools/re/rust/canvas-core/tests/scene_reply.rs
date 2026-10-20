use canvas_core::{
    action_reply::{ActionReplyGate, ReplyOutcome},
    payload_codec::Value,
    scene_reply::{Error, SceneReply, PAYLOAD},
};
use std::collections::BTreeMap;
const EMPTY: &[u8] = include_bytes!("fixtures/native-scene-reply-empty.bplist");
const STRUCTURED: &[u8] = include_bytes!("fixtures/native-scene-reply-structured.bplist");
#[test]
fn independent_native_wrappers_decode_complete_owned_payloads() {
    let d = SceneReply::from_property_list_data(Some(STRUCTURED)).unwrap();
    assert_eq!(
        d.payload,
        Some(BTreeMap::from([
            ("answer".into(), Value::Integer(42)),
            ("bytes".into(), Value::Data(b"abc".to_vec())),
            (
                "flags".into(),
                Value::Array(vec![Value::Boolean(true), Value::Boolean(false)])
            ),
            (
                "nested".into(),
                Value::Dictionary(BTreeMap::from([(
                    "label".into(),
                    Value::String("owned".into())
                )]))
            ),
        ]))
    );
    assert_eq!(
        SceneReply::from_settings(Some(&d.to_settings())).unwrap(),
        d
    );
}
#[test]
fn absent_and_empty_stay_distinct_through_local_reply_gate() {
    let absent = SceneReply::from_property_list_data(None).unwrap();
    let empty = SceneReply::from_property_list_data(Some(EMPTY)).unwrap();
    assert_ne!(absent, empty);
    assert!(absent.to_settings().is_empty());
    assert_eq!(
        empty.to_settings().get(&PAYLOAD),
        Some(&Value::Dictionary(BTreeMap::new()))
    );
    for value in [absent, empty] {
        let mut gate = ActionReplyGate::default();
        assert_eq!(
            gate.finish(ReplyOutcome::Success(value.clone())).unwrap(),
            ReplyOutcome::Success(value)
        );
        assert!(!gate.can_send_response());
    }
}
#[test]
fn wrong_payload_types_and_corrupt_native_serializations_reject() {
    for value in [
        Value::Null,
        Value::String("wrong".into()),
        Value::Data(vec![]),
    ] {
        assert_eq!(
            SceneReply::from_settings(Some(&BTreeMap::from([(PAYLOAD, value)]))),
            Err(Error::DictionaryRequired)
        );
    }
    for bytes in [
        b"".as_slice(),
        &STRUCTURED[..STRUCTURED.len() - 1],
        b"not a plist".as_slice(),
    ] {
        assert!(matches!(
            SceneReply::from_property_list_data(Some(bytes)),
            Err(Error::PropertyList(_))
        ));
    }
}
