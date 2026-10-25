use canvas_core::{
    binary_plist,
    payload_codec::Value,
    service_property_list::ServicePropertyList as P,
    service_reply_error::ServiceReplyError,
    service_reply_failure::{
        classify_service_xpc_dictionary_with, ReplyRepresentation, ServiceReplyFailure,
    },
    service_response::{select_service_response_with, send_service_response_with},
    settings_xpc::XpcValue as X,
};
use std::{cell::Cell, collections::BTreeMap};
fn untouched() -> BTreeMap<String, X> {
    BTreeMap::from([("owned.extra".into(), X::Int64(17))])
}
#[test]
fn absent_connection_or_outcome_or_failed_projection_leaves_reply_and_send_untouched() {
    for (live, payload, error, projections) in [
        (false, Some(P::Data(vec![1])), Some(17), 0),
        (false, None, Some(17), 0),
        (true, None, None, 0),
        (true, None, Some(17), 1),
    ] {
        let mut reply = untouched();
        let count = Cell::new(0);
        let result = send_service_response_with(
            live,
            payload,
            error,
            &mut reply,
            |_| {
                count.set(count.get() + 1);
                None
            },
            |_| -> Result<Vec<u8>, ()> { panic!("no selected response") },
            |_| -> () { panic!("no send") },
        );
        assert_eq!(result, None);
        assert_eq!(reply, untouched());
        assert_eq!(count.get(), projections);
    }
}
#[test]
fn present_payload_wins_without_error_projection_or_reencoding_stored_bytes() {
    let bytes = include_bytes!("fixtures/service-property-list/malformed.wire-data");
    let mut reply = untouched();
    let result = send_service_response_with(
        true,
        Some(P::Data(bytes.to_vec())),
        Some("ignored"),
        &mut reply,
        |_| -> Option<ServiceReplyError> { panic!("payload wins") },
        |_| -> Result<Vec<u8>, ()> { panic!("stored data bypasses serialization") },
        |wire| {
            assert_eq!(wire.get("data"), Some(&X::Data(bytes.to_vec())));
            Err::<(), _>("owned send failure")
        },
    );
    assert_eq!(result, Some(Err("owned send failure")));
    assert_eq!(reply.get("owned.extra"), Some(&X::Int64(17)));
}
#[test]
fn projected_error_encodes_exact_dictionary_and_round_trips_through_reply_classifier() {
    let bytes = include_bytes!("fixtures/service-wire-reply/remote-error.wire-data");
    let Value::Dictionary(fields) = binary_plist::decode(bytes).unwrap() else {
        panic!()
    };
    let error = ServiceReplyError::recognize(&fields).unwrap();
    let mut reply = untouched();
    let projections = Cell::new(0);
    let encodes = Cell::new(0);
    let result = send_service_response_with(
        true,
        None,
        Some(error.clone()),
        &mut reply,
        |error| {
            projections.set(projections.get() + 1);
            Some(error)
        },
        |encoded| {
            encodes.set(encodes.get() + 1);
            assert_eq!(encoded, &fields);
            Ok::<_, ()>(bytes.to_vec())
        },
        |wire| {
            let (payload, error) = classify_service_xpc_dictionary_with(
                wire,
                ReplyRepresentation::SerializedData,
                binary_plist::decode,
                || panic!("valid data"),
            );
            assert!(payload.is_none());
            error
        },
    );
    assert_eq!(result, Some(Some(ServiceReplyFailure::Remote(error))));
    assert_eq!(projections.get(), 1);
    assert_eq!(encodes.get(), 1);
}
#[test]
fn serialization_failure_still_writes_one_data_entry_and_calls_send() {
    let mut reply = BTreeMap::new();
    let calls = Cell::new(0);
    let result = send_service_response_with(
        true,
        None,
        Some(ServiceReplyError {
            domain: "owned".into(),
            code: -17,
            user_info: BTreeMap::new(),
        }),
        &mut reply,
        Some,
        |_| -> Result<Vec<u8>, ()> { Err(()) },
        |wire| {
            calls.set(calls.get() + 1);
            assert_eq!(wire.len(), 1);
            assert_eq!(wire.get("data"), Some(&X::Data(vec![])));
            false
        },
    );
    assert_eq!(result, Some(false));
    assert_eq!(calls.get(), 1);
}
#[test]
fn receiver_can_invoke_response_capability_after_its_message_dispatch_returns() {
    use canvas_core::service_receiver::{prepare_service_dictionary, ServiceMessageReceiver};
    type Capability = Box<dyn FnOnce(P) -> Option<usize>>;
    struct Receiver(Option<Capability>);
    impl ServiceMessageReceiver<Capability> for Receiver {
        fn receive(&mut self, _: P) {
            panic!("request expected");
        }
        fn receive_with_reply(&mut self, _: P, reply: Capability) {
            self.0 = Some(reply);
        }
    }
    let fields = BTreeMap::from([("data".into(), X::Data(b"owned request".to_vec()))]);
    let mut receiver = Receiver(None);
    let request = prepare_service_dictionary(&fields, || {
        Some(Box::new(|payload| {
            send_service_response_with(
                true,
                Some(payload),
                None::<()>,
                &mut BTreeMap::new(),
                |_| None,
                |_| -> Result<Vec<u8>, ()> { panic!("stored bytes") },
                |wire| match &wire["data"] {
                    X::Data(bytes) => bytes.len(),
                    _ => panic!(),
                },
            )
        }) as Capability)
    })
    .unwrap();
    request.dispatch_to(Some(&mut receiver));
    assert_eq!(
        receiver.0.take().unwrap()(P::Data(b"owned response".to_vec())),
        Some(14)
    );
    assert_eq!(
        select_service_response_with(true, None, None::<()>, |_| None),
        None
    );
}
