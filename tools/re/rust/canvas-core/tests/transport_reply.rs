use canvas_core::{payload_codec::Value, transport_reply::{select_reply, DecodeError, LazyReply, ReplyError}};
use std::collections::BTreeMap;
fn fields() -> BTreeMap<String, Value> {
    BTreeMap::from([
        ("padding".into(), Value::Data((0..128).collect())),
        ("reply".into(), Value::Dictionary(BTreeMap::from([
            ("message".into(), Value::String("owned/🪨".into())),
            ("sequence".into(), Value::Integer(-17)),
        ]))),
    ])
}
#[test]
fn payload_wins_both_nullable_callback_combinations() {
    for error in [None, Some("ignored remote failure")] {
        let result = select_reply(Some(LazyReply::Deserialized(fields())), error).unwrap();
        assert_eq!(result.property_list(), Ok(fields()));
    }
    assert_eq!(select_reply::<&str>(None, None), Err(ReplyError::EmptyReply));
    assert_eq!(select_reply(None, Some("remote failure")), Err(ReplyError::Remote("remote failure")));
}
#[test]
fn binary_payload_retains_every_byte_and_decodes_only_on_request() {
    let bytes = include_bytes!("fixtures/transport-reply/dictionary.bplist").to_vec();
    let reply = select_reply(Some(LazyReply::Serialized(bytes.clone())), Some("ignored")).unwrap();
    assert_eq!(reply, LazyReply::Serialized(bytes));
    assert_eq!(reply.property_list(), Ok(fields()));
    assert_eq!(reply.property_list(), Ok(fields()));
}
#[test]
fn malformed_payload_wins_then_fails_later_without_error_fallback() {
    let malformed = vec![0, 255, 17, 42];
    let reply = select_reply(Some(LazyReply::Serialized(malformed.clone())), Some("not fallback")).unwrap();
    assert_eq!(reply, LazyReply::Serialized(malformed));
    assert_eq!(reply.property_list(), Err(DecodeError::Plist(canvas_core::binary_plist::Error::Header)));
    let array = LazyReply::Serialized(include_bytes!("fixtures/transport-reply/array.bplist").to_vec());
    assert_eq!(array.property_list(), Err(DecodeError::NonDictionary));
}
#[test]
fn deserialized_snapshot_owns_data_and_does_not_reparse() {
    let mut reply = LazyReply::Deserialized(fields());
    let mut first = reply.property_list().unwrap();
    first.insert("padding".into(), Value::Data(vec![0; 128]));
    assert_eq!(reply.property_list(), Ok(fields()));
    if let LazyReply::Deserialized(ref mut map) = reply { map.clear(); }
    assert_eq!(reply.property_list(), Ok(BTreeMap::new()));
}
