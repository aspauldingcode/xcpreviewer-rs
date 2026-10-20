use canvas_core::{
    binary_plist,
    crash_listener::{
        CrashListenerMessage as M, Error, NextCrashRequest as R, NextCrashResponse as S,
        ProcessIdentifier as P,
    },
    payload_codec::Value,
};
use std::collections::BTreeMap;
fn d(p: impl IntoIterator<Item = (&'static str, Value)>) -> Value {
    Value::Dictionary(
        p.into_iter()
            .map(|(k, v)| (k.into(), v))
            .collect::<BTreeMap<_, _>>(),
    )
}
fn s(v: &str) -> Value {
    Value::String(v.into())
}
#[test]
fn independent_binary_message_fixtures() {
    for bytes in [
        include_bytes!("fixtures/crash-listener/pid-message.bplist").as_slice(),
        include_bytes!("fixtures/crash-listener/name-message.bplist").as_slice(),
        include_bytes!("fixtures/crash-listener/start-message.bplist").as_slice(),
    ] {
        let v = binary_plist::decode(bytes).unwrap();
        let m = M::decode_binary(bytes).unwrap();
        assert_eq!(m.to_value(), v);
    }
    let M::NextCrashReport(r) = M::decode_binary(include_bytes!(
        "fixtures/crash-listener/name-message.bplist"
    ))
    .unwrap() else {
        panic!()
    };
    assert_eq!(r.process, P::ProcessName("Preview 🪨".into()));
    assert_eq!(r.timeout.to_bits(), (-0.0f64).to_bits());
}
#[test]
fn response_uses_full_report_and_explicit_entropy() {
    let b = include_bytes!("fixtures/crash-listener/response.bplist");
    let v = binary_plist::decode(b).unwrap();
    let r = S::decode_binary(b).unwrap();
    assert_eq!(r.to_value(), v);
    let mut v = v;
    let Value::Dictionary(ref mut outer) = v else {
        panic!()
    };
    let Value::Dictionary(ref mut report) = outer.get_mut("crashReport").unwrap() else {
        panic!()
    };
    report.remove("id");
    assert!(matches!(
        S::decode(&v),
        Err(Error::Report(
            canvas_core::crash_report::Error::EntropyRequired
        ))
    ));
    let mut calls = 0;
    let r = S::decode_with_entropy(&v, &mut || {
        calls += 1;
        Ok([0; 16])
    })
    .unwrap();
    assert_eq!(calls, 1);
    assert_eq!(
        r.crash_report.id.canonical(),
        "00000000-0000-4000-8000-000000000000"
    );
}
#[test]
fn signed_pid_domain_and_name_emptiness() {
    for n in [i32::MIN, -1, 0, i32::MAX] {
        let p = P::Pid(n);
        assert_eq!(P::decode(&p.to_value()).unwrap(), p);
    }
    let p = P::ProcessName(String::new());
    assert_eq!(P::decode(&p.to_value()).unwrap(), p);
    for n in [i32::MIN as i64 - 1, i32::MAX as i64 + 1] {
        assert!(matches!(
            P::decode(&d([
                ("discriminant", s("pid")),
                ("payload", Value::Integer(n))
            ])),
            Err(Error::Range("payload"))
        ));
    }
}
#[test]
fn discriminants_and_payload_types_are_strict() {
    for tag in ["unknown", "PID", ""] {
        assert!(matches!(
            P::decode(&d([
                ("discriminant", s(tag)),
                ("payload", Value::Integer(1))
            ])),
            Err(Error::UnknownDiscriminant(_))
        ));
    }
    for bad in [Value::Null, Value::Boolean(true), Value::Real(1.0), s("1")] {
        assert!(matches!(
            P::decode(&d([("discriminant", s("pid")), ("payload", bad)])),
            Err(Error::Type("payload"))
        ));
    }
    assert!(matches!(
        P::decode(&d([("discriminant", s("processName"))])),
        Err(Error::Missing("payload"))
    ));
}
#[test]
fn required_request_fields_preserve_error_order() {
    assert_eq!(R::decode(&d([])), Err(Error::Missing("process")));
    let p = P::Pid(1).to_value();
    assert_eq!(
        R::decode(&d([("process", p.clone())])),
        Err(Error::Missing("timeout"))
    );
    for v in [Value::Integer(1), Value::Null, Value::Boolean(false)] {
        assert_eq!(
            R::decode(&d([("process", p.clone()), ("timeout", v)])),
            Err(Error::Type("timeout"))
        );
    }
    assert_eq!(S::decode(&d([])), Err(Error::Missing("crashReport")));
}
#[test]
fn no_invented_timeout_validation() {
    for t in [-0.0, -1.0, f64::INFINITY, f64::NEG_INFINITY, f64::NAN] {
        let r = R {
            process: P::Pid(1),
            timeout: t,
        };
        let result = R::decode(&r.to_value()).unwrap();
        assert_eq!(result.timeout.to_bits(), t.to_bits());
    }
}
#[test]
fn listener_case_controls() {
    let v = d([
        ("discriminant", s("startListeningIfNeeded")),
        ("payload", Value::Null),
    ]);
    assert_eq!(M::decode(&v), Ok(M::StartListeningIfNeeded));
    assert!(matches!(
        M::decode(&d([("discriminant", s("nextCrashReport"))])),
        Err(Error::Missing("payload"))
    ));
    assert!(matches!(
        M::decode(&d([("discriminant", s("future"))])),
        Err(Error::UnknownDiscriminant(_))
    ));
    let original = v.clone();
    M::decode(&v).unwrap();
    assert_eq!(v, original);
}
