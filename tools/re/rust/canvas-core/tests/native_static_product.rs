use canvas_core::{
    binary_plist,
    payload_codec::Value,
    static_product::{Error, StaticLinkablePreviewProduct as Product},
};
fn ordered(mut value: Value) -> Value {
    match &mut value {
        Value::Dictionary(f) => {
            for (k, v) in f {
                if k == "sourceFilePaths" || k == "linkerFlags" {
                    if let Value::Array(a) = v {
                        a.sort_by(|a, b| match (a, b) {
                            (Value::String(a), Value::String(b)) => a.cmp(b),
                            _ => panic!(),
                        });
                    }
                } else {
                    *v = ordered(v.clone());
                }
            }
        }
        Value::Array(a) => {
            for v in a {
                *v = ordered(v.clone());
            }
        }
        _ => {}
    }
    value
}
#[test]
fn native_static_product_values_and_nested_rejections() {
    let Value::Dictionary(f) = binary_plist::decode(include_bytes!(
        "fixtures/native_static_product/native.bplist"
    ))
    .unwrap() else {
        panic!()
    };
    let Value::Array(rows) = &f["rows"] else {
        panic!()
    };
    assert_eq!(rows.len(), 201);
    let mut accepted = 0;
    let mut late_error = false;
    for row in rows {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let result = Product::decode(&row["input"]);
        assert_eq!(result.is_ok(), row["accepted"] == Value::Boolean(true));
        if let Err(Error::Target { index: 1, .. }) = &result {
            late_error = true;
        }
        if let Ok(product) = result {
            accepted += 1;
            assert_eq!(
                ordered(product.to_value()),
                ordered(row["canonical"].clone())
            );
        }
    }
    assert_eq!(accepted, 75);
    assert!(late_error);
}
#[test]
fn static_product_default_and_envelope_contract() {
    assert_eq!(
        Product::default().to_value(),
        Value::Dictionary(Default::default())
    );
    assert!(Product::decode(&Value::Array(vec![])).is_err());
}
