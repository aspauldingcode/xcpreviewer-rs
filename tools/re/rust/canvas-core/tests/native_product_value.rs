use canvas_core::{
    binary_plist,
    payload_codec::Value,
    product_value::{PreviewProductIdentity as Identity, PreviewProductSeed as Seed},
};
#[test]
fn native_product_values_roundtrip_and_rejections() {
    let Value::Dictionary(f) = binary_plist::decode(include_bytes!(
        "fixtures/native_product_value/native.bplist"
    ))
    .unwrap() else {
        panic!()
    };
    let Value::Array(rows) = &f["rows"] else {
        panic!()
    };
    assert_eq!(rows.len(), 82);
    let mut accepted = 0;
    for row in rows {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let result = if row["kind"] == Value::String("product-identity".into()) {
            Identity::decode(&row["input"]).map(|p| p.to_value())
        } else {
            Seed::decode(&row["input"]).map(|p| p.to_value())
        };
        assert_eq!(result.is_ok(), row["accepted"] == Value::Boolean(true));
        if let Ok(value) = result {
            accepted += 1;
            assert_eq!(value, row["canonical"]);
        }
    }
    assert_eq!(accepted, 40);
}
#[test]
fn product_values_require_dictionary() {
    assert!(Identity::decode(&Value::Array(vec![])).is_err());
    assert!(Seed::decode(&Value::Array(vec![])).is_err());
}
#[test]
fn owned_typed_seed_extremes_roundtrip() {
    for content_seed in [0, 1, 1 << 63, u64::MAX] {
        for capabilities_rank in [i64::MIN, -1, 0, 1, i64::MAX] {
            let seed = Seed {
                content_seed,
                capabilities_rank,
            };
            assert_eq!(Seed::decode(&seed.to_value()).unwrap(), seed);
        }
    }
}
