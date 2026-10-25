use canvas_core::{
    human_readable_error::{extract_encoded_with, ARCHIVE_KEY},
    payload_codec::Value as V,
    service_reply_error::ServiceReplyError,
    transport_reply::{select_reply_projecting_error, LazyReply, ReplyError},
};
use std::{cell::Cell, collections::BTreeMap};

#[test]
fn exact_archive_key_and_dictionary_gate_skip_decoder() {
    for fields in [
        BTreeMap::new(),
        BTreeMap::from([(
            "uvhumanreadableerror".into(),
            V::Dictionary(BTreeMap::new()),
        )]),
        BTreeMap::from([(ARCHIVE_KEY.into(), V::String("archive".into()))]),
        BTreeMap::from([(ARCHIVE_KEY.into(), V::Data(vec![]))]),
        BTreeMap::from([(ARCHIVE_KEY.into(), V::Array(vec![]))]),
        BTreeMap::from([(ARCHIVE_KEY.into(), V::Null)]),
    ] {
        assert_eq!(
            extract_encoded_with::<(), ()>(&fields, |_| panic!("not a dictionary archive")),
            None
        );
    }
}
#[test]
fn empty_dictionary_reaches_decoder_and_failures_allow_fallback() {
    let fields = BTreeMap::from([(ARCHIVE_KEY.into(), V::Dictionary(BTreeMap::new()))]);
    let calls = Cell::new(0);
    assert_eq!(
        extract_encoded_with::<(), _>(&fields, |archive| {
            calls.set(calls.get() + 1);
            assert!(archive.is_empty());
            Err("missing errorType")
        }),
        None
    );
    assert_eq!(calls.get(), 1);
    assert_eq!(extract_encoded_with(&fields, |_| Ok::<_, ()>(17)), Some(17));
}
#[test]
fn service_error_user_info_retains_complete_archive_for_caller_decoder() {
    let archive = BTreeMap::from([
        ("errorType".into(), V::String("caller-owned".into())),
        ("unknown".into(), V::Data(vec![0, 128, 255])),
        (
            "nested".into(),
            V::Dictionary(BTreeMap::from([("code".into(), V::Integer(i64::MIN))])),
        ),
    ]);
    let error = ServiceReplyError {
        domain: "owned".into(),
        code: 17,
        user_info: BTreeMap::from([(ARCHIVE_KEY.into(), V::Dictionary(archive.clone()))]),
    };
    let restored = ServiceReplyError::recognize(&error.to_dictionary()).unwrap();
    assert_eq!(
        extract_encoded_with(&restored.user_info, |fields| {
            assert_eq!(fields, &archive);
            Ok::<_, ()>(fields.clone())
        }),
        Some(archive)
    );
    assert_eq!(restored, error);
}
#[test]
fn nullable_reply_projects_error_only_after_payload_absence() {
    let payload = LazyReply::Serialized(vec![]);
    for error in [None, Some(17)] {
        assert_eq!(
            select_reply_projecting_error(Some(payload.clone()), error, |_| -> String {
                panic!("payload wins")
            }),
            Ok(payload.clone())
        );
    }
    assert_eq!(
        select_reply_projecting_error(None, None::<()>, |_| -> String { panic!("no error") }),
        Err(ReplyError::EmptyReply)
    );
    let calls = Cell::new(0);
    assert_eq!(
        select_reply_projecting_error(None, Some(17), |value| {
            calls.set(calls.get() + 1);
            value.to_string()
        }),
        Err(ReplyError::Remote("17".into()))
    );
    assert_eq!(calls.get(), 1);
    // A selected malformed payload still bypasses projection; parsing is later.
    let selected =
        select_reply_projecting_error(Some(payload), Some(17), |_| -> String { panic!() }).unwrap();
    assert!(selected.property_list().is_err());
}
