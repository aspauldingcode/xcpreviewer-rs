use canvas_core::{
    binary_plist,
    payload_codec::Value,
    remote_crash::{Error, ScreenshotRequest},
};
#[test]
fn binary_dates_match_all_native_absolute_time_bits() {
    let Value::Array(values) =
        binary_plist::decode(include_bytes!("fixtures/crash-report/dates.bplist")).unwrap()
    else {
        panic!("array")
    };
    let expected = [
        0xc1cd27e440000000,
        0,
        0x3fc0000000000000,
        0xbfe0000000000000,
        0x41d16c0ddfc00000,
        0x41c84322f864fdf4,
    ];
    assert_eq!(values.len(), expected.len());
    for (value, bits) in values.iter().zip(expected) {
        let Value::Date(date) = value else {
            panic!("date type must remain distinct from real")
        };
        assert_eq!(date.to_bits(), bits);
    }
}
#[test]
fn date_tag_is_exact_and_truncation_never_accepts_a_partial_date() {
    let source = include_bytes!("fixtures/crash-report/dates.bplist");
    for n in 0..source.len() {
        assert!(binary_plist::decode(&source[..n]).is_err());
    }
    assert_ne!(Value::Date(0.0), Value::Real(0.0));
}
#[test]
fn screenshot_request_round_trip_matches_independent_binary_fixture() {
    let bytes = include_bytes!("fixtures/crash-report/screenshot-request.bplist");
    assert_eq!(
        ScreenshotRequest::decode_binary(bytes),
        Ok(ScreenshotRequest)
    );
    assert_eq!(
        ScreenshotRequest.to_value(),
        binary_plist::decode(bytes).unwrap()
    );
}
#[test]
fn unrelated_fields_are_ignored_but_discriminants_are_not() {
    let mut value = ScreenshotRequest.to_value();
    let Value::Dictionary(ref mut d) = value else {
        panic!("dictionary")
    };
    d.insert(
        "crashReport".into(),
        Value::String("unused wrong type".into()),
    );
    assert_eq!(ScreenshotRequest::decode(&value), Ok(ScreenshotRequest));
    let Value::Dictionary(ref mut d) = value else {
        unreachable!()
    };
    d.insert(
        "discriminant".into(),
        Value::String("symbolicateCrashedDiagnostics".into()),
    );
    assert_eq!(
        ScreenshotRequest::decode(&value),
        Err(Error::UnsupportedCrashReport)
    );
    let Value::Dictionary(ref mut d) = value else {
        unreachable!()
    };
    d.insert("discriminant".into(), Value::String("subscribe".into()));
    assert_eq!(
        ScreenshotRequest::decode(&value),
        Err(Error::UnknownDiscriminant("subscribe".into()))
    );
}
