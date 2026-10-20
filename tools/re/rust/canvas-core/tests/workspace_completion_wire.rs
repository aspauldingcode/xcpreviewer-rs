use canvas_core::{settings_xpc::XpcValue as X, workspace_action::{WorkspaceActionCompletion as Completion, CompletionReplyError}, xpc_wire};
use std::collections::BTreeMap;
#[test]
fn native_argument_selection_differs_from_strict_envelope_validation() {
    let error = Completion { error_archive: Some(vec![0, 1, 0xff]) };
    let X::Dictionary(mut wrong) = error.to_xpc() else { unreachable!() };
    let encoded_error = wrong.remove("1").unwrap();
    wrong.insert("2".into(), encoded_error.clone());
    let wrong = X::Dictionary(wrong);
    assert!(Completion::from_xpc(&wrong).is_err());
    assert_eq!(Completion::from_native_arguments(&wrong).unwrap(), Completion::default());
    let body = xpc_wire::encode_body(&wrong).unwrap();
    assert_eq!(Completion::from_wire_reply(&body).unwrap(), Completion::default());
    let both = X::Dictionary(BTreeMap::from([("1".into(), encoded_error), ("2".into(), X::Null)]));
    assert_eq!(Completion::from_native_arguments(&both).unwrap(), error);
}
#[test]
fn wire_errors_remain_distinct_from_unsupported_argument_values() {
    assert!(matches!(Completion::from_wire_reply(b"CPX@"), Err(CompletionReplyError::Wire(_))));
    let body = xpc_wire::encode_body(&X::Null).unwrap();
    assert!(matches!(Completion::from_wire_reply(&body), Err(CompletionReplyError::Value(_))));
    let mut body = Completion::default().to_wire_reply().unwrap();
    body.push(0);
    assert!(matches!(Completion::from_wire_reply(&body), Err(CompletionReplyError::Wire(_))));
    let unsupported = X::Dictionary(BTreeMap::from([("1".into(), X::Null)]));
    let body = xpc_wire::encode_body(&unsupported).unwrap();
    assert!(matches!(Completion::from_wire_reply(&body), Err(CompletionReplyError::Value(_))));
}
#[test]
fn actual_native_completion_wire_corpus_when_supplied() {
    let Some(folder) = std::env::var_os("XCPREVIEW_NATIVE_COMPLETION_BODIES") else { return };
    let folder = std::path::PathBuf::from(folder);
    let mut total = 0;
    for (mode, size, archive_size) in [("primary",20,0), ("holdout",20,0), ("error-primary",184,104), ("error-holdout",188,108), ("wrong-slot",184,0)] {
        let bytes = std::fs::read(folder.join(format!("{mode}.body"))).unwrap();
        assert_eq!(bytes.len(), size); total += bytes.len();
        let reply = Completion::from_wire_reply(&bytes).unwrap();
        if archive_size == 0 { assert_eq!(reply, Completion::default()); }
        else {
            let archive = std::fs::read(folder.join(format!("{mode}.archive"))).unwrap();
            assert_eq!(archive.len(), archive_size);
            assert_eq!(reply.error_archive.as_ref().unwrap(), &archive);
        }
        let encoded = reply.to_wire_reply().unwrap();
        if mode == "wrong-slot" { assert_eq!(encoded, Completion::default().to_wire_reply().unwrap()); }
        else { assert_eq!(encoded, bytes); }
    }
    assert_eq!(total, 596);
    eprintln!("verified 5 actual native completion bodies, 596 bytes consumed; 4 exact outputs; wrong-slot projects empty");
}

#[test]
fn reserved_service_returns_never_become_clean_callback_completions() {
    for key in ["BSXPCReturnError", "BSXPCReturnValue"] {
        let value = X::Dictionary(BTreeMap::from([(key.into(), X::Null)]));
        assert!(Completion::from_native_arguments(&value).is_err());
        let bytes = xpc_wire::encode_body(&value).unwrap();
        assert!(matches!(Completion::from_wire_reply(&bytes), Err(CompletionReplyError::Value(_))));
    }
}
