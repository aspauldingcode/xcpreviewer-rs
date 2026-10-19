use canvas_core::{
    binary_plist,
    payload_codec::Value,
    remote_crash::{
        AgentCrashNotification, DiagnosticsBehavior as Behavior, Error, STREAM_IDENTIFIER,
    },
};
fn modern() -> Value {
    binary_plist::decode(include_bytes!(
        "fixtures/remote-crash/modern-canSymbolicate.bplist"
    ))
    .unwrap()
}
fn fields(v: &mut Value) -> &mut std::collections::BTreeMap<String, Value> {
    let Value::Dictionary(d) = v else {
        panic!("dictionary")
    };
    d
}
#[test]
fn independent_binary_fixtures_match_modern_and_legacy_behavior() {
    assert_eq!(STREAM_IDENTIFIER, "Ultraviolet.PreviewRemoteEvents");
    for (bytes, behavior) in [
        (
            &include_bytes!("fixtures/remote-crash/modern-willProvide.bplist")[..],
            Behavior::WillProvide,
        ),
        (
            &include_bytes!("fixtures/remote-crash/modern-canSymbolicate.bplist")[..],
            Behavior::CanSymbolicate,
        ),
        (
            &include_bytes!("fixtures/remote-crash/modern-unavailable.bplist")[..],
            Behavior::Unavailable,
        ),
        (
            &include_bytes!("fixtures/remote-crash/legacy-true.bplist")[..],
            Behavior::WillProvide,
        ),
        (
            &include_bytes!("fixtures/remote-crash/legacy-false.bplist")[..],
            Behavior::Unavailable,
        ),
    ] {
        assert_eq!(
            AgentCrashNotification::decode_binary(bytes),
            Ok(AgentCrashNotification {
                pid: 12345,
                agent_behavior: behavior
            })
        );
    }
}
#[test]
fn serializer_matches_independent_modern_trees_and_preserves_three_cases() {
    for (bytes, behavior) in [
        (
            &include_bytes!("fixtures/remote-crash/modern-willProvide.bplist")[..],
            Behavior::WillProvide,
        ),
        (
            &include_bytes!("fixtures/remote-crash/modern-canSymbolicate.bplist")[..],
            Behavior::CanSymbolicate,
        ),
        (
            &include_bytes!("fixtures/remote-crash/modern-unavailable.bplist")[..],
            Behavior::Unavailable,
        ),
    ] {
        let event = AgentCrashNotification {
            pid: 12345,
            agent_behavior: behavior,
        };
        assert_eq!(event.to_value(), binary_plist::decode(bytes).unwrap());
        assert_eq!(AgentCrashNotification::decode(&event.to_value()), Ok(event));
    }
}
#[test]
fn modern_behavior_bypasses_even_malformed_legacy_field() {
    let mut v = modern();
    fields(&mut v).insert(
        "diagnosticsComing".into(),
        Value::String("wrong type".into()),
    );
    assert_eq!(
        AgentCrashNotification::decode(&v).unwrap().agent_behavior,
        Behavior::CanSymbolicate
    );
    fields(&mut v).remove("diagnosticsComing");
    assert!(AgentCrashNotification::decode(&v).is_ok());
    fields(&mut v).insert("diagnosticsComing".into(), Value::Boolean(true));
    fields(&mut v).insert("agentBehavior".into(), Value::String("willProvide".into()));
    assert_eq!(
        AgentCrashNotification::decode(&v),
        Err(Error::Type("agentBehavior"))
    );
    fields(&mut v).insert("agentBehavior".into(), Value::Null);
    assert_eq!(
        AgentCrashNotification::decode(&v),
        Err(Error::Type("agentBehavior"))
    );
}
#[test]
fn fallback_requirements_pid_boundaries_and_error_order() {
    let mut v = modern();
    fields(&mut v).remove("agentBehavior");
    fields(&mut v).remove("diagnosticsComing");
    fields(&mut v).remove("pid");
    assert_eq!(
        AgentCrashNotification::decode(&v),
        Err(Error::Missing("diagnosticsComing"))
    );
    fields(&mut v).insert("diagnosticsComing".into(), Value::Boolean(false));
    assert_eq!(
        AgentCrashNotification::decode(&v),
        Err(Error::Missing("pid"))
    );
    for pid in [i32::MIN as i64, -1, 0, 1, i32::MAX as i64] {
        fields(&mut v).insert("pid".into(), Value::Integer(pid));
        assert_eq!(AgentCrashNotification::decode(&v).unwrap().pid, pid as i32);
    }
    for pid in [i32::MIN as i64 - 1, i32::MAX as i64 + 1] {
        fields(&mut v).insert("pid".into(), Value::Integer(pid));
        assert_eq!(AgentCrashNotification::decode(&v), Err(Error::Range("pid")));
    }
    fields(&mut v).insert("pid".into(), Value::Real(1.0));
    assert_eq!(AgentCrashNotification::decode(&v), Err(Error::Type("pid")));
}
#[test]
fn unknown_and_unreconstructed_variants_are_explicit() {
    let mut v = modern();
    fields(&mut v).insert(
        "discriminant".into(),
        Value::String("agentCrashedDiagnostics".into()),
    );
    assert_eq!(
        AgentCrashNotification::decode(&v),
        Err(Error::UnsupportedCrashReport)
    );
    fields(&mut v).insert("discriminant".into(), Value::String("mouseDown".into()));
    assert_eq!(
        AgentCrashNotification::decode(&v),
        Err(Error::UnknownDiscriminant("mouseDown".into()))
    );
    let mut v = modern();
    fields(&mut v).insert(
        "agentBehavior".into(),
        Value::Dictionary(std::collections::BTreeMap::from([(
            "discriminant".into(),
            Value::String("other".into()),
        )])),
    );
    assert_eq!(
        AgentCrashNotification::decode(&v),
        Err(Error::UnknownDiscriminant("other".into()))
    );
}
