use canvas_core::{
    binary_plist,
    payload_codec::Value,
    plist_value_box::PlistValueBox,
    update_seed::{next_host_update_seed, HostUpdateGroupSeed, HostUpdateSeed, UpdateSeeds},
};
use std::collections::BTreeMap;
fn dict(v: &Value) -> &BTreeMap<String, Value> {
    let Value::Dictionary(v) = v else { panic!() };
    v
}
fn array(v: &Value) -> &[Value] {
    let Value::Array(v) = v else { panic!() };
    v
}
fn number(v: &Value) -> u64 {
    HostUpdateSeed::decode(v).unwrap().value()
}
fn fixture() -> Value {
    binary_plist::decode(include_bytes!("fixtures/native_update_seeds/native.bplist")).unwrap()
}
#[test]
fn actual_native_numeric_seed_getters_and_group_order() {
    let fixture = fixture();
    let f = dict(&fixture);
    let rows = array(&f["rows"]);
    assert_eq!(rows.len(), 68);
    let mut accepted = 0;
    for row in rows {
        let r = dict(row);
        let boxed = PlistValueBox::decode(&r["input"]).unwrap();
        let result = if r["kind"] == Value::String("host-update-seed".into()) {
            boxed
                .required_with(HostUpdateSeed::decode)
                .map(|s| s.to_value())
        } else {
            boxed
                .required_with(HostUpdateGroupSeed::decode)
                .map(|s| s.to_value())
        };
        assert_eq!(result.is_ok(), r["accepted"] == Value::Boolean(true));
        if let Ok(value) = result {
            accepted += 1;
            assert_eq!(value, r["canonical"]);
        }
    }
    assert_eq!(accepted, 38);
    assert_eq!(f["destroyedSeeds"], Value::Integer(38));
    for row in array(&f["nativeGroupOrder"]) {
        let r = dict(row);
        let a = HostUpdateGroupSeed::decode(&r["left"]).unwrap();
        let b = HostUpdateGroupSeed::decode(&r["right"]).unwrap();
        assert_eq!(a < b, r["less"] == Value::Boolean(true));
    }
}
#[test]
fn actual_native_next_and_increment_closure_boundaries() {
    let fixture = fixture();
    let f = dict(&fixture);
    let seeds = UpdateSeeds::default();
    for value in array(&f["nativeNext"]) {
        assert_eq!(seeds.next_seed().value(), number(value));
    }
    assert_eq!(seeds.last_value(), 8);
    for row in array(&f["nativeIncrementClosure"]) {
        let r = dict(row);
        let seeds = UpdateSeeds::starting_after(number(&r["before"]));
        let next = seeds.next_seed();
        assert_eq!(next.value(), number(&r["after"]));
        assert_eq!(next.value(), number(&r["returned"]));
        assert_eq!(seeds.last_value(), next.value());
    }
}
#[test]
fn scopes_and_integer_precision_do_not_imply_completion() {
    let first = next_host_update_seed();
    let second = next_host_update_seed();
    assert_eq!(second.value(), first.value().wrapping_add(1));
    assert_eq!(UpdateSeeds::default().next_seed().value(), 1);
    assert_eq!(UpdateSeeds::default().next_seed().value(), 1);
    for n in [0, 1, 9007199254740993, u64::MAX] {
        let seed = HostUpdateSeed::new(n);
        assert_eq!(HostUpdateSeed::decode(&seed.to_value()).unwrap(), seed);
    }
    assert_ne!(
        HostUpdateSeed::new(9007199254740992),
        HostUpdateSeed::new(9007199254740993)
    );
}
