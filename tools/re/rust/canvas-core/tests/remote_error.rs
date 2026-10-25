use canvas_core::{
    binary_plist, binary_plist_writer,
    human_readable_error::{extract_encoded_with, ARCHIVE_KEY},
    payload_codec::Value as V,
    remote_error::{Error, RemoteErrorLeaf, Severity},
    service_reply_error::ServiceReplyError,
};
use std::collections::BTreeMap;
fn leaf() -> BTreeMap<String, V> {
    BTreeMap::from([("errorType".into(), V::String("leaf".into()))])
}
#[test]
fn absent_leaf_fields_have_asymmetric_flag_defaults() {
    let value = RemoteErrorLeaf::from_dictionary(&leaf()).unwrap();
    assert_eq!(value.error_type_description, "[Remote] Unknown Error");
    assert!(value.is_potential_crash);
    assert!(!value.is_native);
    assert_eq!(value.options, None);
    assert_eq!(value.severity, None);
    assert_eq!(value.high_value_title, None);
    assert_eq!(value.to_dictionary().len(), 4);
}
#[test]
fn title_prefix_is_exact_idempotent_and_empty_is_present() {
    for (input, expected) in [
        ("owned 🪨", "[Remote] owned 🪨"),
        ("[Remote] owned", "[Remote] owned"),
        ("", "[Remote] "),
        ("[Remote]", "[Remote] [Remote]"),
        ("[remote] x", "[Remote] [remote] x"),
    ] {
        let mut fields = leaf();
        fields.insert("errorTypeDescription".into(), V::String(input.into()));
        let value = RemoteErrorLeaf::from_dictionary(&fields).unwrap();
        assert_eq!(value.error_type_description, expected);
        assert_eq!(
            RemoteErrorLeaf::from_dictionary(&value.to_dictionary()).unwrap(),
            value
        );
    }
}
#[test]
fn complete_leaf_round_trips_and_extra_keys_are_ignored() {
    let mut fields = leaf();
    for (k, v) in [
        ("errorTypeDescription", "owned"),
        ("highValueTitle", ""),
        ("lowValueTitle", "low"),
        ("additionalInfo", "info\0🪨"),
        ("additionalDiagnostics", "details\n"),
        ("severity", "info"),
    ] {
        fields.insert(k.into(), V::String(v.into()));
    }
    fields.insert("options".into(), V::Integer(i64::MIN));
    fields.insert("isPotentialCrash".into(), V::Boolean(false));
    fields.insert("isNative".into(), V::Boolean(true));
    fields.insert("unknown".into(), V::Data(vec![0, 255]));
    let value = RemoteErrorLeaf::from_dictionary(&fields).unwrap();
    assert_eq!(value.high_value_title, Some("".into()));
    assert_eq!(value.options, Some(i64::MIN));
    assert_eq!(value.severity, Some(Severity::Info));
    assert!(!value.is_potential_crash);
    assert!(value.is_native);
    let encoded = value.to_dictionary();
    assert_eq!(encoded.len(), 10);
    assert!(!encoded.contains_key("unknown"));
    let V::Dictionary(decoded) =
        binary_plist::decode(&binary_plist_writer::encode_dictionary(&encoded).unwrap()).unwrap()
    else {
        panic!()
    };
    assert_eq!(RemoteErrorLeaf::from_dictionary(&decoded).unwrap(), value);
}
#[test]
fn present_invalid_optional_values_never_become_defaults() {
    for key in [
        "errorTypeDescription",
        "highValueTitle",
        "lowValueTitle",
        "additionalInfo",
        "additionalDiagnostics",
        "options",
        "severity",
        "isPotentialCrash",
        "isNative",
    ] {
        let mut fields = leaf();
        fields.insert(key.into(), V::Null);
        assert_eq!(
            RemoteErrorLeaf::from_dictionary(&fields),
            Err(Error::Type(key))
        );
    }
    let mut fields = leaf();
    fields.insert("severity".into(), V::String("warning".into()));
    assert_eq!(
        RemoteErrorLeaf::from_dictionary(&fields),
        Err(Error::Severity)
    );
    for (key, bad) in [("options", V::Boolean(true)), ("isNative", V::Integer(1))] {
        let mut fields = leaf();
        fields.insert(key.into(), bad);
        assert_eq!(
            RemoteErrorLeaf::from_dictionary(&fields),
            Err(Error::Type(key))
        );
    }
}
#[test]
fn discriminator_routes_wrapper_explicitly() {
    assert_eq!(
        RemoteErrorLeaf::from_dictionary(&BTreeMap::new()),
        Err(Error::MissingDiscriminant)
    );
    for kind in ["wrapper", "unknown"] {
        let fields = BTreeMap::from([("errorType".into(), V::String(kind.into()))]);
        assert_eq!(
            RemoteErrorLeaf::from_dictionary(&fields),
            Err(if kind == "wrapper" {
                Error::UnsupportedWrapper
            } else {
                Error::InvalidDiscriminant
            })
        );
    }
}
#[test]
fn service_error_extraction_uses_real_leaf_decoder_and_suppresses_rejection() {
    let mut fields = leaf();
    fields.insert("options".into(), V::Integer(i64::MAX));
    fields.insert("severity".into(), V::String("error".into()));
    let error = ServiceReplyError {
        domain: "owned".into(),
        code: 17,
        user_info: BTreeMap::from([(ARCHIVE_KEY.into(), V::Dictionary(fields.clone()))]),
    };
    let projected = ServiceReplyError::recognize(&error.to_dictionary()).unwrap();
    let remote =
        extract_encoded_with(&projected.user_info, RemoteErrorLeaf::from_dictionary).unwrap();
    assert_eq!(remote.options, Some(i64::MAX));
    assert_eq!(remote.severity, Some(Severity::Error));
    fields.insert("errorType".into(), V::String("wrapper".into()));
    assert_eq!(
        extract_encoded_with(
            &BTreeMap::from([(ARCHIVE_KEY.into(), V::Dictionary(fields))]),
            RemoteErrorLeaf::from_dictionary
        ),
        None
    );
}

#[test]
fn native_prefix_scalar_boundaries_and_partial_characters() {
    let V::Array(raw) =
        binary_plist::decode(include_bytes!("fixtures/remote-prefix/boundaries.bplist")).unwrap()
    else {
        panic!()
    };
    let ranges: Vec<(u32, u32)> = raw
        .into_iter()
        .map(|entry| {
            let V::Array(pair) = entry else { panic!() };
            let [V::Integer(a), V::Integer(b)] = pair.as_slice() else {
                panic!()
            };
            (*a as u32, *b as u32)
        })
        .collect();
    assert_eq!(ranges.len(), 334);
    for &(a, b) in &ranges {
        for code in [a.saturating_sub(1), a, b, b + 1] {
            let Some(scalar) = char::from_u32(code) else {
                continue;
            };
            let title = format!("[Remote] {scalar}x");
            let rejected = ranges.iter().any(|&(a, b)| a <= code && code <= b);
            let mut fields = leaf();
            fields.insert("errorTypeDescription".into(), V::String(title.clone()));
            let value = RemoteErrorLeaf::from_dictionary(&fields).unwrap();
            assert_eq!(
                value.error_type_description,
                if rejected {
                    format!("[Remote] {title}")
                } else {
                    title
                },
                "U+{code:04X}"
            );
        }
    }
    let mut fields = leaf();
    fields.insert(
        "errorTypeDescription".into(),
        V::String("[Remote] 🪨".into()),
    );
    assert_eq!(
        RemoteErrorLeaf::from_dictionary(&fields)
            .unwrap()
            .error_type_description,
        "[Remote] 🪨"
    );
}
