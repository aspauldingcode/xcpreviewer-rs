// Actual native receiver data forwarding and explicit Unit acknowledgement controls.
use canvas_core::{
    binary_plist,
    payload_codec::Value,
    service_receiver::{prepare_observed_service_data, ServiceReceiverMessage},
    transport_reply::LazyReply,
};
use std::collections::BTreeMap;
fn dict(value: &Value) -> &BTreeMap<String, Value> {
    let Value::Dictionary(v) = value else {
        panic!("dictionary")
    };
    v
}
fn array(value: &Value) -> &[Value] {
    let Value::Array(v) = value else {
        panic!("array")
    };
    v
}
fn text(value: &Value) -> &str {
    let Value::String(v) = value else {
        panic!("string")
    };
    v
}
fn bytes(value: &Value) -> &[u8] {
    let Value::Data(v) = value else {
        panic!("data")
    };
    v
}
fn main() {
    let input = binary_plist::decode(include_bytes!(
        "../tests/fixtures/daemon_receiver/input.bplist"
    ))
    .unwrap();
    let native = binary_plist::decode(include_bytes!(
        "../tests/fixtures/daemon_receiver/native.bplist"
    ))
    .unwrap();
    let native = dict(&native);
    assert_eq!(native["relayCalls"], Value::Integer(12));
    assert_eq!(native["encodedCallbackCalls"], Value::Integer(4));
    assert_eq!(native["lazySize"], Value::Integer(17));
    assert_eq!(native["lazyStride"], Value::Integer(24));
    let rows = array(&native["rows"]);
    assert_eq!(rows.len(), 12);
    for (index, (input, row)) in array(&input).iter().zip(rows).enumerate() {
        let input = dict(input);
        let row = dict(row);
        assert_eq!(input["case"], row["case"]);
        let mode = text(&input["mode"]);
        let data = bytes(&input["data"]);
        let token = Box::new(index);
        let address = &*token as *const usize;
        let mut creates = 0;
        let initialized = prepare_observed_service_data(Some(data), || {
            creates += 1;
            (mode != "oneway").then_some(token)
        })
        .unwrap();
        assert_eq!(creates, 1);
        let mut encodes = 0;
        let relay = initialized.into_daemon_data_with(|_| {
            encodes += 1;
            Err::<Vec<u8>, ()>(())
        });
        assert_eq!(encodes, 0);
        assert_eq!(relay.message, LazyReply::Serialized(data.to_vec()));
        assert_eq!(bytes(&row["serializedBytes"]), data);
        assert_eq!(row["replyPresent"], Value::Boolean(relay.reply.is_some()));
        if let Some(reply) = &relay.reply {
            assert_eq!(&**reply as *const usize, address)
        }
        let parsed = relay.message.property_list();
        assert_eq!(row["parseAccepted"], Value::Boolean(parsed.is_ok()));
        if let Ok(fields) = parsed {
            assert_eq!(Value::Dictionary(fields), row["canonical"])
        }
        let callbacks = array(&row["encodedReplies"]);
        if mode == "send" {
            assert_eq!(callbacks.len(), 1);
            let callback = dict(&callbacks[0]);
            assert_eq!(callback["payloadPresent"], Value::Boolean(true));
            assert_eq!(callback["errorPresent"], Value::Boolean(false));
            let summary = dict(&callback["summary"]);
            assert_eq!(summary["dictionary"], Value::Dictionary(BTreeMap::new()));
            assert_eq!(
                binary_plist::decode(bytes(&summary["data"])).unwrap(),
                Value::Dictionary(BTreeMap::new())
            )
        } else {
            assert!(callbacks.is_empty())
        }
        println!(
            "{}: lazy bytes preserved, reply {}, parse {}",
            text(&input["case"]),
            relay.reply.is_some(),
            row["parseAccepted"] == Value::Boolean(true)
        );
    }
    // Dictionary serialization is supplied explicitly; failure stays lazy empty data.
    let mut encodes = 0;
    let failed = ServiceReceiverMessage::<()>::OneWay(
        canvas_core::service_property_list::ServicePropertyList::Dictionary(BTreeMap::new()),
    )
    .into_daemon_data_with(|_| {
        encodes += 1;
        Err::<Vec<u8>, ()>(())
    });
    assert_eq!(encodes, 1);
    assert_eq!(failed.message, LazyReply::Serialized(Vec::new()));
    assert!(failed.message.property_list().is_err());
}
