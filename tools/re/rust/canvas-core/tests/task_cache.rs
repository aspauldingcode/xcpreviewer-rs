use canvas_core::{binary_plist, binary_plist_writer, payload_codec::Value, task_cache::TaskCache};
use std::{
    io::Write,
    process::{Command, Stdio},
};
fn rows() -> Vec<Value> {
    let Value::Array(rows) =
        binary_plist::decode(include_bytes!("fixtures/task_cache/native.bplist")).unwrap()
    else {
        panic!()
    };
    rows
}
#[test]
fn factory_coalescing_error_retention_and_stale_creator_cleanup() {
    let mut destination = canvas_core::content_requests::content_override_task_cache();
    let key = canvas_core::content_requests::RequestContentOverridePayload {
        content_category: "cat".into(),
        requested_overrides: vec![],
    }
    .cache_key();
    let first = destination.acquire(key.clone(), || 9);
    assert!(destination.clear_on_failure());
    assert_eq!(destination.observe_failure(first), Some(9));
    assert_eq!(*destination.acquire(key, || 10).task(), 10);

    let mut cache = TaskCache::default();
    assert!(!cache.clear_on_failure());
    let owner = cache.acquire("key", || 1);
    let waiter = cache.acquire("key", || panic!("duplicate factory"));
    assert_eq!(*owner.task(), 1);
    assert!(!waiter.created());
    assert_eq!(cache.observe_failure(owner), None);
    assert_eq!(
        *cache
            .acquire("key", || panic!("failed handle evicted"))
            .task(),
        1
    );
    assert_eq!(cache.observe_failure(waiter), None);
    let mut cache = TaskCache::new(true);
    let owner = cache.acquire("key", || 1);
    let waiter = cache.acquire("key", || panic!());
    assert_eq!(cache.observe_failure(waiter), None);
    assert_eq!(cache.len(), 1);
    assert_eq!(
        cache.invalidate_with(&"key", false, |_| panic!("unexpected cancel")),
        Some(1)
    );
    let replacement = cache.acquire("key", || 2);
    assert_eq!(cache.observe_failure(owner), Some(2));
    assert!(cache.is_empty());
    assert_eq!(*replacement.task(), 2);
    let retry = cache.acquire("key", || 3);
    assert!(retry.created());
    assert_eq!(*retry.task(), 3);
}
#[test]
fn cancellation_is_a_request_and_external_handles_outlive_storage() {
    use std::{cell::Cell, rc::Rc};
    struct Handle {
        cancelled: Cell<bool>,
    }
    let mut cache = TaskCache::default();
    let creator = cache.acquire("k", || {
        Rc::new(Handle {
            cancelled: Cell::new(false),
        })
    });
    let waiter = cache.acquire("k", || panic!());
    let weak = Rc::downgrade(creator.task());
    let removed = cache.invalidate(&"k", |h| h.cancelled.set(true)).unwrap();
    assert!(cache.is_empty());
    assert!(creator.task().cancelled.get());
    assert!(waiter.task().cancelled.get());
    drop(cache);
    assert!(weak.upgrade().is_some());
    drop(removed);
    drop(creator);
    assert!(weak.upgrade().is_some());
    drop(waiter);
    assert!(weak.upgrade().is_none());
    let mut cache = TaskCache::<&str, i32>::default();
    assert_eq!(cache.invalidate(&"missing", |_| panic!()), None);
}
#[test]
fn complete_public_dictionary_traces_and_bounded_cli() {
    let mut accepted = 0;
    for row in rows() {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let bytes = binary_plist_writer::encode(&row["input"]).unwrap();
        for canonical in [false, true] {
            let mut command = Command::new(env!("CARGO_BIN_EXE_inspect-content-result"));
            if canonical {
                command.arg("--canonical");
            }
            let mut child = command
                .args(["task-cache", "-"])
                .stdin(Stdio::piped())
                .stdout(Stdio::piped())
                .stderr(Stdio::piped())
                .spawn()
                .unwrap();
            child.stdin.take().unwrap().write_all(&bytes).unwrap();
            let out = child.wait_with_output().unwrap();
            assert_eq!(
                out.status.success(),
                row["accepted"] == Value::Boolean(true),
                "{:?}",
                row["name"]
            );
            if out.status.success() {
                if canonical {
                    accepted += 1;
                    assert_eq!(
                        binary_plist::decode(&out.stdout).unwrap(),
                        row["output"],
                        "{:?}",
                        row["name"]
                    );
                } else {
                    let s = String::from_utf8(out.stdout).unwrap();
                    assert!(s.starts_with("result=task-cache\n"));
                    assert!(s.len() < 1000);
                    if row["name"] == Value::String("long-many".into()) {
                        assert!(s.contains("operations=24\n"));
                        assert!(s.contains("tasksStarted=3\n"));
                        assert!(s.contains("retainedTasks=3\n"));
                        assert!(s.contains("eventsShown=8"));
                        assert!(!s.contains("event8."));
                    }
                }
            } else {
                assert!(out.stdout.is_empty());
            }
        }
    }
    assert_eq!(accepted, 20);
}
