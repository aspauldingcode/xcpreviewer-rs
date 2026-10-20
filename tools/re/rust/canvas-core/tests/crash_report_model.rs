use canvas_core::{
    binary_plist,
    crash_report::{CrashReport, Error, Uuid},
    payload_codec::Value,
    remote_crash::{RemoteEventPayload, RemoteEventRequest},
};
include!("fixtures/crash-report-model/uuid_cases.rs");
fn full() -> Value {
    binary_plist::decode(include_bytes!(
        "fixtures/crash-report-model/report-full.bplist"
    ))
    .unwrap()
}
fn minimal() -> Value {
    binary_plist::decode(include_bytes!(
        "fixtures/crash-report-model/report-minimal.bplist"
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
fn native_uuid_input_and_canonical_cases_match() {
    assert_eq!(UUID_CASES.len(), 10);
    for (input, expected) in UUID_CASES {
        assert_eq!(
            Uuid::parse(input).ok().map(Uuid::canonical).as_deref(),
            *expected
        );
    }
}
#[test]
fn full_report_matches_independent_canonical_tree() {
    let report = CrashReport::decode(&full()).unwrap();
    assert_eq!(
        report.id.canonical(),
        "00112233-4455-6677-8899-AABBCCDDEEFF"
    );
    assert_eq!(report.name, "PreviewLab");
    assert_eq!(report.bug_type, "309");
    assert_eq!(report.pid, 12345);
    assert_eq!(report.time.to_bits(), 0.125_f64.to_bits());
    assert_eq!(report.images[0].uuid, "opaque-image-id");
    assert_eq!(report.images[0].base, 4096);
    assert_eq!(report.frames[0].symbol.as_deref(), Some("body"));
    assert_eq!(report.frames[0].source_line, Some(7));
    assert_eq!(report.termination.as_ref().unwrap().by_pid, Some(-1));
    assert_eq!(
        report.asi.as_ref().unwrap()["Application Specific Information"],
        vec!["line1", "按钮🧪"]
    );
    assert_eq!(
        report.to_value(),
        binary_plist::decode(include_bytes!(
            "fixtures/crash-report-model/report-canonical.bplist"
        ))
        .unwrap()
    );
    assert_eq!(CrashReport::decode(&report.to_value()), Ok(report));
}
#[test]
fn minimal_report_omits_absent_fields() {
    let tree = minimal();
    let report = CrashReport::decode(&tree).unwrap();
    assert!(report.asi.is_none() && report.termination.is_none() && report.log_file_path.is_none());
    assert!(report.images.is_empty() && report.frames.is_empty());
    assert_eq!(report.to_value(), tree);
}
#[test]
fn missing_id_uses_lazy_entropy_and_never_a_fixed_default() {
    let mut calls = 0;
    let mut entropy = || {
        calls += 1;
        Ok([0xa5; 16])
    };
    let report = CrashReport::decode_with_entropy(&minimal(), &mut entropy).unwrap();
    assert_eq!(
        report.id.canonical(),
        "00112233-4455-6677-8899-AABBCCDDEEFF"
    );
    drop(entropy);
    assert_eq!(calls, 0);
    let mut tree = minimal();
    fields(&mut tree).remove("id");
    assert_eq!(CrashReport::decode(&tree), Err(Error::EntropyRequired));
    let mut calls = 0;
    let report = CrashReport::decode_with_entropy(&tree, &mut || {
        calls += 1;
        Ok([0xa5; 16])
    })
    .unwrap();
    assert_eq!(calls, 1);
    assert_eq!(
        report.id.canonical(),
        "A5A5A5A5-A5A5-45A5-A5A5-A5A5A5A5A5A5"
    );
    assert_eq!(report.id.0[6] >> 4, 4);
    assert_eq!(report.id.0[8] >> 6, 2);
    fields(&mut tree).remove("name");
    let mut calls = 0;
    assert_eq!(
        CrashReport::decode_with_entropy(&tree, &mut || {
            calls += 1;
            Ok([0; 16])
        }),
        Err(Error::Missing("name"))
    );
    assert_eq!(calls, 1);
}
#[test]
fn required_and_nested_types_reject_without_input_changes() {
    for key in ["name", "bugType", "pid", "time", "images", "frames"] {
        let mut tree = full();
        fields(&mut tree).remove(key);
        let copy = tree.clone();
        assert_eq!(CrashReport::decode(&tree), Err(Error::Missing(key)));
        assert_eq!(tree, copy);
    }
    let mut tree = full();
    fields(&mut tree).insert("time".into(), Value::Real(0.125));
    assert_eq!(CrashReport::decode(&tree), Err(Error::Type("time")));
    let mut tree = full();
    fields(&mut tree).insert("pid".into(), Value::Integer(i64::from(i32::MAX) + 1));
    assert_eq!(CrashReport::decode(&tree), Err(Error::Range("pid")));
    let mut tree = full();
    fields(&mut tree).insert("id".into(), Value::String("opaque-image-id".into()));
    assert_eq!(CrashReport::decode(&tree), Err(Error::InvalidUuid));
    for (array, key) in [
        ("images", "uuid"),
        ("images", "base"),
        ("frames", "imageIndex"),
        ("frames", "imageOffset"),
    ] {
        let mut tree = full();
        let Value::Array(a) = fields(&mut tree).get_mut(array).unwrap() else {
            unreachable!()
        };
        fields(&mut a[0]).remove(key);
        assert_eq!(CrashReport::decode(&tree), Err(Error::Missing(key)));
    }
}
#[test]
fn all_recovered_remote_event_and_request_cases_work() {
    let event = RemoteEventPayload::decode_binary(include_bytes!(
        "fixtures/crash-report-model/event-report.bplist"
    ))
    .unwrap();
    let request = RemoteEventRequest::decode_binary(include_bytes!(
        "fixtures/crash-report-model/request-report.bplist"
    ))
    .unwrap();
    let expected = CrashReport::decode(&full()).unwrap();
    assert_eq!(
        event,
        RemoteEventPayload::AgentCrashedDiagnostics(expected.clone())
    );
    assert_eq!(
        request,
        RemoteEventRequest::SymbolicateCrashedDiagnostics(expected)
    );
    assert_eq!(RemoteEventPayload::decode(&event.to_value()), Ok(event));
    assert_eq!(RemoteEventRequest::decode(&request.to_value()), Ok(request));
    assert_eq!(
        RemoteEventRequest::decode_binary(include_bytes!(
            "fixtures/crash-report/screenshot-request.bplist"
        )),
        Ok(RemoteEventRequest::RequestScreenshot)
    );
    assert!(matches!(
        RemoteEventPayload::decode_binary(include_bytes!(
            "fixtures/remote-crash/modern-willProvide.bplist"
        )),
        Ok(RemoteEventPayload::AgentCrashed(_))
    ));
}
#[test]
fn optional_empty_values_and_signed_ints_are_preserved() {
    let mut tree = minimal();
    let d = fields(&mut tree);
    d.insert("asi".into(), Value::Dictionary(Default::default()));
    d.insert("termination".into(), Value::Dictionary(Default::default()));
    d.insert("logFilePath".into(), Value::String(String::new()));
    let report = CrashReport::decode(&tree).unwrap();
    assert_eq!(report.to_value(), tree);
    let mut tree = full();
    let Value::Array(a) = fields(&mut tree).get_mut("images").unwrap() else {
        unreachable!()
    };
    fields(&mut a[0]).insert("base".into(), Value::Integer(i64::MIN));
    assert_eq!(CrashReport::decode(&tree).unwrap().images[0].base, i64::MIN);
    let mut tree = full();
    fields(&mut tree).insert("termination".into(), Value::Null);
    assert_eq!(CrashReport::decode(&tree), Err(Error::Type("termination")));
}
#[test]
fn opaque_extras_do_not_change_known_fields_and_entropy_errors_propagate() {
    let mut tree = full();
    fields(&mut tree).insert("unknown".into(), Value::Array(vec![Value::Boolean(true)]));
    assert_eq!(
        CrashReport::decode(&tree).unwrap().to_value(),
        CrashReport::decode(&full()).unwrap().to_value()
    );
    let mut tree = minimal();
    fields(&mut tree).remove("id");
    assert_eq!(
        CrashReport::decode_with_entropy(&tree, &mut || Err(Error::EntropyRequired)),
        Err(Error::EntropyRequired)
    );
    let mut event = Value::Dictionary(std::collections::BTreeMap::from([
        (
            "discriminant".into(),
            Value::String("agentCrashedDiagnostics".into()),
        ),
        ("crashReport".into(), tree),
    ]));
    let mut calls = 0;
    let result = RemoteEventPayload::decode_with_entropy(&event, &mut || {
        calls += 1;
        Ok([1; 16])
    });
    assert!(result.is_ok());
    assert_eq!(calls, 1);
    fields(&mut event).insert("discriminant".into(), Value::String("mouseDown".into()));
    assert!(RemoteEventPayload::decode(&event).is_err());
}
