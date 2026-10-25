use canvas_core::{
    binary_plist,
    payload_codec::Value as V,
    service_reply_dispatch::ServiceReplyNotifications,
    service_reply_failure::{
        classify_service_reply, ObservedXpcError, ServiceReplyFailure, ServiceReplyInput,
        XpcFailure,
    },
    transport_reply::{select_reply, LazyReply, ReplyError},
};
use std::{cell::RefCell, collections::BTreeMap, rc::Rc};
type Outcome = Result<LazyReply, ReplyError<ServiceReplyFailure>>;
fn records() -> Vec<BTreeMap<String, V>> {
    let V::Array(rows) =
        binary_plist::decode(include_bytes!("observed.bplist")).unwrap()
    else {
        panic!()
    };
    rows.into_iter()
        .map(|r| {
            let V::Dictionary(r) = r else { panic!() };
            r
        })
        .collect()
}

fn owned_sdk_categories_feed_existing_projected_reply_routes() {
    let rows = records();
    assert_eq!(rows.len(), 2);
    for row in rows {
        for key in [
            "request_received",
            "callback_received",
            "capture_alive_before_operation",
            "capture_dropped_after_callback_within_1s",
            "quiet_window_completed",
        ] {
            assert_eq!(row[key], V::Boolean(true));
        }
        assert_eq!(row["callbacks_in_observation_window"], V::Integer(1));
        assert_eq!(row["capture_drops"], V::Integer(1));
        assert_eq!(row["target_resource_settlement_proven"], V::Boolean(false));
        let V::String(mode) = &row["mode"] else {
            panic!()
        };
        let input = if mode == "cancel" {
            assert_eq!(row["reply_invalid"], V::Boolean(true));
            assert_eq!(row["late_peer_reply_submitted"], V::Boolean(true));
            ServiceReplyInput::Error(ObservedXpcError::ConnectionInvalidated { reason: None })
        } else {
            assert_eq!(mode, "normal");
            assert_eq!(row["owned_marker_matches"], V::Boolean(true));
            ServiceReplyInput::DecodedDictionary(BTreeMap::from([(
                "owned.marker".into(),
                V::String("owned reply marker".into()),
            )]))
        };
        let (payload, error) = classify_service_reply(input);
        let mut handlers = ServiceReplyNotifications {
            interruption: None::<fn()>,
            invalidation: None::<fn()>,
        };
        let outcome = handlers.dispatch(select_reply(payload, error), |reply| reply);
        if mode == "cancel" {
            assert_eq!(
                outcome,
                Err(ReplyError::Remote(ServiceReplyFailure::Xpc(
                    XpcFailure::ConnectionInvalidated("<no description>".into())
                )))
            );
        } else {
            assert!(matches!(outcome, Ok(LazyReply::Deserialized(_))));
        }
    }
}
struct Capture {
    label: &'static str,
    events: Rc<RefCell<Vec<&'static str>>>,
}
impl Drop for Capture {
    fn drop(&mut self) {
        self.events.borrow_mut().push(self.label);
    }
}
fn notification(capture: Capture) -> impl FnMut() {
    move || {
        std::hint::black_box(&capture);
    }
}

fn clearing_notification_captures_keeps_separate_completion_alive() {
    let rows = records();
    let cancel = rows
        .iter()
        .find(|r| r["mode"] == V::String("cancel".into()))
        .unwrap();
    assert_eq!(cancel["reply_invalid"], V::Boolean(true));
    let events = Rc::new(RefCell::new(Vec::new()));
    let capture = |label| Capture {
        label,
        events: events.clone(),
    };
    let mut handlers = ServiceReplyNotifications {
        interruption: Some(notification(capture("drop.interruption"))),
        invalidation: Some(notification(capture("drop.invalidation"))),
    };
    let pending = capture("drop.pending");
    let callback_events = events.clone();
    let completion = move |reply: Outcome| {
        std::hint::black_box(&pending);
        callback_events.borrow_mut().push("completion");
        reply
    };
    handlers.clear_connection_notifications();
    assert_eq!(*events.borrow(), ["drop.interruption", "drop.invalidation"]);
    let (p, e) = classify_service_reply(ServiceReplyInput::Error(
        ObservedXpcError::ConnectionInvalidated { reason: None },
    ));
    let outcome = handlers.dispatch(select_reply(p, e), completion);
    assert!(outcome.is_err());
    assert_eq!(
        *events.borrow(),
        [
            "drop.interruption",
            "drop.invalidation",
            "completion",
            "drop.pending"
        ]
    );
}

fn main(){owned_sdk_categories_feed_existing_projected_reply_routes();clearing_notification_captures_keeps_separate_completion_alive();println!("Owned SDK category projections and separate portable completion-capture controls passed in WASI");}
