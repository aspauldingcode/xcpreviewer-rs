use canvas_core::{scene_identity::SceneIdentity, settings_xpc::XpcValue as X, workspace_action::{WorkspaceActionInvocation as Invocation, SELECTOR}, xpc_wire};
use std::collections::BTreeMap;
fn expected(id: &str, extension: Option<&str>) -> X {
    let mut d = BTreeMap::from([
        ("bsxpc_CID".into(), X::UInt64(1)), ("bsxpc_CIDr".into(), X::Bool(false)),
        ("bsxpc_SEL".into(), X::String(SELECTOR.into())),
        ("1".into(), X::Dictionary(BTreeMap::from([("bsx_class".into(), X::String("FBSSceneIdentity".into())), ("i".into(), X::String(id.into()))]))),
        ("2".into(), X::Array(vec![])),
    ]);
    if let Some(s) = extension { d.insert("3".into(), X::String(s.into())); }
    X::Dictionary(d)
}
#[test]
fn native_primary_and_unicode_absent_extension_shapes() {
    for (name, extension) in [("owned.scene.primary", Some("owned.extension.primary")), ("owned.scene.☃", None)] {
        let value = expected(name, extension);
        let invocation = Invocation::from_xpc(&value).unwrap();
        assert_eq!(invocation.identity.identifier, name);
        assert_eq!(invocation.extension.as_deref(), extension);
        assert_eq!(invocation.to_xpc(), value);
        let bytes = xpc_wire::encode_body(&value).unwrap();
        assert_eq!(xpc_wire::decode_body(&bytes).unwrap(), value);
    }
}
#[test]
fn rejects_wrong_route_selector_argument_and_inline_completion() {
    let X::Dictionary(base) = expected("owned.scene.primary", None) else { unreachable!() };
    for (key, value) in [("bsxpc_CID",X::Int64(1)),("bsxpc_CIDr",X::Bool(true)),("bsxpc_SEL",X::String("wrong:".into())),("1",X::String("not an identity".into())),("2",X::Null),("3",X::Null),("4",X::Null)] {
        let mut d = base.clone(); d.insert(key.into(), value);
        assert!(Invocation::from_xpc(&X::Dictionary(d)).is_err(), "{key}");
    }
    for key in ["bsxpc_CID","bsxpc_CIDr","bsxpc_SEL","1","2"] {
        let mut d = base.clone(); d.remove(key);
        assert!(Invocation::from_xpc(&X::Dictionary(d)).is_err(), "{key}");
    }
}
#[test]
fn opaque_action_values_are_owned_snapshots_not_native_set_encoding() {
    let mut action = X::Data(vec![1,2,3]);
    let invocation = Invocation { connection_id: 7, identity: SceneIdentity {identifier:"owned".into(),workspace_identifier:None,internal_workspace_identifier:None}, actions:vec![action.clone()], extension:Some(String::new()) };
    if let X::Data(bytes) = &mut action { bytes[0]=9; }
    assert_eq!(invocation.actions,vec![X::Data(vec![1,2,3])]);
    let snapshot = invocation.to_xpc();
    assert_eq!(Invocation::from_xpc(&snapshot).unwrap(),invocation);
}
