use canvas_core::{payload_codec::Value, scene_timing::*};
use std::{cell::Cell, collections::BTreeMap, rc::Rc};
fn payload(n: i64) -> BTreeMap<String, Value> {
    BTreeMap::from([("seed".into(), Value::Integer(n))])
}
#[test]
fn source_seed_wrap_matches_independent_bit_domain_cases() {
    for (before, after) in [
        (0, 1),
        (1, 2),
        (-1, 0),
        (i64::MAX, i64::MIN),
        (i64::MIN, i64::MIN + 1),
    ] {
        let mut s = SceneSeedCounter::from_last(SceneUpdateSeed(before));
        assert_eq!(s.next_seed(), SceneUpdateSeed(after));
    }
    let mut s = SceneSeedCounter::from_last(SceneUpdateSeed(0));
    assert_eq!(
        (s.next_seed().0, s.next_seed().0, s.next_seed().0),
        (1, 2, 3)
    );
}
#[test]
fn timing_is_presence_only_and_preferences_preserve_token() {
    let m =
        HostSceneMessage::decode_parts("preferencesResolved", &payload(-4), Some(77u32)).unwrap();
    assert_eq!(
        m,
        HostSceneMessage::PreferencesResolved {
            seed: SceneUpdateSeed(-4),
            fence: Some(77)
        }
    );
    assert_eq!(m.timing().raw(), "fenced");
    let m =
        HostSceneMessage::<u32>::decode_parts("preferencesResolved", &payload(0), None).unwrap();
    assert_eq!(m.timing().raw(), "async");
}
#[test]
fn constructor_fence_policy_and_unsupported_event_are_explicit() {
    let empty = BTreeMap::new();
    assert_eq!(
        HostSceneMessage::<()>::decode_parts(
            "confirmReadyForDisplayAfterSceneResize",
            &empty,
            None
        ),
        Ok(HostSceneMessage::ConfirmReadyForDisplayAfterSceneResize)
    );
    for tag in ["confirmReadyForDisplayAfterSceneResize", "hardwareEvent"] {
        assert_eq!(
            HostSceneMessage::decode_parts(tag, &empty, Some(())),
            Err(Error::UnexpectedFence)
        );
    }
    assert_eq!(
        HostSceneMessage::<()>::decode_parts("hardwareEvent", &empty, None),
        Err(Error::UnsupportedHardwareEvent)
    );
    assert_eq!(
        HostSceneMessage::<()>::decode_parts("preferencesResolved", &empty, None),
        Err(Error::MissingSeed)
    );
    assert_eq!(
        HostSceneMessage::<()>::decode_parts(
            "preferencesResolved",
            &BTreeMap::from([("seed".into(), Value::Boolean(true))]),
            None
        ),
        Err(Error::SeedType)
    );
    assert!(matches!(
        HostSceneMessage::<()>::decode_parts("future", &empty, None),
        Err(Error::UnknownMessageType(_))
    ));
}
#[test]
fn original_token_ownership_drops_once_on_error_and_success() {
    struct Token(Rc<Cell<u32>>);
    impl Drop for Token {
        fn drop(&mut self) {
            self.0.set(self.0.get() + 1)
        }
    }
    let count = Rc::new(Cell::new(0));
    assert!(HostSceneMessage::decode_parts(
        "confirmReadyForDisplayAfterSceneResize",
        &BTreeMap::new(),
        Some(Token(count.clone()))
    )
    .is_err());
    assert_eq!(count.get(), 1);
    assert!(HostSceneMessage::decode_parts(
        "preferencesResolved",
        &BTreeMap::new(),
        Some(Token(count.clone()))
    )
    .is_err());
    assert_eq!(count.get(), 2);
    let m = HostSceneMessage::decode_parts(
        "preferencesResolved",
        &payload(1),
        Some(Token(count.clone())),
    )
    .unwrap();
    assert_eq!(count.get(), 2);
    drop(m);
    assert_eq!(count.get(), 3);
}
