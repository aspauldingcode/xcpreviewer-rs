// Native pending-reply outcomes; portable completion below is original composition.
// No native Future, observer, receiver registration or final settlement is invoked.
use canvas_core::{
    binary_plist,
    payload_codec::Value,
    reply_completion::{ReplyCompletion, ReplyTermination},
    service_reply_failure::{
        classify_service_observed_data_with, classify_service_reply, ObservedXpcError,
        ReplyRepresentation, ServiceReplyFailure, ServiceReplyInput, XpcFailure,
    },
    transport_reply::{select_reply, ReplyError},
};
use std::collections::BTreeMap;
fn dict(v: &Value) -> &BTreeMap<String, Value> {
    let Value::Dictionary(v) = v else {
        panic!("dictionary")
    };
    v
}
fn text(v: &Value) -> &str {
    let Value::String(v) = v else {
        panic!("string")
    };
    v
}
fn bytes(v: &Value) -> &[u8] {
    let Value::Data(v) = v else { panic!("data") };
    v
}
fn main() {
    let fixture = binary_plist::decode(include_bytes!(
        "../tests/fixtures/native_pending_reply/native.bplist"
    ))
    .unwrap();
    let Value::Array(rows) = fixture else {
        panic!("rows")
    };
    assert_eq!(rows.len(), 3);
    for row in rows {
        let row = dict(&row);
        let mode = text(&row["mode"]);
        let peer = dict(&row["peer"]);
        assert_eq!(row["callbackCount"], Value::Integer(1));
        assert_eq!(row["replyTimedOut"], Value::Boolean(false));
        assert_eq!(peer["dictionaries"], Value::Integer(1));
        assert_eq!(peer["sameProcessPeer"], Value::Integer(1));
        assert_eq!(
            binary_plist::decode(bytes(&peer["messageData"])).unwrap(),
            Value::Dictionary(BTreeMap::from([(
                "ownedRequest".into(),
                Value::Integer(17)
            )]))
        );
        let (payload, error) = match mode {
            "local-invalidate" => {
                assert_eq!(
                    text(&row["nativeKind"]),
                    "connectionInvalidated(\"xpc_connection_cancel()\")"
                );
                classify_service_reply(ServiceReplyInput::Error(
                    ObservedXpcError::ConnectionInvalidated {
                        reason: Some("xpc_connection_cancel()".into()),
                    },
                ))
            }
            "remote-close" => {
                assert_eq!(text(&row["nativeKind"]), "connectionInterrupted");
                classify_service_reply(ServiceReplyInput::Error(
                    ObservedXpcError::ConnectionInterrupted,
                ))
            }
            "reply-first" => {
                assert_eq!(text(&row["nativeKind"]), "");
                classify_service_observed_data_with(
                    Some(bytes(&row["responseData"])),
                    ReplyRepresentation::SerializedData,
                    binary_plist::decode,
                    || panic!("reply initialized"),
                )
            }
            _ => panic!("mode"),
        };
        assert_eq!(row["uvPresent"], Value::Boolean(payload.is_some()));
        assert_eq!(row["errorPresent"], Value::Boolean(error.is_some()));
        if error.is_some() {
            assert_eq!(text(&row["errorDomain"]), "PreviewsServices.XPCError");
            assert_eq!(row["errorCode"], Value::Integer(1));
        }
        let selected = select_reply(payload, error);
        match &selected {
            Ok(value) => assert_eq!(
                Value::Dictionary(value.property_list().unwrap()),
                row["response"]
            ),
            Err(ReplyError::Remote(ServiceReplyFailure::Xpc(
                XpcFailure::ConnectionInvalidated(reason),
            ))) => {
                assert_eq!(mode, "local-invalidate");
                assert_eq!(reason, "xpc_connection_cancel()");
            }
            Err(ReplyError::Remote(ServiceReplyFailure::Xpc(
                XpcFailure::ConnectionInterrupted,
            ))) => assert_eq!(mode, "remote-close"),
            _ => panic!("unexpected callback outcome"),
        }
        let mut local = ReplyCompletion::new();
        assert!(local.try_complete(selected).is_ok());
        assert!(matches!(
            local.termination(),
            Some(ReplyTermination::Completed(_))
        ));
        println!(
            "{}: delivered callback projected and completed locally",
            mode
        );
    }
}
