//! Executable portable reply conformance control; no host IPC or private ABI.
//! Run natively or as wasm32-wasip1 with a WASI runtime.
use canvas_core::{
    binary_plist, binary_plist_writer,
    payload_codec::Value as V,
    service_property_list::ServicePropertyList as P,
    service_receiver::{prepare_observed_service_data, ServiceReceiverMessage},
    service_reply_dispatch::ServiceReplyNotifications,
    service_reply_error::ServiceReplyError,
    service_reply_failure::{
        classify_service_observed_data_with, ReplyRepresentation as R, ServiceReplyFailure as F,
        XpcFailure,
    },
    service_response::send_service_response_binary,
    settings_xpc::XpcValue as X,
    transport_reply::{acknowledge_reply, decode_reply_with, select_reply, ReplyError},
};
use std::{cell::RefCell, collections::BTreeMap};

fn main() {
    // Values exercise the 32-bit host-size boundary and both signed extremes.
    let fields = BTreeMap::from([
        ("min".into(), V::Integer(i64::MIN)),
        ("max".into(), V::Integer(i64::MAX)),
        ("wide".into(), V::Integer(1i64 << 32)),
        ("unicode".into(), V::String("owned 🪨\0雪".into())),
        (
            "bytes".into(),
            V::Data((0..=255).cycle().take(512).collect()),
        ),
        ("date".into(), V::Date(-1234.5)),
        ("real".into(), V::Real(f64::MIN_POSITIVE)),
    ]);
    let mut wire = BTreeMap::from([("extra".into(), X::Int64(17))]);
    assert_eq!(
        send_service_response_binary(
            true,
            Some(P::Dictionary(fields.clone())),
            None::<()>,
            &mut wire,
            |_| None,
            |_| "sent"
        ),
        Some("sent")
    );
    assert_eq!(wire["extra"], X::Int64(17));
    let X::Data(bytes) = &wire["data"] else {
        panic!()
    };
    for representation in [R::SerializedData, R::DeserializedDictionary] {
        let (payload, error) = classify_service_observed_data_with(
            Some(bytes),
            representation,
            binary_plist::decode,
            || panic!("available data"),
        );
        let decoded =
            decode_reply_with(payload, error, |value| Ok::<_, ()>(value.clone())).unwrap();
        assert_eq!(decoded, V::Dictionary(fields.clone()));
    }
    println!(
        "generated: signed64/wide32/unicode/data/date/real; both reply representations matched"
    );

    // Independently captured owned native/XPC fixtures, embedded in the module.
    for (name, bytes, remote) in [
        (
            "normal",
            include_bytes!("../tests/fixtures/service-xpc-roundtrip/normal.wire-data").as_slice(),
            false,
        ),
        (
            "error",
            include_bytes!("../tests/fixtures/service-xpc-roundtrip/error.wire-data").as_slice(),
            true,
        ),
        (
            "empty",
            include_bytes!("../tests/fixtures/service-xpc-roundtrip/empty.wire-data").as_slice(),
            false,
        ),
        (
            "malformed",
            include_bytes!("../tests/fixtures/service-xpc-roundtrip/malformed.wire-data")
                .as_slice(),
            false,
        ),
    ] {
        let (payload, error) = classify_service_observed_data_with(
            Some(bytes),
            R::SerializedData,
            binary_plist::decode,
            || panic!("available data"),
        );
        if remote {
            let Some(F::Remote(error)) = error else {
                panic!()
            };
            assert!(payload.is_none());
            let V::Dictionary(fields) = binary_plist::decode(bytes).unwrap() else {
                panic!()
            };
            assert_eq!(Some(error), ServiceReplyError::recognize(&fields));
        } else {
            assert!(acknowledge_reply(payload.clone(), error.clone()).is_ok());
            let decoded = decode_reply_with(payload, error, |v| Ok::<_, ()>(v.clone()));
            assert_eq!(decoded.is_ok(), name == "normal");
        }
        println!("fixture: {name} matched");
    }
    let available = prepare_observed_service_data(Some(&[]), || Some(17)).unwrap();
    assert_eq!(
        available,
        ServiceReceiverMessage::WithReply {
            message: P::Data(vec![]),
            reply: 17
        }
    );
    assert!(prepare_observed_service_data::<()>(None, || panic!("unavailable data")).is_none());
    let (payload, error) =
        classify_service_observed_data_with(None, R::SerializedData, binary_plist::decode, || {
            "unavailable".into()
        });
    assert_eq!(
        select_reply(payload, error),
        Err(ReplyError::Remote(F::Xpc(XpcFailure::InvalidType(
            "unavailable".into()
        ))))
    );
    println!("availability: Some(empty) accepted; None rejected before reply creation");

    let events = RefCell::new(Vec::new());
    let mut handlers = ServiceReplyNotifications {
        interruption: Some(|| events.borrow_mut().push("interrupt")),
        invalidation: Some(|| events.borrow_mut().push("invalidate")),
    };
    for failure in [
        XpcFailure::ConnectionInterrupted,
        XpcFailure::ConnectionInvalidated("owned".into()),
        XpcFailure::TerminationImminent,
    ] {
        let expected = Err(ReplyError::Remote(F::Xpc(failure)));
        handlers.dispatch(expected.clone(), |outcome| {
            assert_eq!(outcome, expected);
            events.borrow_mut().push("complete");
        });
    }
    assert_eq!(
        *events.borrow(),
        [
            "interrupt",
            "complete",
            "invalidate",
            "complete",
            "complete"
        ]
    );
    assert!(binary_plist_writer::encode(&V::Null).is_err());
    println!("notifications: specialized-before-completion; termination completion only");
    println!("PASS: portable pipeline; no native IPC, browser rendering or settlement assertion");
}
