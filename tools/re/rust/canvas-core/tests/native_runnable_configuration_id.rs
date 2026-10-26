//! Actual native typed variant codec and runnable configuration identity outputs.
use canvas_core::{
    binary_plist, canvas_control_state::CanvasControlState, content_results::PreviewVariant,
    payload_codec::Value, request_projection::DisplayMode,
    runnable_configuration_id::RunnableConfigurationId,
};
use std::{
    collections::hash_map::DefaultHasher,
    hash::{Hash, Hasher},
};
fn dictionary(value: &Value) -> &std::collections::BTreeMap<String, Value> {
    let Value::Dictionary(d) = value else {
        panic!()
    };
    d
}
fn array(value: &Value) -> &[Value] {
    let Value::Array(v) = value else { panic!() };
    v
}
fn index(value: &Value) -> usize {
    let Value::Integer(v) = value else { panic!() };
    *v as usize
}
fn hash(value: &RunnableConfigurationId) -> u64 {
    let mut h = DefaultHasher::new();
    value.hash(&mut h);
    h.finish()
}
fn fixture() -> Value {
    binary_plist::decode(include_bytes!(
        "fixtures/native_runnable_configuration_id/native.bplist"
    ))
    .unwrap()
}
#[test]
fn native_id_fields_equality_and_source_configuration_destruction() {
    let value = fixture();
    let v = dictionary(&value);
    let input = dictionary(&v["input"]);
    let boxes = array(&input["boxes"]);
    let sequences = array(&input["sequences"]);
    let variants = array(&input["variants"]);
    let rows = array(&v["rows"]);
    assert_eq!(
        v["privateRunnableConfigurationIDMethodsInvoked"],
        Value::Boolean(true)
    );
    assert_eq!(
        v["nativeConfigurationDestructionReturns"],
        Value::Integer(29)
    );
    assert_eq!(v["sourceStateDestructionReturns"], Value::Integer(24));
    let ids: Vec<_> = array(&input["configurations"])
        .iter()
        .zip(rows)
        .map(|(configuration, row)| {
            let c = dictionary(configuration);
            let row = dictionary(row);
            let mode = match index(&c["mode"]) {
                0 => DisplayMode::Interactive(false),
                1 => DisplayMode::Interactive(true),
                2 => DisplayMode::Static,
                _ => panic!(),
            };
            let overrides: Vec<_> = array(&c["overrides"])
                .iter()
                .map(|i| PreviewVariant::decode(&variants[index(i)]).unwrap())
                .collect();
            let sequence = if index(&c["state"]) == sequences.len() {
                Vec::new()
            } else {
                array(&sequences[index(&c["state"])])
                    .iter()
                    .map(|i| boxes[index(i)].clone())
                    .collect()
            };
            let state = CanvasControlState::decode(&Value::Array(sequence)).unwrap();
            let id = RunnableConfigurationId::new(mode, &overrides, state);
            let Value::Dictionary(mut projection) = id.to_value() else {
                panic!()
            };
            projection.remove("displayMode");
            projection.insert("mode".into(), c["mode"].clone());
            assert_eq!(
                Value::Dictionary(projection),
                Value::Dictionary(row.clone())
            );
            id
        })
        .collect();
    for pair in array(&v["pairs"]) {
        let pair = dictionary(pair);
        let (i, j) = (index(&pair["left"]), index(&pair["right"]));
        assert_eq!(
            ids[i] == ids[j],
            pair["equal"] == Value::Boolean(true),
            "native pair{i}/{j}"
        );
        if ids[i] == ids[j] {
            assert_eq!(hash(&ids[i]), hash(&ids[j]));
            assert_eq!(pair["sameHash"], Value::Boolean(true));
        }
    }
    assert_eq!(ids.len(), 29);
    assert_eq!(array(&v["pairs"]).len(), 841);
    for i in [1, 2, 3, 27] {
        assert_eq!(ids[0], ids[i]);
    }
    for i in [4, 5, 6, 7, 8, 9, 10, 11, 14] {
        assert_ne!(ids[0], ids[i]);
    }
    assert_eq!(ids[12], ids[13]);
    assert_ne!(ids[12].override_ids(), ids[13].override_ids());
    assert_ne!(ids[7], ids[8]);
    assert_ne!(ids[19], ids[21]);
}
#[test]
fn actual_private_typed_variant_codec_controls() {
    let value = fixture();
    let v = dictionary(&value);
    for row in array(&v["variants"]) {
        let row = dictionary(row);
        assert_eq!(
            PreviewVariant::decode(&row["input"]).unwrap().to_value(),
            row["canonical"]
        );
    }
    assert_eq!(array(&v["variants"]).len(), 8);
}
