use canvas_core::{action_xpc::ActionEnvelope, settings_xpc::XpcValue as X, workspace_action::WorkspaceActionCompletion as Completion, xpc_wire};
use std::collections::BTreeMap;
fn action(with_info: bool) -> X {
    let mut d = BTreeMap::from([("bsx_class".into(),X::String("BSAction".into()))]);
    if with_info { d.insert("i".into(),X::Dictionary(BTreeMap::from([("bsx_class".into(),X::String("BSSettings".into()))]))); }
    X::Dictionary(d)
}
#[test]
fn native_base_action_absent_and_empty_info_arguments() {
    for with_info in [false,true] {
        let value=action(with_info);let decoded=ActionEnvelope::from_service_argument(&value).unwrap();
        assert_eq!(decoded.info.is_some(),with_info);assert_eq!(decoded.to_service_argument(),value);
        let bytes=xpc_wire::encode_body(&value).unwrap();assert_eq!(xpc_wire::decode_body(&bytes).unwrap(),value);
    }
}
#[test]
fn selected_action_rejects_subclasses_and_responder_fields() {
    let X::Dictionary(d)=action(false)else{unreachable!()};
    for (key,value) in [("bsx_class",X::String("OtherAction".into())),("r",X::UInt64(1)),("i",X::Null)] {
        let mut bad=d.clone();bad.insert(key.into(),value);assert!(ActionEnvelope::from_service_argument(&X::Dictionary(bad)).is_err());
    }
}
#[test]
fn nullable_error_and_complete_opaque_archive_snapshot() {
    assert_eq!(Completion::from_xpc(&X::Dictionary(BTreeMap::new())).unwrap(),Completion::default());
    let mut original=vec![0,1,0xff,0,0x80];let reply=Completion{error_archive:Some(original.clone())};original[0]=9;
    let encoded=reply.to_xpc();assert_eq!(Completion::from_xpc(&encoded).unwrap().error_archive,Some(vec![0,1,0xff,0,0x80]));
    let bytes=xpc_wire::encode_body(&encoded).unwrap();assert_eq!(xpc_wire::decode_body(&bytes).unwrap(),encoded);
}
#[test]
fn strict_completion_fields_are_distinct_from_native_wrong_slot_policy() {
    for value in [X::Null,X::Dictionary(BTreeMap::from([("2".into(),X::Null)])),X::Dictionary(BTreeMap::from([("1".into(),X::Null)])),X::Dictionary(BTreeMap::from([("1".into(),X::Dictionary(BTreeMap::from([("bsx_class".into(),X::String("NSError".into())),("root".into(),X::String("bytes?".into()))])))]))] {assert!(Completion::from_xpc(&value).is_err());}
}
#[test]
fn native_error_archive_corpus_when_supplied() {
    let Some(paths)=std::env::var_os("XCPREVIEW_NATIVE_INVOCATION_REPLIES")else{return};let paths:Vec<_>=std::env::split_paths(&paths).collect();assert_eq!(paths.len(),2);
    for (path,size) in paths.into_iter().zip([104,108]) {
        let bytes=std::fs::read(path).unwrap();assert_eq!(bytes.len(),size);assert!(bytes.starts_with(b"bplist17"));
        let reply=Completion{error_archive:Some(bytes.clone())};let value=reply.to_xpc();let wire=xpc_wire::encode_body(&value).unwrap();let decoded=xpc_wire::decode_body(&wire).unwrap();assert_eq!(Completion::from_xpc(&decoded).unwrap().error_archive.as_ref().unwrap(),&bytes);
    }
    eprintln!("verified 2 actual native NSError archives, 212 bytes preserved");
}
