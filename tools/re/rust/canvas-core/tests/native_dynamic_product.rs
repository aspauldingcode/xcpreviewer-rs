use canvas_core::{
    dynamic_product::DynamicLoadablePreviewProduct as Product,
    payload_codec::Value,
};
#[test]
fn native_dynamic_product_roundtrips_and_rejections() {
    let Value::Dictionary(f) = canvas_core::binary_plist::decode(include_bytes!(
        "fixtures/native_dynamic_product/native.bplist"
    ))
    .unwrap() else {
        panic!()
    };
    let Value::Array(rows) = &f["rows"] else {
        panic!()
    };
    assert_eq!(rows.len(), 43);
    let mut accepted = 0;
    for row in rows {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let result = Product::decode(&row["input"]);
        assert_eq!(result.is_ok(), row["accepted"] == Value::Boolean(true));
        if let Ok(p) = result {
            accepted += 1;
            assert_eq!(p.to_value(), row["canonical"]);
            assert_eq!(Product::decode(&p.to_value()).unwrap(), p);
        }
    }
    assert_eq!(accepted, 17);
}
#[test]
fn product_requires_dictionary() {
    assert!(Product::decode(&Value::Array(vec![])).is_err());
}
