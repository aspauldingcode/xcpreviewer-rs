// Actual native plain XPCConnection send/reply controls on owned local peers.
use canvas_core::{
    binary_plist,
    payload_codec::Value,
    service_reply_failure::{
        classify_service_observed_data_with, ReplyRepresentation, ServiceReplyFailure, XpcFailure,
    },
    transport_reply::LazyReply,
};
use std::collections::BTreeMap;
fn dict(v: &Value) -> &BTreeMap<String, Value> {
    let Value::Dictionary(v) = v else {
        panic!("dictionary")
    };
    v
}
fn bytes(v: &Value) -> &[u8] {
    let Value::Data(v) = v else { panic!("data") };
    v
}
fn text(v: &Value) -> &str {
    let Value::String(v) = v else {
        panic!("string")
    };
    v
}
fn main() {
    let native = binary_plist::decode(include_bytes!(
        "../tests/fixtures/native_local_connection/native.bplist"
    ))
    .unwrap();
    let Value::Array(rows) = native else {
        panic!("rows")
    };
    assert_eq!(rows.len(), 8);
    for row in rows {
        let row = dict(&row);
        let profile = text(&row["profile"]);
        let peer = dict(&row["peer"]);
        assert_eq!(row["callbackCount"], Value::Integer(1));
        assert_eq!(row["replyTimedOut"], Value::Boolean(false));
        assert_eq!(peer["dictionaries"], Value::Integer(1));
        assert_eq!(peer["sameProcessPeer"], Value::Integer(1));
        let expected = BTreeMap::from([("ownedRequest".into(), Value::Integer(17))]);
        assert_eq!(
            binary_plist::decode(bytes(&peer["messageData"])).unwrap(),
            Value::Dictionary(expected)
        );
        let available = row["responseDataPresent"] == Value::Boolean(true);
        assert_eq!(available, profile != "missing");
        assert_eq!(row["uvPresent"], Value::Boolean(available));
        let data = available.then(|| bytes(&row["responseData"]));
        let mut described = 0;
        let (payload, error) = classify_service_observed_data_with(
            data,
            ReplyRepresentation::SerializedData,
            binary_plist::decode,
            || {
                described += 1;
                "owned rejected dictionary".into()
            },
        );
        assert_eq!(row["errorPresent"], Value::Boolean(error.is_some()));
        if profile == "missing" {
            assert!(payload.is_none());
            assert_eq!(described, 1);
            assert_eq!(
                error,
                Some(ServiceReplyFailure::Xpc(XpcFailure::InvalidType(
                    "owned rejected dictionary".into()
                )))
            );
            assert_eq!(
                row["errorDomain"],
                Value::String("PreviewsServices.XPCError".into())
            );
            assert_eq!(row["errorCode"], Value::Integer(1));
        } else {
            assert!(error.is_none());
            assert_eq!(described, 0);
            let payload = payload.unwrap();
            assert_eq!(
                payload,
                LazyReply::Serialized(bytes(&row["responseData"]).to_vec())
            );
            if profile == "valid" {
                assert_eq!(
                    Value::Dictionary(payload.property_list().unwrap()),
                    row["response"]
                )
            } else {
                assert!(payload.property_list().is_err());
                assert_eq!(
                    bytes(&row["responseData"]),
                    if profile == "malformed" {
                        &b"invalid"[..]
                    } else {
                        &b""[..]
                    }
                );
            }
        }
        println!(
            "{}/{}: native receipt and portable reply classification match",
            text(&row["direction"]),
            profile
        );
    }
}
