use canvas_core::{service_identifier::ServiceIdentifiers, service_envelope::{ForwardServiceEnvelope, IDENTIFIER_KEY}, forward_payload::ForwardPayload, payload_codec::Value};
use std::{collections::BTreeSet, sync::Arc, thread};
#[test]
fn initial_and_unsigned_decimal_match_owned_swift_control() {
    let sequence = ServiceIdentifiers::default();
    assert_eq!([sequence.next_identifier(), sequence.next_identifier(), sequence.next_identifier()], ["0", "1", "2"]);
    let values = [0, 1, 9, 10, 999, 4294967296, 9223372036854775808, u64::MAX];
    let actual = values.map(|value| ServiceIdentifiers::starting_at(value).next_identifier());
    let json = format!("[{}]", actual.iter().map(|s| format!("\"{s}\"")).collect::<Vec<_>>().join(","));
    assert_eq!(json, include_str!("fixtures/service-identifier/swift-format.json").trim());
}
#[test]
fn wrap_returns_old_value_without_overflow_failure() {
    let sequence = ServiceIdentifiers::starting_at(u64::MAX - 1);
    let actual = (0..4).map(|_| sequence.next_identifier()).collect::<Vec<_>>();
    assert_eq!(actual, ["18446744073709551614", "18446744073709551615", "0", "1"]);
}
#[test]
fn shared_sequence_allocates_contiguous_unique_values_concurrently() {
    let sequence = Arc::new(ServiceIdentifiers::default());
    let workers = (0..8).map(|_| {
        let sequence = sequence.clone();
        thread::spawn(move || (0..256).map(|_| sequence.next_identifier().parse::<u64>().unwrap()).collect::<Vec<_>>())
    }).collect::<Vec<_>>();
    let actual = workers.into_iter().flat_map(|w| w.join().unwrap()).collect::<Vec<_>>();
    assert_eq!(actual.len(), 2048);
    assert_eq!(actual.into_iter().collect::<BTreeSet<_>>(), (0..2048).collect());
    assert_eq!(sequence.next_identifier(), "2048");
}
#[test]
fn new_envelopes_share_process_sequence_and_preserve_identifier_namespace() {
    let value = canvas_core::binary_plist::decode(include_bytes!("fixtures/forward-payload/full.bplist")).unwrap();
    let forward = ForwardPayload::decode(&value).unwrap();
    let first = ForwardServiceEnvelope::new(forward.clone());
    let second = ForwardServiceEnvelope::new(forward);
    let a = first.identifier.as_ref().unwrap().parse::<u64>().unwrap();
    let b = second.identifier.as_ref().unwrap().parse::<u64>().unwrap();
    assert_eq!(b, a.wrapping_add(1));
    let root = first.to_value();
    let Value::Dictionary(d) = &root else { panic!() };
    assert!(!d.contains_key(IDENTIFIER_KEY));
    let Value::Dictionary(p) = &d["payload"] else { panic!() };
    assert_eq!(p[IDENTIFIER_KEY], Value::String(a.to_string()));
    assert_eq!(ForwardServiceEnvelope::decode(&root), Ok(first));
}
