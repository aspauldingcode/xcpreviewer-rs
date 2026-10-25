use canvas_core::{
    binary_plist,
    payload_codec::Value,
    service_property_list::ServicePropertyList as P,
    service_receiver::{
        prepare_observed_service_data, prepare_service_dictionary, ServiceReceiverMessage,
    },
    service_reply_error::ServiceReplyError,
    service_reply_failure::{
        classify_service_observed_data_with as observed, ReplyRepresentation as Mode,
        ServiceReplyFailure, XpcFailure,
    },
    settings_xpc::XpcValue as X,
    transport_reply::{
        acknowledge_reply, decode_reply_with, select_reply, DecodeError, LazyReply, ReplyError,
        TypedReplyError,
    },
};
use std::{cell::Cell, collections::BTreeMap};
#[test]
fn empty_bytes_after_receipt_are_distinct_from_unavailable_local_bytes() {
    let bytes = include_bytes!("fixtures/service-xpc-roundtrip/empty.wire-data");
    assert!(bytes.is_empty());
    assert_eq!(
        P::from_observed_xpc_data(Some(bytes)),
        Some(P::Data(vec![]))
    );
    assert_eq!(P::from_observed_xpc_data(None), None);
    assert_eq!(
        P::from_xpc_dictionary(&BTreeMap::from([("data".into(), X::Data(vec![]))])),
        None
    );
    assert_eq!(
        P::from_observed_xpc_data(Some(bytes))
            .unwrap()
            .dictionary_with(binary_plist::decode),
        BTreeMap::new()
    );
}
#[test]
fn received_empty_reply_selects_success_but_serialized_typing_still_fails() {
    let bytes = include_bytes!("fixtures/service-xpc-roundtrip/empty.wire-data");
    let Value::Dictionary(native) = binary_plist::decode(include_bytes!(
        "fixtures/service-xpc-roundtrip/empty.decoded"
    ))
    .unwrap() else {
        panic!()
    };
    assert!(native.is_empty());
    for (mode, calls) in [(Mode::SerializedData, 1), (Mode::DeserializedDictionary, 2)] {
        let parses = Cell::new(0);
        let (p, e) = observed(
            Some(bytes),
            mode,
            |b| {
                parses.set(parses.get() + 1);
                binary_plist::decode(b)
            },
            || panic!("received bytes available"),
        );
        assert_eq!(parses.get(), calls);
        assert!(e.is_none());
        assert_eq!(acknowledge_reply(p.clone(), e.clone()), Ok(()));
        if mode == Mode::SerializedData {
            assert_eq!(p, Some(LazyReply::Serialized(vec![])));
            assert!(matches!(
                decode_reply_with(p, e, |_| Ok::<_, ()>(())),
                Err(TypedReplyError::Decode(DecodeError::Plist(_)))
            ));
        } else {
            assert_eq!(
                select_reply(p, e),
                Ok(LazyReply::Deserialized(native.clone()))
            );
        }
    }
    let (p, e) = observed(
        None,
        Mode::SerializedData,
        |_| -> Result<Value, ()> { panic!() },
        || "bytes unavailable".into(),
    );
    assert_eq!(
        select_reply(p, e),
        Err(ReplyError::Remote(ServiceReplyFailure::Xpc(
            XpcFailure::InvalidType("bytes unavailable".into())
        )))
    );
}
#[test]
fn native_received_normal_error_and_malformed_responses_match_portable_projection() {
    let normal = include_bytes!("fixtures/service-xpc-roundtrip/normal.wire-data");
    let Value::Dictionary(expected) = binary_plist::decode(include_bytes!(
        "fixtures/service-xpc-roundtrip/normal.decoded"
    ))
    .unwrap() else {
        panic!()
    };
    let (p, e) = observed(
        Some(normal),
        Mode::SerializedData,
        binary_plist::decode,
        || panic!(),
    );
    assert_eq!(select_reply(p, e).unwrap().property_list(), Ok(expected));
    let error = include_bytes!("fixtures/service-xpc-roundtrip/error.wire-data");
    let Value::Dictionary(expected) = binary_plist::decode(include_bytes!(
        "fixtures/service-xpc-roundtrip/error.decoded"
    ))
    .unwrap() else {
        panic!()
    };
    let (p, e) = observed(
        Some(error),
        Mode::SerializedData,
        binary_plist::decode,
        || panic!(),
    );
    assert!(p.is_none());
    assert_eq!(
        e,
        Some(ServiceReplyFailure::Remote(
            ServiceReplyError::recognize(&expected).unwrap()
        ))
    );
    let malformed = include_bytes!("fixtures/service-xpc-roundtrip/malformed.wire-data");
    let (p, e) = observed(
        Some(malformed),
        Mode::SerializedData,
        binary_plist::decode,
        || panic!(),
    );
    assert!(select_reply(p, e).unwrap().property_list().is_err());
    assert_eq!(
        binary_plist::decode(include_bytes!(
            "fixtures/service-xpc-roundtrip/malformed.decoded"
        ))
        .unwrap(),
        Value::Dictionary(BTreeMap::new())
    );
}
#[test]
fn receipt_aware_empty_request_creates_reply_capability_before_receiver_dispatch() {
    let calls = Cell::new(0);
    let message = prepare_observed_service_data(Some(&[]), || {
        calls.set(calls.get() + 1);
        Some(17)
    });
    assert_eq!(
        message,
        Some(ServiceReceiverMessage::WithReply {
            message: P::Data(vec![]),
            reply: 17
        })
    );
    assert_eq!(calls.get(), 1);
    assert_eq!(
        prepare_observed_service_data(None, || -> Option<i32> { panic!() }),
        None
    );
    assert_eq!(
        prepare_service_dictionary(
            &BTreeMap::from([("data".into(), X::Data(vec![]))]),
            || -> Option<i32> { panic!() }
        ),
        None
    );
}
