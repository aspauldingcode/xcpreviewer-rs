use canvas_core::{binary_plist, payload_codec::Value as V, service_reply_error::ServiceReplyError, service_reply_failure::{classify_service_xpc_dictionary_with as classify, ReplyRepresentation as Mode, ServiceReplyFailure as Failure, XpcFailure}, settings_xpc::XpcValue as X, transport_reply::{acknowledge_reply, decode_reply_with, select_reply, DecodeError, LazyReply, ReplyError, TypedReplyError}};
use std::{cell::Cell, collections::BTreeMap};
fn wire(bytes:&[u8]) -> BTreeMap<String,X> {BTreeMap::from([("data".into(),X::Data(bytes.to_vec())),("owned.extra".into(),X::Int64(17))])}
fn no_description() -> String {panic!("valid wire initializer must not request raw description")}
#[test]
fn normal_native_dictionary_retains_original_bytes_in_serialized_mode_and_full_values_in_legacy_mode() {
    let bytes=include_bytes!("fixtures/service-property-list/nested.wire-data");
    let V::Dictionary(expected)=binary_plist::decode(bytes).unwrap() else {panic!()};
    for (mode,count) in [(Mode::SerializedData,1),(Mode::DeserializedDictionary,2)] {
        let calls=Cell::new(0);let mut input=wire(bytes);
        let (p,e)=classify(&input,mode,|bytes| {calls.set(calls.get()+1);binary_plist::decode(bytes)},no_description);
        assert_eq!(calls.get(),count);assert!(e.is_none());input.clear();
        let reply=select_reply(p,e).unwrap();
        match mode {Mode::SerializedData=>assert_eq!(reply,LazyReply::Serialized(bytes.to_vec())),Mode::DeserializedDictionary=>assert_eq!(reply,LazyReply::Deserialized(expected.clone()))}
        assert_eq!(reply.property_list(),Ok(expected.clone()));
    }
}
#[test]
fn recognition_fallback_does_not_destroy_malformed_bytes_or_hide_late_typed_errors() {
    for (bytes,non_dictionary) in [(include_bytes!("fixtures/service-property-list/malformed.wire-data").as_slice(),false),(include_bytes!("fixtures/service-property-list/array_root.wire-data").as_slice(),true)] {
        let calls=Cell::new(0);
        let (p,e)=classify(&wire(bytes),Mode::SerializedData,|b| {calls.set(calls.get()+1);binary_plist::decode(b)},no_description);
        assert_eq!(calls.get(),1);assert_eq!(p,Some(LazyReply::Serialized(bytes.to_vec())));assert!(e.is_none());
        assert_eq!(acknowledge_reply(p.clone(),e.clone()),Ok(()));
        let typed_calls=Cell::new(0);
        let result=decode_reply_with(p,e,|_| {typed_calls.set(typed_calls.get()+1);Ok::<_,()>(())});
        if non_dictionary {assert_eq!(result,Err(TypedReplyError::Decode(DecodeError::NonDictionary)));}
        else {assert!(matches!(result,Err(TypedReplyError::Decode(DecodeError::Plist(_)))));}
        assert_eq!(typed_calls.get(),0);
    }
}
#[test]
fn legacy_dictionary_mode_repeats_getter_and_keeps_its_empty_fallback() {
    for bytes in [include_bytes!("fixtures/service-property-list/malformed.wire-data").as_slice(),include_bytes!("fixtures/service-property-list/array_root.wire-data").as_slice()] {
        let calls=Cell::new(0);
        let (p,e)=classify(&wire(bytes),Mode::DeserializedDictionary,|b| {calls.set(calls.get()+1);binary_plist::decode(b)},no_description);
        assert_eq!(calls.get(),2);assert!(e.is_none());assert_eq!(p,Some(LazyReply::Deserialized(BTreeMap::new())));
    }
}
#[test]
fn missing_wrong_and_empty_data_fail_before_parser_and_request_description_once() {
    for input in [BTreeMap::new(),BTreeMap::from([("data".into(),X::String("owned".into()))]),wire(&[])] {
        let descriptions=Cell::new(0);
        let (p,e)=classify(&input,Mode::SerializedData,|_| -> Result<V,()> {panic!("rejected input must not parse")},|| {descriptions.set(descriptions.get()+1);"owned raw 🪨\nsecond line".into()});
        assert_eq!(descriptions.get(),1);assert_eq!(select_reply(p,e),Err(ReplyError::Remote(Failure::Xpc(XpcFailure::InvalidType("owned raw 🪨\nsecond line".into())))));
    }
}
#[test]
fn actual_native_error_fields_select_remote_error_before_either_success_representation() {
    let bytes=include_bytes!("fixtures/service-wire-reply/remote-error.wire-data");
    let expected=ServiceReplyError {domain:"owned/reply/🪨".into(),code:i64::MIN,user_info:BTreeMap::from([("bytes".into(),V::Data((0..128).collect())),("reason".into(),V::String("owned failure".into()))])};
    assert_eq!(binary_plist::decode(bytes).unwrap(),V::Dictionary(expected.to_dictionary()));
    for mode in [Mode::SerializedData,Mode::DeserializedDictionary] {
        let calls=Cell::new(0);
        let (p,e)=classify(&wire(bytes),mode,|b| {calls.set(calls.get()+1);binary_plist::decode(b)},no_description);
        assert_eq!(calls.get(),1);assert!(p.is_none());assert_eq!(e,Some(Failure::Remote(expected.clone())));
    }
}
