use canvas_core::{
    binary_plist,
    payload_codec::Value,
    service_reply_dispatch::ServiceReplyNotifications,
    service_reply_error::ServiceReplyError,
    service_reply_failure::{
        classify_service_reply, classify_service_xpc_dictionary_with, ObservedXpcError,
        ReplyRepresentation, ServiceReplyFailure, ServiceReplyInput, XpcFailure,
    },
    settings_xpc::XpcValue,
    transport_reply::{select_reply, LazyReply, ReplyError},
};
use std::{cell::RefCell, collections::BTreeMap, rc::Rc};
type Outcome = Result<LazyReply, ReplyError<ServiceReplyFailure>>;
fn xpc(error: XpcFailure) -> Outcome {
    Err(ReplyError::Remote(ServiceReplyFailure::Xpc(error)))
}

#[test]
fn notification_matrix_precedes_completion_and_preserves_every_outcome() {
    let cases = [
        (xpc(XpcFailure::ConnectionInterrupted), Some("interruption")),
        (
            xpc(XpcFailure::ConnectionInvalidated("owned 🪨".into())),
            Some("invalidation"),
        ),
        (xpc(XpcFailure::TerminationImminent), None),
        (xpc(XpcFailure::InvalidType("dictionary".into())), None),
        (xpc(XpcFailure::Unknown("owned".into())), None),
        (
            Err(ReplyError::Remote(ServiceReplyFailure::Remote(
                ServiceReplyError {
                    domain: "owned".into(),
                    code: i64::MIN,
                    user_info: BTreeMap::new(),
                },
            ))),
            None,
        ),
        (Err(ReplyError::EmptyReply), None),
        (Ok(LazyReply::Serialized(vec![1, 2, 3])), None),
        (
            Ok(LazyReply::Deserialized(BTreeMap::from([(
                "owned".into(),
                Value::Integer(17),
            )]))),
            None,
        ),
    ];
    for (outcome, notification) in cases {
        let events = RefCell::new(Vec::new());
        let mut handlers = ServiceReplyNotifications {
            interruption: Some(|| events.borrow_mut().push("interruption")),
            invalidation: Some(|| events.borrow_mut().push("invalidation")),
        };
        let expected = outcome.clone();
        let returned = handlers.dispatch(outcome, |received| {
            let before: Vec<_> = notification.into_iter().collect();
            assert_eq!(*events.borrow(), before);
            events.borrow_mut().push("completion");
            assert_eq!(received, expected);
            17
        });
        assert_eq!(returned, 17);
        let expected: Vec<_> = notification.into_iter().chain(["completion"]).collect();
        assert_eq!(*events.borrow(), expected);
    }
}

#[test]
fn absent_and_cleared_notifications_still_forward_each_request() {
    let events = RefCell::new(Vec::new());
    let mut handlers = ServiceReplyNotifications {
        interruption: Some(|| events.borrow_mut().push("interruption")),
        invalidation: Some(|| events.borrow_mut().push("invalidation")),
    };
    handlers.interruption = None;
    for event in [
        ObservedXpcError::ConnectionInterrupted,
        ObservedXpcError::ConnectionInvalidated {
            reason: Some("first".into()),
        },
    ] {
        let (p, e) = classify_service_reply(ServiceReplyInput::Error(event));
        handlers.dispatch(select_reply(p, e), |outcome| assert!(outcome.is_err()));
    }
    assert_eq!(*events.borrow(), ["invalidation"]);
    handlers.clear_connection_notifications();
    handlers.clear_connection_notifications();
    for kind in [
        XpcFailure::ConnectionInterrupted,
        XpcFailure::ConnectionInvalidated("after clear".into()),
    ] {
        let outcome = xpc(kind);
        let expected = outcome.clone();
        assert_eq!(handlers.dispatch(outcome, |reply| reply), expected);
    }
    assert_eq!(*events.borrow(), ["invalidation"]);
}

#[test]
fn clearing_local_notification_captures_does_not_drop_request_capture() {
    struct Capture(&'static str, Rc<RefCell<Vec<&'static str>>>);
    impl Drop for Capture {
        fn drop(&mut self) {
            self.1.borrow_mut().push(self.0);
        }
    }
    let events = Rc::new(RefCell::new(Vec::new()));
    let i = Capture("drop interruption", events.clone());
    let v = Capture("drop invalidation", events.clone());
    let request = Capture("drop request", events.clone());
    let mut handlers = ServiceReplyNotifications {
        interruption: Some(move || {
            let _ = &i;
        }),
        invalidation: Some(move || {
            let _ = &v;
        }),
    };
    let complete = move |reply: Outcome| {
        assert!(reply.is_err());
        drop(request);
    };
    handlers.clear_connection_notifications();
    assert_eq!(*events.borrow(), ["drop interruption", "drop invalidation"]);
    handlers.dispatch(xpc(XpcFailure::ConnectionInterrupted), complete);
    assert_eq!(
        *events.borrow(),
        ["drop interruption", "drop invalidation", "drop request"]
    );
}

#[test]
fn native_wire_fixtures_keep_remote_errors_and_late_decode_errors_separate_from_notifications() {
    let events = RefCell::new(Vec::new());
    let mut handlers = ServiceReplyNotifications {
        interruption: Some(|| events.borrow_mut().push("interruption")),
        invalidation: Some(|| events.borrow_mut().push("invalidation")),
    };
    for (bytes, remote) in [
        (
            include_bytes!("fixtures/service-wire-reply/remote-error.wire-data").as_slice(),
            true,
        ),
        (
            include_bytes!("fixtures/service-property-list/malformed.wire-data").as_slice(),
            false,
        ),
    ] {
        let fields = BTreeMap::from([("data".into(), XpcValue::Data(bytes.to_vec()))]);
        let (p, e) = classify_service_xpc_dictionary_with(
            &fields,
            ReplyRepresentation::SerializedData,
            binary_plist::decode,
            || panic!("nonempty wire input"),
        );
        handlers.dispatch(select_reply(p, e), |reply| {
            assert!(events.borrow().is_empty());
            if remote {
                assert!(matches!(
                    reply,
                    Err(ReplyError::Remote(ServiceReplyFailure::Remote(_)))
                ));
            } else {
                let reply = reply.unwrap();
                assert_eq!(reply, LazyReply::Serialized(bytes.to_vec()));
                assert!(reply.property_list().is_err());
            }
        });
    }
    assert!(events.borrow().is_empty());
}
