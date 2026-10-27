// Replay owned SDK/native callback observations against the portable decoder.
// Native success-predicate false does not establish failure or termination.
use canvas_core::{
    binary_plist,
    payload_codec::Value,
    transport_reply::{acknowledge_reply, decode_reply_with, LazyReply},
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
fn boolean(value: &Value) -> bool {
    let Value::Boolean(value) = value else {
        panic!("boolean")
    };
    *value
}
fn main() {
    let input = binary_plist::decode(include_bytes!(
        "../tests/fixtures/encoded_future/input.bplist"
    ))
    .unwrap();
    let native = binary_plist::decode(include_bytes!(
        "../tests/fixtures/encoded_future/native.bplist"
    ))
    .unwrap();
    let native = dict(&native);
    assert_eq!(native["calls"], Value::Integer(6));
    assert_eq!(native["delayedReplyCopiesDestroyed"], Value::Integer(6));
    assert_eq!(native["futureReferencesReleased"], Value::Integer(6));
    let states = array(&native["states"]);
    let receipts = array(&native["carrierReceipts"]);
    assert_eq!(states.len(), 6);
    assert_eq!(receipts.len(), 6);
    for ((input, state), receipt) in array(&input).iter().zip(states).zip(receipts) {
        let input = dict(input);
        let state = dict(state);
        let receipt = dict(receipt);
        assert_eq!(state["case"], input["case"]);
        assert!(!boolean(&state["successfulBeforeEncodedCallback"]));
        for field in [
            "accepted",
            "peerSameProcess",
            "replyBytesAvailable",
            "replyBytesEqual",
        ] {
            assert!(boolean(&receipt[field]));
        }
        // Objective-C comparison boxing records this receipt field as an integer.
        assert_eq!(receipt["uvInitialized"], Value::Integer(1));
        assert_eq!(receipt["errorsBeforeCleanup"], Value::Integer(0));
        let Value::Data(bytes) = &input["responseData"] else {
            panic!("data")
        };
        let payload =
            boolean(&input["payloadPresent"]).then(|| LazyReply::Serialized(bytes.clone()));
        // The error token is opaque: native NSError projection is not reproduced.
        let error = boolean(&input["errorPresent"]).then_some("owned opaque error");
        let ack = acknowledge_reply(payload.clone(), error).is_ok();
        let decoded = decode_reply_with(payload, error, |fields| Ok::<_, ()>(fields.clone()));
        let success = decoded.is_ok();
        assert_eq!(success, boolean(&state["successfulAfterEncodedCallback"]));
        assert_eq!(success, boolean(&input["expectedSuccess"]));
        if let Ok(value) = decoded {
            assert_eq!(value, binary_plist::decode(bytes).unwrap());
        }
        // Available malformed/empty bytes select a payload, then fail typed parsing.
        assert_eq!(ack, boolean(&input["payloadPresent"]));
        let Value::String(name) = &input["case"] else {
            panic!("name")
        };
        println!("{name}: acknowledged={ack}, typed_success={success}");
    }
}
