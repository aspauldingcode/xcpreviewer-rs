use canvas_core::{
    binary_plist,
    payload_codec::Value,
    shell_payload::ShellUpdatePayload,
    shell_service::{dispatch_shell_update, ShellServiceEnvelope, ShellServiceTransport},
};
use std::rc::Rc;
fn ordered(mut v: Value) -> Value {
    match &mut v {
        Value::Dictionary(f) => {
            for (k, v) in f {
                if k == "sourceFilePaths" || k == "linkerFlags" {
                    if let Value::Array(a) = v {
                        a.sort_by(|a, b| match (a, b) {
                            (Value::String(a), Value::String(b)) => a.cmp(b),
                            _ => panic!(),
                        })
                    }
                } else {
                    *v = ordered(v.clone())
                }
            }
        }
        Value::Array(a) => {
            for v in a {
                *v = ordered(v.clone())
            }
        }
        _ => {}
    }
    v
}

fn rows(bytes: &[u8], key: &str) -> Vec<Value> {
    let Value::Dictionary(mut f) = binary_plist::decode(bytes).unwrap() else {
        panic!()
    };
    let Value::Array(a) = f.remove(key).unwrap() else {
        panic!()
    };
    a
}
#[test]
fn actual_modern_updater_requests_and_reply_success_controls() {
    let Value::Dictionary(f) = binary_plist::decode(include_bytes!(
        "fixtures/modern_shell_dispatch/native.bplist"
    ))
    .unwrap() else {
        panic!()
    };
    let Value::Array(requests) = &f["received"] else {
        panic!()
    };
    let Value::Array(states) = &f["states"] else {
        panic!()
    };
    assert_eq!(requests.len(), 6);
    assert_eq!(states.len(), 6);
    assert_eq!(f["futureReferencesReleased"], Value::Integer(6));
    assert_eq!(f["delayedReplyCopiesDestroyed"], Value::Integer(2));
    for (i, (request, state)) in requests.iter().zip(states).enumerate() {
        let envelope = ShellServiceEnvelope::decode_single_entry_updates(request).unwrap();
        assert_eq!(envelope.identifier.as_deref(), Some(i.to_string().as_str()));
        assert_eq!(ordered(envelope.to_value()), ordered(request.clone()));
        let Value::Dictionary(s) = state else {
            panic!()
        };
        assert_eq!(
            s["successfulBeforeOwnedDelayedReply"],
            Value::Boolean(i % 3 == 1)
        );
        assert_eq!(
            s["successfulAfterOwnedDelayedReply"],
            Value::Boolean(i % 3 != 0)
        );
    }
}
struct OwnedTransport {
    requests: Vec<Value>,
    pending: Rc<()>,
}
impl ShellServiceTransport for OwnedTransport {
    type PendingReply = Rc<()>;
    fn send(&mut self, request: ShellServiceEnvelope) -> Rc<()> {
        self.requests.push(request.to_value());
        Rc::clone(&self.pending)
    }
}
#[test]
fn portable_dispatch_preserves_native_requests_and_backend_pending_identity() {
    let native = rows(
        include_bytes!("fixtures/modern_shell_dispatch/native.bplist"),
        "received",
    );
    let Value::Array(inputs) = binary_plist::decode(include_bytes!(
        "fixtures/modern_shell_dispatch/input.bplist"
    ))
    .unwrap() else {
        panic!()
    };
    let token = Rc::new(());
    let mut transport = OwnedTransport {
        requests: vec![],
        pending: Rc::clone(&token),
    };
    let mut identifiers = vec![];
    for (i, row) in inputs.iter().enumerate() {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let shell = ShellUpdatePayload::decode_single_entry_updates(&row["input"]).unwrap();
        let pending = dispatch_shell_update(&mut transport, shell);
        assert!(Rc::ptr_eq(&pending, &token));
        assert_eq!(transport.requests.len(), i + 1);
        let actual =
            ShellServiceEnvelope::decode_single_entry_updates(&transport.requests[i]).unwrap();
        identifiers.push(actual.identifier.clone().unwrap().parse::<u64>().unwrap());
        let mut expected = ShellServiceEnvelope::decode_single_entry_updates(&native[i]).unwrap();
        expected.identifier = actual.identifier;
        assert_eq!(expected.to_value(), transport.requests[i]);
    }
    assert!(identifiers.windows(2).all(|x| x[1] == x[0].wrapping_add(1)));
}
