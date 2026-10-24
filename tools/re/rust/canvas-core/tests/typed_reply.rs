use canvas_core::{transport_reply::{acknowledge_reply, decode_reply_with, LazyReply, ReplyError, TypedReplyError, DecodeError}, payload_codec::{Value, DecodeError as FieldError}, iosurface_payload::{IOSurfacePayload, Error as SurfaceError}};
use std::{cell::Cell, collections::BTreeMap};
fn serialized() -> LazyReply {
    LazyReply::Serialized(include_bytes!("fixtures/iosurface-payload/payload.bplist").to_vec())
}
#[test]
fn typed_surface_reply_matches_complete_independent_fixture() {
    let source = canvas_core::binary_plist::decode(include_bytes!("fixtures/iosurface-payload/payload.bplist")).unwrap();
    let actual = decode_reply_with(Some(serialized()), Some("ignored"), IOSurfacePayload::decode).unwrap();
    assert_eq!(actual.to_value(), source);
    assert_eq!(actual.surface_id, 12345);
    assert_eq!(actual.size_in_pixels(), (3.0, 2.0));
}
#[test]
fn remote_empty_and_lazy_parse_failure_skip_typed_decoder() {
    let called = Cell::new(0);
    let mut decode = |_: &Value| { called.set(called.get() + 1); Ok::<(), &str>(()) };
    assert_eq!(decode_reply_with(None, Some("remote"), &mut decode), Err(TypedReplyError::Reply(ReplyError::Remote("remote"))));
    assert_eq!(decode_reply_with::<_, &str, _>(None, None, &mut decode), Err(TypedReplyError::Reply(ReplyError::EmptyReply)));
    assert_eq!(decode_reply_with(Some(LazyReply::Serialized(vec![1, 2])), Some("ignored"), &mut decode), Err(TypedReplyError::Decode(DecodeError::Plist(canvas_core::binary_plist::Error::Header))));
    assert_eq!(called.get(), 0);
}
#[test]
fn typed_failure_remains_distinct_from_transport_and_parse_error() {
    let called = Cell::new(0);
    let result = decode_reply_with(Some(LazyReply::Deserialized(BTreeMap::new())), None::<&str>, |v| {
        called.set(called.get() + 1);
        IOSurfacePayload::decode(v)
    });
    assert_eq!(result, Err(TypedReplyError::Payload(SurfaceError::Field(FieldError::Missing("surfaceID")))));
    assert_eq!(called.get(), 1);
}
#[test]
fn void_acknowledgement_does_not_validate_serialized_payload() {
    assert_eq!(acknowledge_reply(Some(LazyReply::Serialized(vec![1, 2])), Some("ignored")), Ok(()));
    assert_eq!(acknowledge_reply::<&str>(None, None), Err(ReplyError::EmptyReply));
    assert_eq!(acknowledge_reply(None, Some("remote")), Err(ReplyError::Remote("remote")));
}
#[test]
fn deserialized_typed_reply_invokes_decoder_once_and_preserves_data() {
    let bytes: Vec<u8> = (0..128).collect();
    let fields = BTreeMap::from([("data".to_string(), Value::Data(bytes.clone()))]);
    let called = Cell::new(0);
    let result = decode_reply_with(Some(LazyReply::Deserialized(fields.clone())), None::<&str>, |v| {
        called.set(called.get() + 1);
        Ok::<_, &str>(v.clone())
    }).unwrap();
    assert_eq!(result, Value::Dictionary(fields));
    assert_eq!(called.get(), 1);
}
