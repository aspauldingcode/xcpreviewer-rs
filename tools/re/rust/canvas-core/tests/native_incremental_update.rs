use canvas_core::{
    binary_plist,
    incremental_update::{Error, PreviewIncrementalUpdate as Update},
    payload_codec::Value,
};
fn equal(a: &Value, b: &Value) -> bool {
    match (a, b) {
        (Value::Real(a), Value::Real(b)) => a.to_bits() == b.to_bits(),
        (Value::Dictionary(a), Value::Dictionary(b)) => {
            a.len() == b.len() && a.iter().all(|(k, v)| b.get(k).is_some_and(|x| equal(v, x)))
        }
        _ => a == b,
    }
}
#[test]
fn native_single_entries_and_explicit_multikey_restriction() {
    let Value::Dictionary(f) = binary_plist::decode(include_bytes!(
        "fixtures/native_incremental_update/native.bplist"
    ))
    .unwrap() else {
        panic!()
    };
    let Value::Array(rows) = &f["rows"] else {
        panic!()
    };
    assert_eq!(rows.len(), 109);
    let (mut accepted, mut rejected, mut ambiguous) = (0, 0, 0);
    for row in rows {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let result = Update::decode_single_entry(&row["input"]);
        if let Err(Error::AmbiguousNativeSelection { entries: 3 }) = result {
            assert_eq!(row["accepted"], Value::Boolean(true));
            ambiguous += 1;
            continue;
        }
        assert_eq!(result.is_ok(), row["accepted"] == Value::Boolean(true));
        if let Ok(update) = result {
            accepted += 1;
            assert!(equal(&update.to_value(), &row["canonical"]));
            assert!(equal(&update.to_value(), &row["input"]))
        } else {
            rejected += 1
        }
    }
    assert_eq!((accepted, rejected, ambiguous), (62, 31, 16));
}
#[test]
fn constructor_and_schema_limits() {
    assert_eq!(
        Update::decode_single_entry(&Value::Array(vec![])).unwrap_err(),
        Error::Dictionary
    );
    assert_eq!(
        Update::new("owned".into(), Value::Null).unwrap_err(),
        Error::UnsupportedValue
    );
    let v = Value::Real(f64::from_bits(0x7ff8000000000001));
    let u = Update::new("".into(), v.clone()).unwrap();
    assert_eq!(u.key(), "");
    assert!(equal(u.value(), &v));
}

#[test]
fn codec_only_nonfinite_writer_and_generic_limits() {
    use canvas_core::binary_plist_writer::{self as writer, Error as WError};
    for bits in [
        0x7ff0000000000000,
        0xfff0000000000000,
        0x7ff8000000000001,
        0x8000000000000000,
    ] {
        let value = Value::Real(f64::from_bits(bits));
        let update = Update::new("owned".into(), value.clone()).unwrap();
        let decoded = binary_plist::decode(&update.to_binary_plist().unwrap()).unwrap();
        assert!(equal(&decoded, &update.to_value()));
        if !f64::from_bits(bits).is_finite() {
            assert_eq!(writer::encode(&value), Err(WError::NonFinite));
        }
    }
    assert_eq!(
        writer::encode(&Value::Date(f64::INFINITY)),
        Err(WError::NonFinite)
    );
}
