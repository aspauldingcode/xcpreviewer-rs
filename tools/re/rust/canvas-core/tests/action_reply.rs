use canvas_core::action_reply::*;
use std::{cell::Cell, rc::Rc};
#[test]
fn outcomes_match_independently_frozen_native_callbacks() {
    for line in include_str!("fixtures/native-action-outcomes.tsv").lines() {
        let f: Vec<_> = line.split('\t').collect();
        let mut gate = ActionReplyGate::default();
        assert!(gate.can_send_response());
        let outcome: ReplyOutcome<()> = match f[0] {
            "reply" => gate.finish(ReplyOutcome::Success(())).unwrap(),
            "error" => gate
                .finish(ReplyOutcome::Failure(ActionError {
                    domain: "Owned.ActionError".into(),
                    code: 17,
                }))
                .unwrap(),
            "timeout" => gate.expire().unwrap(),
            "invalidate" => gate.invalidate().unwrap(),
            _ => panic!("fixture case"),
        };
        match outcome {
            ReplyOutcome::Success(()) => assert_eq!(f[1], "-"),
            ReplyOutcome::Failure(e) => {
                assert_eq!(e.domain, f[1]);
                assert_eq!(e.code, f[2].parse::<i64>().unwrap());
            }
        }
        assert!(!gate.can_send_response());
        assert!(gate.invalidate::<()>().is_none());
        assert!(gate.expire::<()>().is_none());
    }
}
#[test]
fn each_serial_event_order_emits_only_its_first_outcome() {
    for first in 0..3 {
        for second in 0..3 {
            for third in 0..3 {
                let mut gate = ActionReplyGate::default();
                let mut count = 0;
                for event in [first, second, third] {
                    let result = match event {
                        0 => gate.finish(ReplyOutcome::Success(42)).ok(),
                        1 => gate.expire(),
                        _ => gate.invalidate(),
                    };
                    if result.is_some() {
                        count += 1;
                    }
                }
                assert_eq!(count, 1);
                assert!(!gate.can_send_response());
            }
        }
    }
}
#[test]
fn rejected_owned_reply_drops_once_while_accepted_value_stays_with_consumer() {
    struct Token(Rc<Cell<usize>>);
    impl Drop for Token {
        fn drop(&mut self) {
            self.0.set(self.0.get() + 1)
        }
    }
    let count = Rc::new(Cell::new(0));
    let mut gate = ActionReplyGate::default();
    let accepted = gate
        .finish(ReplyOutcome::Success(Token(count.clone())))
        .ok()
        .unwrap();
    assert_eq!(count.get(), 0);
    assert!(gate
        .finish(ReplyOutcome::Success(Token(count.clone())))
        .is_err());
    assert_eq!(count.get(), 1);
    drop(gate);
    assert_eq!(count.get(), 1);
    drop(accepted);
    assert_eq!(count.get(), 2);
}
