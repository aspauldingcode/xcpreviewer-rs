use canvas_core::{
    scene_identity::*,
    settings_xpc::XpcValue::{self, *},
    xpc_wire,
};
use std::collections::BTreeMap;
fn fixture(mode: usize) -> XpcValue {
    let mut d = BTreeMap::from([
        ("bsx_class".into(), String("FBSSceneIdentity".into())),
        (
            "i".into(),
            String(
                if mode == 3 {
                    "owned.scene.☃"
                } else {
                    "owned.scene"
                }
                .into(),
            ),
        ),
    ]);
    if (1..=3).contains(&mode) {
        d.insert("w".into(), String("owned.workspace".into()));
    }
    if mode >= 2 {
        d.insert("iw".into(), String("owned.internal".into()));
    }
    Dictionary(d)
}
#[test]
fn five_independently_observed_native_shapes() {
    for mode in 0..5 {
        let native = fixture(mode);
        let identity = SceneIdentity::from_xpc(&native).unwrap();
        assert_eq!(identity.to_xpc(), native);
        assert_eq!(
            identity.workspace_identifier.is_some(),
            (1..=3).contains(&mode)
        );
        assert_eq!(identity.internal_workspace_identifier.is_some(), mode >= 2);
        assert_eq!(
            identity.effective_internal_workspace_identifier(),
            match mode {
                0 => None,
                1 => Some("owned.workspace"),
                _ => Some("owned.internal"),
            }
        );
        let bytes = xpc_wire::encode_body(&identity.to_xpc()).unwrap();
        assert_eq!(xpc_wire::decode_body(&bytes).unwrap(), native);
    }
}
#[test]
fn class_field_and_unknown_variant_rejection() {
    let Dictionary(d) = fixture(0) else { panic!() };
    for (key, value) in [
        ("bsx_class", String("Wrong".into())),
        ("i", Null),
        ("w", Int64(7)),
        ("iw", Data(vec![])),
        ("unmeasured", Bool(true)),
    ] {
        let mut bad = d.clone();
        bad.insert(key.into(), value);
        assert!(SceneIdentity::from_xpc(&Dictionary(bad)).is_err());
    }
    let mut missing = d;
    missing.remove("i");
    assert_eq!(
        SceneIdentity::from_xpc(&Dictionary(missing)),
        Err(Error::Identifier)
    );
}
#[test]
fn preserves_raw_absence_utf8_and_owned_snapshot() {
    let mut source = fixture(3);
    let identity = SceneIdentity::from_xpc(&source).unwrap();
    let Dictionary(ref mut d) = source else {
        panic!()
    };
    d.insert("i".into(), String("mutated".into()));
    assert_eq!(identity.identifier.as_bytes(), "owned.scene.☃".as_bytes());
    let fallback = SceneIdentity::from_xpc(&fixture(1)).unwrap();
    let Dictionary(d) = fallback.to_xpc() else {
        panic!()
    };
    assert!(!d.contains_key("iw"));
    assert_eq!(
        fallback.effective_internal_workspace_identifier(),
        Some("owned.workspace")
    );
}
