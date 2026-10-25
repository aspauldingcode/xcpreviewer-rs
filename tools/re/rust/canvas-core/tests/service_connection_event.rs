use canvas_core::{
    service_connection_event::ServiceConnectionEvents,
    service_reply_dispatch::ServiceReplyNotifications,
    service_reply_failure::ServiceReplyFailure,
    service_reply_failure::{ObservedXpcError, XpcFailure},
    transport_reply::ReplyError,
};
use std::cell::RefCell;

#[test]
fn event_matrix_uses_specific_notifications_or_unchanged_generic_error() {
    let notifications = RefCell::new(Vec::new());
    let generic = RefCell::new(Vec::new());
    let mut handlers = ServiceConnectionEvents {
        notifications: ServiceReplyNotifications {
            interruption: Some(|| notifications.borrow_mut().push("interrupted")),
            invalidation: Some(|| notifications.borrow_mut().push("invalidated")),
        },
        connection_error: Some(|error| generic.borrow_mut().push(error)),
    };
    for kind in [
        XpcFailure::ConnectionInterrupted,
        XpcFailure::ConnectionInvalidated("owned 🪨".into()),
        XpcFailure::TerminationImminent,
        XpcFailure::InvalidType("owned dictionary".into()),
        XpcFailure::Unknown(
            "owned
error"
                .into(),
        ),
    ] {
        handlers.dispatch_error(kind);
    }
    assert_eq!(*notifications.borrow(), ["interrupted", "invalidated"]);
    assert_eq!(
        *generic.borrow(),
        [
            XpcFailure::TerminationImminent,
            XpcFailure::InvalidType("owned dictionary".into()),
            XpcFailure::Unknown(
                "owned
error"
                    .into()
            )
        ]
    );
}

#[test]
fn missing_specialized_handlers_do_not_fall_back_to_generic_handler() {
    let generic = RefCell::new(Vec::new());
    let mut handlers = ServiceConnectionEvents {
        notifications: ServiceReplyNotifications {
            interruption: None::<fn()>,
            invalidation: None::<fn()>,
        },
        connection_error: Some(|error| generic.borrow_mut().push(error)),
    };
    handlers.dispatch_error(ObservedXpcError::ConnectionInterrupted.classify());
    handlers.dispatch_error(ObservedXpcError::ConnectionInvalidated { reason: None }.classify());
    assert!(generic.borrow().is_empty());
    handlers.dispatch_error(ObservedXpcError::TerminationImminent.classify());
    assert_eq!(*generic.borrow(), [XpcFailure::TerminationImminent]);
    handlers.connection_error = None;
    handlers.dispatch_error(XpcFailure::Unknown(
        "ignored with no generic handler".into(),
    ));
    assert_eq!(generic.borrow().len(), 1);
}

#[test]
fn reply_and_event_paths_share_notification_slots_but_keep_generic_errors_separate() {
    let events = RefCell::new(Vec::new());
    let mut handlers = ServiceConnectionEvents {
        notifications: ServiceReplyNotifications {
            interruption: Some(|| events.borrow_mut().push("interrupted")),
            invalidation: Some(|| events.borrow_mut().push("invalidated")),
        },
        connection_error: Some(|kind| {
            assert_eq!(kind, XpcFailure::TerminationImminent);
            events.borrow_mut().push("connection error");
        }),
    };
    handlers.dispatch_error(XpcFailure::ConnectionInterrupted);
    handlers.notifications.dispatch(
        Err(ReplyError::Remote(ServiceReplyFailure::Xpc(
            XpcFailure::ConnectionInterrupted,
        ))),
        |reply| {
            assert!(reply.is_err());
            events.borrow_mut().push("request completion");
        },
    );
    assert_eq!(
        *events.borrow(),
        ["interrupted", "interrupted", "request completion"]
    );
    // Separate invocations model caller-supplied events, not an observed native
    // duplicate or a guarantee that both paths receive the same XPC condition.
    handlers.notifications.clear_connection_notifications();
    handlers.dispatch_error(XpcFailure::ConnectionInvalidated("after clear".into()));
    handlers.notifications.dispatch(
        Err(ReplyError::Remote(ServiceReplyFailure::Xpc(
            XpcFailure::TerminationImminent,
        ))),
        |_| events.borrow_mut().push("request completion"),
    );
    handlers.dispatch_error(XpcFailure::TerminationImminent);
    assert_eq!(
        *events.borrow(),
        [
            "interrupted",
            "interrupted",
            "request completion",
            "request completion",
            "connection error"
        ]
    );
}
