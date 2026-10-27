// Compare portable reply categories and complete values with actual native snapshots.
use canvas_core::{
    binary_plist,
    payload_codec::Value,
    transport_reply::{decode_reply_with, LazyReply, ReplyError, TypedReplyError},
};
use std::collections::BTreeMap;
fn dict(value: &Value) -> &BTreeMap<String, Value> {
    let Value::Dictionary(fields) = value else {
        panic!("dictionary")
    };
    fields
}
fn array(value: &Value) -> &[Value] {
    let Value::Array(values) = value else {
        panic!("array")
    };
    values
}
fn text(value: &Value) -> &str {
    let Value::String(value) = value else {
        panic!("string")
    };
    value
}
fn boolean(value: &Value) -> bool {
    let Value::Boolean(value) = value else {
        panic!("boolean")
    };
    *value
}
fn main() {
    let input = binary_plist::decode(include_bytes!(
        "../tests/fixtures/future_result/input.bplist"
    ))
    .unwrap();
    let native = binary_plist::decode(include_bytes!(
        "../tests/fixtures/future_result/native.bplist"
    ))
    .unwrap();
    let native = dict(&native);
    assert_eq!(native["stateSize"], Value::Integer(58));
    assert_eq!(native["stateStride"], Value::Integer(64));
    assert_eq!(native["calls"], Value::Integer(6));
    let states = array(&native["states"]);
    assert_eq!(states.len(), 6);
    for (input, state) in array(&input).iter().zip(states) {
        let input = dict(input);
        let state = dict(state);
        assert_eq!(state["case"], input["case"]);
        assert_eq!(text(&dict(&state["beforeSnapshot"])["state"]), "running");
        let after = dict(&state["afterSnapshot"]);
        assert_eq!(text(&after["state"]), "finished");
        let Value::Data(bytes) = &input["responseData"] else {
            panic!("data")
        };
        let payload =
            boolean(&input["payloadPresent"]).then(|| LazyReply::Serialized(bytes.clone()));
        // Opaque token: exact native NSError presentation remains host-specific.
        let error = boolean(&input["errorPresent"]).then_some("owned error");
        let result = decode_reply_with(payload, error, |value| Ok::<_, ()>(value.clone()));
        let category = match result {
            Ok(value) => {
                assert_eq!(text(&after["termination"]), "succeeded");
                assert_eq!(value, after["value"]);
                "success"
            }
            Err(TypedReplyError::Decode(_)) => {
                assert_eq!(text(&after["termination"]), "failed");
                assert_eq!(text(&after["domain"]), "NSCocoaErrorDomain");
                assert_eq!(after["code"], Value::Integer(3840));
                "parse_failure"
            }
            Err(TypedReplyError::Reply(ReplyError::Remote(_))) => {
                assert_eq!(text(&after["termination"]), "failed");
                assert!(text(&after["errorType"]).ends_with(".HumanReadableNSError"));
                let wrapped = dict(&after["wrappedError"]);
                assert_eq!(text(&wrapped["domain"]), "owned.encoded.reply");
                assert_eq!(wrapped["code"], Value::Integer(17));
                assert_eq!(text(&wrapped["description"]), "owned reply failure");
                "remote_failure"
            }
            Err(TypedReplyError::Reply(ReplyError::EmptyReply)) => {
                assert_eq!(text(&after["termination"]), "failed");
                assert!(text(&after["errorType"]).ends_with(".EmptyReply"));
                "empty_reply"
            }
            Err(TypedReplyError::Payload(())) => unreachable!(),
        };
        println!("{}: finished, {category}", text(&input["case"]));
    }
}
