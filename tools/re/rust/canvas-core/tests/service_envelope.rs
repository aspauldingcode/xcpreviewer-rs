use canvas_core::{service_envelope::{ForwardServiceEnvelope as E,Error,IDENTIFIER_KEY},agent_message_kind::AgentMessageKind as K,payload_codec::Value};
fn fixture()->Value {canvas_core::binary_plist::decode(include_bytes!("fixtures/service-envelope/forward.bplist")).unwrap()}
#[test]
fn exact_outer_and_inner_kinds_and_identifier_namespace() {
 let value=fixture();let envelope=E::decode(&value).unwrap();assert_eq!(envelope.identifier.as_deref(),Some("owned/request/🪨"));assert_eq!(envelope.forward.message_type,K::IncrementalCaptureIOSurface);assert_eq!(envelope.to_value(),value);
 let Value::Dictionary(body)=envelope.forward.message_payload else {panic!()};assert_eq!(body.get(IDENTIFIER_KEY),Some(&Value::String("nested-not-envelope".into())));assert_eq!(body.get("padding"),Some(&Value::Data((0..64).collect())));
}
#[test]
fn missing_identifier_is_not_generated_or_read_from_other_namespaces() {
 let Value::Dictionary(mut root)=fixture() else {panic!()};let Value::Dictionary(payload)=root.get_mut("payload").unwrap() else {panic!()};payload.remove(IDENTIFIER_KEY);root.insert(IDENTIFIER_KEY.into(),Value::String("wrong-root".into()));root.insert("identifier".into(),Value::String("also-wrong".into()));
 let envelope=E::decode(&Value::Dictionary(root)).unwrap();assert_eq!(envelope.identifier,None);let Value::Dictionary(encoded)=envelope.to_value() else {panic!()};let Value::Dictionary(payload)=encoded.get("payload").unwrap() else {panic!()};assert!(!payload.contains_key(IDENTIFIER_KEY));
}
#[test]
fn outer_kind_and_required_shape_fail_explicitly() {
 for key in ["messageType","payload"] {let Value::Dictionary(mut d)=fixture() else {panic!()};d.remove(key);assert_eq!(E::decode(&Value::Dictionary(d)),Err(Error::Missing(key)));}
 let Value::Dictionary(mut d)=fixture() else {panic!()};d.insert("messageType".into(),Value::String("captureIOSurface".into()));assert_eq!(E::decode(&Value::Dictionary(d.clone())),Err(Error::UnsupportedMessageType));d.insert("messageType".into(),Value::String("forward".into()));d.insert("payload".into(),Value::Null);assert_eq!(E::decode(&Value::Dictionary(d)),Err(Error::Type("payload")));
}
#[test]
fn identifier_type_and_inner_codec_errors_propagate() {
 for value in [Value::Null,Value::Integer(7)] {let Value::Dictionary(mut d)=fixture() else {panic!()};let Value::Dictionary(p)=d.get_mut("payload").unwrap() else {panic!()};p.insert(IDENTIFIER_KEY.into(),value);assert_eq!(E::decode(&Value::Dictionary(d)),Err(Error::Type(IDENTIFIER_KEY)));}
 let Value::Dictionary(mut d)=fixture() else {panic!()};let Value::Dictionary(p)=d.get_mut("payload").unwrap() else {panic!()};p.remove("pid");assert!(matches!(E::decode(&Value::Dictionary(d)),Err(Error::Forward(_))));
}
