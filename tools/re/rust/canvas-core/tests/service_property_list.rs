use canvas_core::{binary_plist, payload_codec::Value as V, service_property_list::ServicePropertyList as P, settings_xpc::XpcValue as X, service_reply_error::ServiceReplyError, service_reply_failure::{classify_service_reply, ServiceReplyInput}, transport_reply::{select_reply, LazyReply}};
use std::{cell::Cell, collections::BTreeMap};
fn nested() -> BTreeMap<String,V> {
    BTreeMap::from([
        ("bytes".into(),V::Data((0..128).collect())),("name".into(),V::String("owned/🪨".into())),
        ("min".into(),V::Integer(i64::MIN)),("max".into(),V::Integer(i64::MAX)),
        ("real".into(),V::Real(3.5)),("date".into(),V::Date(17.0)),
        ("array".into(),V::Array(vec![V::Boolean(true),V::String("value".into())])),
    ])
}
#[test]
fn native_wire_payloads_decode_complete_empty_and_nested_values() {
    for (bytes,expected) in [
        (include_bytes!("fixtures/service-property-list/empty.wire-data").as_slice(),BTreeMap::new()),
        (include_bytes!("fixtures/service-property-list/nested.wire-data").as_slice(),nested()),
    ] {
        let mut wire=BTreeMap::from([("data".into(),X::Data(bytes.to_vec())),("owned.extra".into(),X::Int64(17))]);
        let p=P::from_xpc_dictionary(&wire).unwrap();wire.clear();
        assert_eq!(p.dictionary_with(binary_plist::decode),expected);
        assert_eq!(p.data_with(|_| -> Result<Vec<u8>,()> {panic!("stored bytes must bypass encoder")}),bytes);
    }
}
#[test]
fn initialization_rejects_missing_wrong_and_empty_but_parsing_bad_nonempty_returns_empty_map() {
    for wire in [BTreeMap::new(),BTreeMap::from([("data".into(),X::String("owned".into()))]),BTreeMap::from([("data".into(),X::Data(vec![]))])] {
        assert_eq!(P::from_xpc_dictionary(&wire),None);
    }
    for bytes in [include_bytes!("fixtures/service-property-list/malformed.wire-data").as_slice(),include_bytes!("fixtures/service-property-list/array_root.wire-data").as_slice()] {
        let p=P::from_xpc_dictionary(&BTreeMap::from([("data".into(),X::Data(bytes.to_vec()))])).unwrap();
        let fields=p.dictionary_with(binary_plist::decode);assert!(fields.is_empty());
        let (payload,error)=classify_service_reply(ServiceReplyInput::DecodedDictionary(fields));
        assert_eq!(select_reply(payload,error).unwrap().property_list(),Ok(BTreeMap::new()));
        // TransportReply's different throwing lazy parser retains its errors.
        assert!(LazyReply::Serialized(bytes.to_vec()).property_list().is_err());
    }
}
#[test]
fn failed_serializer_still_writes_one_data_entry_and_bypasses_count_zero_retry() {
    let e=ServiceReplyError {domain:"owned/error".into(),code:-17,user_info:BTreeMap::new()};
    let p=P::Dictionary(e.to_dictionary());let mut wire=BTreeMap::new();
    // Inject the native Foundation failure observation; this portable Value
    // profile cannot represent the NSObject used by the independent helper.
    p.encode_to_xpc_dictionary_with(&mut wire, |_| -> Result<Vec<u8>,()> {Err(())});
    assert_eq!(wire,BTreeMap::from([("data".into(),X::Data(include_bytes!("fixtures/service-property-list/invalid_error.wire-data").to_vec()))]));
    assert_eq!(wire.len(),1);assert_eq!(e.retry_dictionary_if_empty(wire.len(),"owned failure"),None);
    assert_eq!(P::from_xpc_dictionary(&wire),None);
    wire.insert("owned.extra".into(),X::Int64(17));wire.insert("data".into(),X::String("old".into()));
    p.encode_to_xpc_dictionary_with(&mut wire, |_| -> Result<Vec<u8>,()> {Err(())});
    assert_eq!(wire.len(),2);assert_eq!(wire["owned.extra"],X::Int64(17));assert_eq!(wire["data"],X::Data(vec![]));
}
#[test]
fn stored_direction_skips_conversion_and_computed_results_are_not_cached() {
    let p=P::Dictionary(nested());
    assert_eq!(p.dictionary_with(|_| -> Result<V,()> {panic!("dictionary storage must bypass parser")}),nested());
    let calls=Cell::new(0);
    for i in 1..=2 {assert_eq!(p.data_with(|fields| {assert_eq!(fields,&nested());calls.set(calls.get()+1);Ok::<_,()>(vec![i])}),vec![i]);}
    assert_eq!(calls.get(),2);
    let raw=P::Data(vec![1]);let calls=Cell::new(0);
    for _ in 0..2 {assert_eq!(raw.dictionary_with(|bytes| {assert_eq!(bytes,&[1]);calls.set(calls.get()+1);Ok::<_,()>(V::Dictionary(nested()))}),nested());}
    assert_eq!(calls.get(),2);
}
