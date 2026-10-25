use canvas_core::{
    binary_plist,
    binary_plist_writer::{encode, encode_with_limits, Error, Limits},
    payload_codec::Value as V,
};
use std::collections::BTreeMap;
#[test]
fn scalar_boundaries_unicode_and_nested_values_round_trip() {
    let v = V::Dictionary(BTreeMap::from([
        (
            "ints".into(),
            V::Array(
                [
                    i64::MIN,
                    -1,
                    0,
                    1,
                    127,
                    128,
                    255,
                    256,
                    65535,
                    65536,
                    i64::MAX,
                ]
                .map(V::Integer)
                .to_vec(),
            ),
        ),
        (
            "text".into(),
            V::String(format!("{}按钮🪨\0\n", "a".repeat(20))),
        ),
        (
            "data".into(),
            V::Data((0..512).map(|i| (i % 256) as u8).collect()),
        ),
        ("date".into(), V::Date(17.5)),
        ("empty".into(), V::Dictionary(BTreeMap::new())),
        (
            "bool".into(),
            V::Array(vec![V::Boolean(false), V::Boolean(true)]),
        ),
    ]));
    assert_eq!(binary_plist::decode(&encode(&v).unwrap()), Ok(v.clone()));
    assert_eq!(encode(&v), encode(&v));
}
#[test]
fn length_reference_and_offset_width_transitions_are_real_round_trips() {
    for n in [0, 14, 15, 255, 256, 300] {
        let v = V::Array((0..n).map(|i| V::String(format!("owned-{i}"))).collect());
        let b = encode(&v).unwrap();
        assert_eq!(binary_plist::decode(&b), Ok(v));
        assert_eq!(b[b.len() - 25], if n <= 255 { 1 } else { 2 });
    }
    let root = V::Data(vec![17; 512]);
    let b = encode(&root).unwrap();
    assert_eq!(b[b.len() - 26], 2);
    assert_eq!(binary_plist::decode(&b), Ok(root));
    let v = V::Array(vec![
        V::Data(vec![17; 70000]),
        V::String("after wide offset".into()),
    ]);
    let b = encode(&v).unwrap();
    assert_eq!(b[b.len() - 26], 4);
    assert_eq!(binary_plist::decode(&b), Ok(v));
}
#[test]
fn real_and_date_bits_include_negative_zero_and_subnormal() {
    for bits in [
        0,
        0x8000000000000000,
        1,
        3.5_f64.to_bits(),
        f64::MAX.to_bits(),
    ] {
        let value = f64::from_bits(bits);
        for v in [V::Real(value), V::Date(value)] {
            let b = encode(&v).unwrap();
            let got = binary_plist::decode(&b).unwrap();
            let number = match got {
                V::Real(v) | V::Date(v) => v,
                _ => panic!(),
            };
            assert_eq!(number.to_bits(), bits);
        }
    }
}
#[test]
fn limits_charge_dictionary_keys_and_complete_output_including_trailer() {
    let text = V::String("界".repeat(100));
    let encoded = encode(&text).unwrap();
    assert_eq!(
        encode_with_limits(
            &text,
            Limits {
                bytes: encoded.len(),
                ..Limits::default()
            }
        )
        .unwrap(),
        encoded
    );
    let v = V::Dictionary(BTreeMap::from([("key".into(), V::Boolean(true))]));
    let bytes = encode(&v).unwrap();
    let limits = Limits {
        objects: 3,
        bytes: bytes.len(),
        depth: 1,
    };
    assert_eq!(encode_with_limits(&v, limits).unwrap(), bytes);
    for limits in [
        Limits {
            objects: 2,
            ..limits
        },
        Limits {
            bytes: bytes.len() - 1,
            ..limits
        },
        Limits { depth: 0, ..limits },
        Limits {
            objects: 100001,
            ..limits
        },
    ] {
        assert_eq!(encode_with_limits(&v, limits), Err(Error::Limit));
    }
}
#[test]
fn null_nonfinite_and_excessive_depth_are_explicit_rejections() {
    assert_eq!(encode(&V::Null), Err(Error::Null));
    for n in [f64::NAN, f64::INFINITY, f64::NEG_INFINITY] {
        assert_eq!(encode(&V::Real(n)), Err(Error::NonFinite));
        assert_eq!(encode(&V::Date(n)), Err(Error::NonFinite));
    }
    let mut v = V::Boolean(true);
    for _ in 0..64 {
        v = V::Array(vec![v]);
    }
    assert!(encode(&v).is_ok());
    v = V::Array(vec![v]);
    assert_eq!(encode(&v), Err(Error::Limit));
}
#[test]
fn real_service_error_can_encode_and_classify_without_fixture_encoder() {
    use canvas_core::{
        service_reply_error::ServiceReplyError,
        service_reply_failure::{
            classify_service_xpc_dictionary_with, ReplyRepresentation, ServiceReplyFailure,
        },
        service_response::send_service_response_binary,
    };
    let error = ServiceReplyError {
        domain: "owned/🪨".into(),
        code: i64::MIN,
        user_info: BTreeMap::from([
            ("bytes".into(), V::Data((0..128).collect())),
            ("reason".into(), V::String("owned".into())),
        ]),
    };
    let mut wire = BTreeMap::new();
    let got =
        send_service_response_binary(true, None, Some(error.clone()), &mut wire, Some, |wire| {
            classify_service_xpc_dictionary_with(
                wire,
                ReplyRepresentation::SerializedData,
                binary_plist::decode,
                || panic!(),
            )
        });
    assert_eq!(got, Some((None, Some(ServiceReplyFailure::Remote(error)))));
}
