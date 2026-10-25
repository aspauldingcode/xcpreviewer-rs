use canvas_core::{
    binary_plist, binary_plist_writer, payload_codec::Value, service_envelope::ServiceEnvelope,
};
use std::{
    collections::BTreeMap,
    io::Write,
    process::{Command, Output, Stdio},
};
fn dict(fields: Vec<(&str, Value)>) -> Value {
    Value::Dictionary(
        fields
            .into_iter()
            .map(|(k, v)| (k.into(), v))
            .collect::<BTreeMap<_, _>>(),
    )
}
fn envelope(kind: &str, fields: Vec<(&str, Value)>) -> Value {
    dict(vec![
        ("messageType", Value::String(kind.into())),
        ("payload", dict(fields)),
    ])
}
fn invoke(args: &[&str], bytes: &[u8]) -> Output {
    let mut child = Command::new(env!("CARGO_BIN_EXE_inspect-service-message"))
        .args(args)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    child.stdin.take().unwrap().write_all(bytes).unwrap();
    child.wait_with_output().unwrap()
}
fn encoded(value: &Value) -> Vec<u8> {
    binary_plist_writer::encode(value).unwrap()
}
#[test]
fn supported_routes_emit_canonical_values_and_bounded_summaries() {
    let mut cases = vec![
        envelope("ping", vec![]),
        envelope("capabilities", vec![]),
        envelope("capabilities", vec![("isRunningInXTP", Value::Integer(1))]),
        envelope(
            "purge",
            vec![("workspaceID", Value::String("owned\nworkspace".into()))],
        ),
        envelope(
            "cancelUpdate",
            vec![
                ("pid", Value::Integer(23)),
                ("contentIdentifier", Value::String("content".into())),
                ("updateSeed", Value::Unsigned(u64::MAX)),
            ],
        ),
        envelope(
            "forward",
            vec![
                ("pid", Value::Integer(23)),
                ("messageType", Value::String("render".into())),
                ("messagePayload", dict(vec![])),
            ],
        ),
    ];
    for kind in ["connect", "stop", "kill"] {
        cases.push(envelope(kind, vec![("pid", Value::Integer(23))]));
    }
    cases.push(envelope(
        "connect",
        vec![
            ("discriminant", Value::String("auditToken".into())),
            (
                "auditToken",
                dict(vec![("val", Value::Array(vec![Value::Integer(1); 8]))]),
            ),
        ],
    ));
    for value in cases {
        let bytes = encoded(&value);
        let expected = ServiceEnvelope::decode(&value).unwrap().to_value();
        let out = invoke(&["--canonical", "-"], &bytes);
        assert!(out.status.success(), "{:?}", out);
        assert!(out.stderr.is_empty());
        assert_eq!(binary_plist::decode(&out.stdout).unwrap(), expected);
        let out = invoke(&["-"], &bytes);
        assert!(out.status.success(), "{:?}", out);
        assert!(out.stderr.is_empty());
        let summary = String::from_utf8(out.stdout).unwrap();
        assert!(summary.starts_with("messageType="));
        assert!(summary.contains("identifier=absent\n"));
        assert!(summary.len() < 4096);
        if summary.contains("messageType=cancelUpdate\n") {
            assert!(summary.contains("updateSeed=18446744073709551615\n"));
        }
        if summary.contains("messageType=purge\n") {
            assert!(summary.contains("workspaceID=\"owned\\nworkspace\"\n"));
            assert!(summary.contains("killAgents=false\n"));
        }
    }
}
#[test]
fn malformed_and_unsupported_input_fail_without_binary_output() {
    for bytes in [
        b"garbage".to_vec(),
        encoded(&envelope("launch", vec![])),
        encoded(&envelope("purge", vec![])),
        encoded(&envelope(
            "ping",
            vec![("__unique_service_message_identifier", Value::Integer(1))],
        )),
    ] {
        let out = invoke(&["--canonical", "-"], &bytes);
        assert!(!out.status.success());
        assert!(out.stdout.is_empty());
        assert!(String::from_utf8(out.stderr)
            .unwrap()
            .starts_with("decode: "));
    }
    for args in [vec![], vec!["--canonical"], vec!["-", "extra"]] {
        let out = invoke(&args, &[]);
        assert!(!out.status.success());
        assert!(out.stdout.is_empty());
        assert!(String::from_utf8(out.stderr).unwrap().contains("usage:"));
    }
}
#[test]
fn unicode_and_controls_cannot_add_summary_lines_or_unbound_output() {
    let value = envelope(
        "ping",
        vec![(
            "__unique_service_message_identifier",
            Value::String(format!("\n\0\r\t{}", "🦀".repeat(1000))),
        )],
    );
    let bytes = encoded(&value);
    let out = invoke(&["-"], &bytes);
    assert!(out.status.success());
    let summary = String::from_utf8(out.stdout).unwrap();
    assert_eq!(summary.lines().count(), 4);
    assert!(summary.contains("identifierBytes=4004\n"));
    assert!(summary.contains("identifierTruncated=true\n"));
    assert!(!summary.contains('\0'));
    assert!(summary.len() < 2048);
    let out = invoke(&["--canonical", "-"], &bytes);
    assert!(out.status.success());
    assert_eq!(binary_plist::decode(&out.stdout).unwrap(), value);
}
#[test]
fn named_file_and_stdin_have_identical_results_and_input_budget_rejects() {
    let bytes = encoded(&envelope("ping", vec![]));
    let file = std::env::temp_dir().join(format!("canvas-inspector-{}.bplist", std::process::id()));
    std::fs::write(&file, &bytes).unwrap();
    let out = invoke(&[file.to_str().unwrap()], &[]);
    std::fs::remove_file(file).unwrap();
    assert!(out.status.success());
    assert_eq!(out.stdout, invoke(&["-"], &bytes).stdout);
    let out = invoke(&["--canonical", "-"], &vec![0; 64 * 1024 * 1024 + 1]);
    assert!(!out.status.success());
    assert!(out.stdout.is_empty());
    assert_eq!(out.stderr, b"input exceeds 64 MiB\n");
}
