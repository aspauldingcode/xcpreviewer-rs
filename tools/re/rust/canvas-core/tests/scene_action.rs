use canvas_core::{payload_codec::Value, scene_action::*, scene_timing::HostSceneMessage};
use std::collections::BTreeMap;
#[test]
fn native_slot_labels_and_optional_object_fields() {
    assert_eq!(
        (setting_name(0), setting_name(1), setting_name(2)),
        (Some("messageType"), Some("payload"), Some("fenceHandle"))
    );
    for k in [-1, 3, i64::MIN, i64::MAX] {
        assert_eq!(setting_name(k), None);
    }
    let fields = BTreeMap::from([
        (
            0,
            Setting::<u32>::Value(Value::String("future-message".into())),
        ),
        (99, Setting::Value(Value::Null)),
    ]);
    let a = SceneAction::from_settings(Some(&fields)).unwrap();
    assert_eq!(a.payload, None);
    assert_eq!(a.fence, None);
    assert_eq!(a.to_settings().len(), 1);
    assert!(a.into_message_parts().1.is_empty());
}
#[test]
fn payload_fence_preserved_and_explicit_empty_is_not_missing() {
    let p = BTreeMap::from([("seed".into(), Value::Integer(7))]);
    let a = SceneAction {
        message_type: "preferencesResolved".into(),
        payload: Some(p),
        fence: Some(123u32),
    };
    assert_eq!(
        SceneAction::from_settings(Some(&a.to_settings())).unwrap(),
        a
    );
    let (tag, p, f) = a.into_message_parts();
    assert!(HostSceneMessage::decode_parts(&tag, &p, f).is_ok());
    let empty = SceneAction::<()> {
        message_type: "confirmReadyForDisplayAfterSceneResize".into(),
        payload: Some(BTreeMap::new()),
        fence: None,
    };
    assert!(empty.to_settings().contains_key(&1));
    assert_eq!(
        SceneAction::from_settings(Some(&empty.to_settings())).unwrap(),
        empty
    );
}
#[test]
fn missing_info_and_wrong_native_object_kinds_are_explicit() {
    assert_eq!(
        SceneAction::<()>::from_settings(None),
        Err(Error::MissingInfo)
    );
    assert_eq!(
        SceneAction::<()>::from_settings(Some(&BTreeMap::new())),
        Err(Error::MissingMessageType)
    );
    let mut p = BTreeMap::from([(0, Setting::<()>::Value(Value::Integer(0)))]);
    assert_eq!(
        SceneAction::from_settings(Some(&p)),
        Err(Error::MessageType)
    );
    p.insert(0, Setting::Value(Value::String("x".into())));
    p.insert(1, Setting::Value(Value::Null));
    assert_eq!(SceneAction::from_settings(Some(&p)), Err(Error::Payload));
    p.remove(&1);
    p.insert(2, Setting::Value(Value::Integer(1)));
    assert_eq!(
        SceneAction::from_settings(Some(&p)),
        Err(Error::FenceHandle)
    );
}
