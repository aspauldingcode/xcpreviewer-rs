use canvas_core::action_xpc::{ActionEnvelope, Error};
use canvas_core::settings_xpc::XpcValue::{self, *};
use canvas_core::payload_codec::Value;
use std::collections::BTreeMap;
fn objects(v: &mut XpcValue) -> &mut Vec<XpcValue> {
    let Dictionary(root) = v else { panic!() };
    let Some(Dictionary(info)) = root.get_mut("i") else { panic!() };
    let Some(Array(objects)) = info.get_mut("objects") else { panic!() };objects
}
fn wrapper(v: &mut XpcValue) -> &mut BTreeMap<std::string::String, XpcValue> {
    let Array(parts) = &mut objects(v)[1] else { panic!() };
    let Dictionary(wrapper) = &mut parts[1] else { panic!() };wrapper
}
#[test]
fn native_action_envelopes_preserve_absence_classes_and_all_268_data_bytes() {
    let native=include!("fixtures/native-action-xpc.rs");
    for (i,x) in native.iter().enumerate() {
        let action=ActionEnvelope::from_xpc(x).unwrap();
        assert_eq!(action.info.is_none(),i==0);
        assert_eq!(&action.to_xpc(),x);
    }
    let action=ActionEnvelope::from_xpc(&native[3]).unwrap();
    let info=action.info.unwrap();
    assert_eq!(info.archived_settings().objects.len(),1);
    assert_eq!(info.property_list(1),Some(&BTreeMap::from([("count".into(),Value::Integer(7)),("label".into(),Value::String("owned".into()))])));
    assert_eq!(info.property_list(0),None); // ordinary string remains opaque
}
#[test]
fn outer_and_inner_class_confusion_and_unobserved_endpoints_reject() {
    let native=include!("fixtures/native-action-xpc.rs");
    for inner in [false,true] {
        let mut x=native[3].clone();let w=wrapper(&mut x);
        if inner { let Some(Dictionary(d))=w.get_mut("__BSXPCSecureValue") else { panic!() };d.insert("bsx_class".into(),String("NSObject".into())); }
        else { w.insert("__BSXPCSecureClass".into(),String("NSObject".into())); }
        assert_eq!(ActionEnvelope::from_xpc(&x),Err(Error::Class));
    }
    let mut x=native[1].clone();let Dictionary(root)=&mut x else { panic!() };root.insert("r".into(),UInt64(1));
    assert_eq!(ActionEnvelope::from_xpc(&x),Err(Error::Envelope));
}
#[test]
fn duplicate_native_slot_and_truncated_property_list_reject() {
    let native=include!("fixtures/native-action-xpc.rs");
    let mut x=native[3].clone();let duplicate=objects(&mut x)[1].clone();objects(&mut x).push(duplicate);
    assert_eq!(ActionEnvelope::from_xpc(&x),Err(Error::DuplicateSlot));
    let mut x=native[3].clone();let w=wrapper(&mut x);let Some(Dictionary(inner))=w.get_mut("__BSXPCSecureValue") else { panic!() };let Some(Data(bytes))=inner.get_mut("data") else { panic!() };bytes.pop();
    assert!(matches!(ActionEnvelope::from_xpc(&x),Err(Error::PropertyList(_))));
    let mut x=native[3].clone();let Array(parts)=&mut objects(&mut x)[1] else { panic!() };parts[0]=UInt64(0);
    assert_eq!(ActionEnvelope::from_xpc(&x),Err(Error::DuplicateSlot));
}
#[test]
fn decoded_property_list_and_export_own_native_data() {
    let mut native=include!("fixtures/native-action-xpc.rs");let saved=ActionEnvelope::from_xpc(&native[3]).unwrap();
    let w=wrapper(&mut native[3]);let Some(Dictionary(inner))=w.get_mut("__BSXPCSecureValue") else { panic!() };let Some(Data(bytes))=inner.get_mut("data") else { panic!() };bytes.fill(0);
    assert_ne!(saved.to_xpc(),native[3]);assert_eq!(saved.info.unwrap().property_list(1).unwrap()["count"],Value::Integer(7));
}
