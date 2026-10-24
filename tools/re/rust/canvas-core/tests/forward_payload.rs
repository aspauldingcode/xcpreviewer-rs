use canvas_core::{agent_message_kind::AgentMessageKind as K,forward_payload::{ForwardPayload as F,PreviewContentDomain as D,PreviewOrientation as O,Error},payload_codec::Value};
fn full()->Value {canvas_core::binary_plist::decode(include_bytes!("fixtures/forward-payload/full.bplist")).unwrap()}
#[test]
fn independent_full_fixture_preserves_payload_and_aliases() {
 let v=full();let f=F::decode(&v).unwrap();assert_eq!(f.message_type,K::IncrementalCaptureIOSurface);assert_eq!(f.pid,i32::MAX);assert_eq!(f.content_domain,Some(D::View));assert_eq!(f.preview_interface_orientation,Some(O::LandscapeRight));assert_eq!(f.scene_identifier.as_deref(),Some("owned/🪨"));assert_eq!(f.to_value(),v);
 let Value::Dictionary(body)=&f.message_payload else {panic!()};assert_eq!(body.get("padding"),Some(&Value::Data((0..64).collect())));
}
#[test]
fn missing_orientation_normalizes_but_other_optional_fields_stay_absent() {
 let f=F::decode_binary(include_bytes!("fixtures/forward-payload/minimal.bplist")).unwrap();assert_eq!(f.pid,i32::MIN);assert_eq!(f.content_domain,None);assert_eq!(f.scene_identifier,None);assert_eq!(f.preview_interface_orientation,Some(O::Portrait));
 let Value::Dictionary(d)=f.to_value() else {panic!()};assert_eq!(d.get("previewInterfaceOrientation"),Some(&Value::String("portrait".into())));assert!(!d.contains_key("previewContextType"));
}
#[test]
fn all_recovered_domain_and_orientation_values_roundtrip() {
 for d in [D::View,D::Widget,D::Complication] {for o in [O::Portrait,O::PortraitUpsideDown,O::LandscapeLeft,O::LandscapeRight] {let mut f=F::decode(&full()).unwrap();f.content_domain=Some(d);f.preview_interface_orientation=Some(o);assert_eq!(F::decode(&f.to_value()).unwrap(),f);}}
 assert_eq!(D::View.as_str(),"application");assert_eq!(D::from_raw("view"),None);
}
#[test]
fn required_fields_and_strict_scalar_negatives() {
 for key in ["messageType","messagePayload","pid"] {let Value::Dictionary(mut d)=full() else {panic!()};d.remove(key);assert_eq!(F::decode(&Value::Dictionary(d)),Err(Error::Missing(key)));}
 for (key,bad) in [("pid",Value::Integer(i64::from(i32::MAX)+1)),("pid",Value::Integer(i64::from(i32::MIN)-1)),("pid",Value::Real(1.0)),("messageType",Value::String("unknown".into())),("previewContextType",Value::String("view".into())),("previewInterfaceOrientation",Value::String("up".into())),("sceneIdentifier",Value::Integer(7)),("previewContextType",Value::Null)] {let Value::Dictionary(mut d)=full() else {panic!()};d.insert(key.into(),bad);assert!(F::decode(&Value::Dictionary(d)).is_err());}
}
