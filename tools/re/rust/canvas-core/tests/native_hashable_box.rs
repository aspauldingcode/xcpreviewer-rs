//! Actual shipped HashableBox<PlistValueBox> outputs; scoped finite profile only.
use canvas_core::{
    binary_plist,
    hashable_plist_box::{Error, HashablePlistBox},
    payload_codec::Value,
    plist_value_box::PlistValueBox,
};
use std::{
    collections::{hash_map::DefaultHasher, BTreeMap},
    hash::{Hash, Hasher},
};
fn hash(b: &HashablePlistBox) -> u64 {
    let mut h = DefaultHasher::new();
    b.hash(&mut h);
    h.finish()
}
#[test]
fn native_value_equality_and_hash_law() {
    let Value::Dictionary(v) =
        binary_plist::decode(include_bytes!("fixtures/native_hashable_box/native.bplist")).unwrap()
    else {
        panic!()
    };
    let Value::Array(rows) = &v["rows"] else {
        panic!()
    };
    let boxes: Vec<_> = rows
        .iter()
        .map(|r| {
            let Value::Dictionary(r) = r else { panic!() };
            let value = PlistValueBox::decode(&r["input"]).unwrap();
            assert_eq!(value.to_value(), r["roundtrip"]);
            HashablePlistBox::new(value).unwrap()
        })
        .collect();
    let Value::Array(pairs) = &v["pairs"] else {
        panic!()
    };
    let mut comparisons = 0;
    for pair in pairs {
        let Value::Dictionary(p) = pair else { panic!() };
        let (Value::Integer(i), Value::Integer(j)) = (&p["left"], &p["right"]) else {
            panic!()
        };
        let (a, b) = (&boxes[*i as usize], &boxes[*j as usize]);
        comparisons += 1;
        assert_eq!(
            a == b,
            p["equal"] == Value::Boolean(true),
            "native pair {i}/{j}"
        );
        if a == b {
            assert_eq!(hash(a), hash(b));
            assert_eq!(p["sameHash"], Value::Boolean(true));
        }
    }
    assert_eq!(boxes.len(), 96);
    assert_eq!(comparisons, 9216);
    assert_eq!(pairs.len(), 9216);
}
#[test]
fn unsupported_profile_rejected_without_lawless_keys() {
    for (value, error) in [
        (Value::Null, Error::Null),
        (Value::Real(f64::NAN), Error::Nonfinite),
        (Value::Real(f64::INFINITY), Error::Nonfinite),
        (Value::Date(f64::NEG_INFINITY), Error::Nonfinite),
        (
            Value::Dictionary(BTreeMap::from([
                ("é".into(), Value::Integer(1)),
                ("e\u{301}".into(), Value::Integer(2)),
            ])),
            Error::CanonicalKeyCollision,
        ),
    ] {
        assert_eq!(
            HashablePlistBox::new(PlistValueBox::from_value(value)).unwrap_err(),
            error
        );
    }
    let mut value = Value::Integer(0);
    for _ in 0..65 {
        value = Value::Array(vec![value]);
    }
    assert_eq!(
        HashablePlistBox::new(PlistValueBox::from_value(value)).unwrap_err(),
        Error::Depth
    );
}

#[test]
fn native_numeric_projection_types_and_public_bridge() {
    let Value::Dictionary(v) =
        binary_plist::decode(include_bytes!("fixtures/native_hashable_box/native.bplist")).unwrap()
    else {
        panic!()
    };
    let Value::Array(rows) = &v["rows"] else {
        panic!()
    };
    let mut numeric = 0;
    for row in rows {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        assert_eq!(row["publicProjectionEqual"], Value::Boolean(true));
        assert_eq!(row["snapshot"], row["publicProjection"]);
        let Value::Dictionary(input) = &row["input"] else {
            panic!()
        };
        if input.len() != 1 {
            continue;
        }
        let Some(Value::Integer(_) | Value::Unsigned(_) | Value::Real(_)) = input.get("value")
        else {
            continue;
        };
        let Value::Dictionary(snapshot) = &row["snapshot"] else {
            panic!()
        };
        let Value::Dictionary(fields) = &snapshot["dictionary"] else {
            panic!()
        };
        let Value::Dictionary(value) = &fields["value"] else {
            panic!()
        };
        let Value::String(kind) = &value["swiftType"] else {
            panic!()
        };
        let Value::String(text) = &value["stringValue"] else {
            panic!()
        };
        let projected = match kind.as_str() {
            "Swift.Int64" => Value::Integer(text.parse().unwrap()),
            "Swift.UInt64" => Value::Unsigned(text.parse().unwrap()),
            "Swift.Double" => {
                let Value::String(text) = &value["doubleValue"] else {
                    panic!()
                };
                Value::Real(text.parse().unwrap())
            }
            _ => panic!("unexpected numeric snapshot type {kind}"),
        };
        assert_eq!(
            HashablePlistBox::new(PlistValueBox::decode(&row["input"]).unwrap()).unwrap(),
            HashablePlistBox::new(PlistValueBox::from_value(projected)).unwrap()
        );
        numeric += 1;
    }
    assert!(numeric >= 60);
}
