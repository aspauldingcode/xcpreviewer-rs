use canvas_core::{
    binary_plist,
    error_archive::{Error, ErrorArchive as A, Limits},
    human_readable_error::{extract_encoded_with, ARCHIVE_KEY},
    payload_codec::Value as V,
    remote_error::{Error as LeafError, RemoteErrorLeaf},
    service_reply_error::ServiceReplyError,
    service_reply_failure::{
        classify_service_observed_data_with, ReplyRepresentation, ServiceReplyFailure,
    },
    service_response::send_service_response_binary,
    settings_xpc::XpcValue,
};
use std::collections::BTreeMap;
fn leaf(title: &str, crash: bool, native: bool) -> A {
    A::Leaf(
        RemoteErrorLeaf::from_dictionary(&BTreeMap::from([
            ("errorType".into(), V::String("leaf".into())),
            ("errorTypeDescription".into(), V::String(title.into())),
            ("isPotentialCrash".into(), V::Boolean(crash)),
            ("isNative".into(), V::Boolean(native)),
        ]))
        .unwrap(),
    )
}
fn wrapper(main: A, underlying: A) -> A {
    A::Wrapper {
        main: Box::new(main),
        underlying: Box::new(underlying),
    }
}
#[test]
fn nested_wrappers_keep_both_children_and_project_flags_by_branch() {
    let value = wrapper(
        wrapper(leaf("main", true, true), leaf("inner cause", false, false)),
        leaf("outer cause 🪨", false, false),
    );
    assert!(!value.is_potential_crash());
    assert!(value.is_native());
    let mut fields = value.to_dictionary().unwrap();
    assert_eq!(fields.len(), 3);
    assert!(fields.contains_key("underlying"));
    assert!(!fields.contains_key("cause"));
    fields.insert("extra".into(), V::Null);
    assert_eq!(A::from_dictionary(&fields).unwrap(), value);
    let reversed = wrapper(leaf("main", false, false), leaf("cause", true, true));
    assert!(reversed.is_potential_crash());
    assert!(!reversed.is_native());
}
#[test]
fn required_child_shape_validation_precedes_child_semantics() {
    let mut fields = BTreeMap::from([("errorType".into(), V::String("wrapper".into()))]);
    assert_eq!(A::from_dictionary(&fields), Err(Error::Missing("main")));
    fields.insert("main".into(), V::Dictionary(BTreeMap::new()));
    assert_eq!(
        A::from_dictionary(&fields),
        Err(Error::Missing("underlying"))
    );
    fields.insert("cause".into(), V::Dictionary(BTreeMap::new()));
    assert_eq!(
        A::from_dictionary(&fields),
        Err(Error::Missing("underlying"))
    );
    fields.insert("underlying".into(), V::Null);
    assert_eq!(A::from_dictionary(&fields), Err(Error::Type("underlying")));
    fields.insert("underlying".into(), V::Dictionary(BTreeMap::new()));
    assert_eq!(
        A::from_dictionary(&fields),
        Err(Error::Leaf(LeafError::MissingDiscriminant))
    );
    fields.insert("main".into(), V::Null);
    assert_eq!(A::from_dictionary(&fields), Err(Error::Type("main")));
}
#[test]
fn main_decode_failure_precedes_underlying_decode_failure() {
    let fields = BTreeMap::from([
        ("errorType".into(), V::String("wrapper".into())),
        (
            "main".into(),
            V::Dictionary(BTreeMap::from([(
                "errorType".into(),
                V::String("unknown".into()),
            )])),
        ),
        ("underlying".into(), V::Dictionary(BTreeMap::new())),
    ]);
    assert_eq!(
        A::from_dictionary(&fields),
        Err(Error::Leaf(LeafError::InvalidDiscriminant))
    );
}
#[test]
fn archive_node_and_depth_limits_apply_to_decode_and_encode() {
    let value = wrapper(leaf("main", false, false), leaf("cause", false, false));
    let fields = value.to_dictionary().unwrap();
    for limits in [
        Limits {
            nodes: 0,
            depth: 64,
        },
        Limits {
            nodes: 2,
            depth: 64,
        },
        Limits { nodes: 3, depth: 0 },
    ] {
        assert_eq!(
            A::from_dictionary_with_limits(&fields, limits),
            Err(Error::Limit)
        );
        assert_eq!(value.to_dictionary_with_limits(limits), Err(Error::Limit));
    }
    let limits = Limits { nodes: 3, depth: 1 };
    assert_eq!(
        A::from_dictionary_with_limits(&fields, limits).unwrap(),
        value
    );
    assert_eq!(value.to_dictionary_with_limits(limits).unwrap(), fields);
}
#[test]
fn response_error_round_trip_extracts_recursive_archive_without_losing_outer_error() {
    let archive = wrapper(
        leaf("main", true, false),
        wrapper(leaf("cause", false, true), leaf("root", false, false)),
    );
    let error = ServiceReplyError {
        domain: "owned/wrapper".into(),
        code: i64::MIN,
        user_info: BTreeMap::from([
            (
                ARCHIVE_KEY.into(),
                V::Dictionary(archive.to_dictionary().unwrap()),
            ),
            ("other".into(), V::Data(vec![0, 128, 255])),
        ]),
    };
    let mut wire = BTreeMap::new();
    assert_eq!(
        send_service_response_binary(true, None, Some(error.clone()), &mut wire, Some, |_| ()),
        Some(())
    );
    let XpcValue::Data(bytes) = &wire["data"] else {
        panic!()
    };
    let (payload, failure) = classify_service_observed_data_with(
        Some(bytes),
        ReplyRepresentation::SerializedData,
        binary_plist::decode,
        || panic!(),
    );
    assert!(payload.is_none());
    let Some(ServiceReplyFailure::Remote(restored)) = failure else {
        panic!()
    };
    assert_eq!(restored, error);
    assert_eq!(
        extract_encoded_with(&restored.user_info, A::from_dictionary),
        Some(archive)
    );
}
