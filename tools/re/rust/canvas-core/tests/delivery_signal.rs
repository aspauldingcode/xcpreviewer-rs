use canvas_core::delivery_signal::DeliverySignal;
use std::sync::{mpsc, Arc, Barrier};
const NATIVE: &str = include_str!("fixtures/native-delivery-signal.tsv");
#[test]
fn independent_native_sequential_signal_outcomes() {
    let rows: Vec<_> = NATIVE
        .lines()
        .take(4)
        .map(|l| l.split('\t').nth(1).unwrap() == "1")
        .collect();
    let token = DeliverySignal::new();
    assert_eq!(
        vec![
            token.has_been_signalled(),
            token.signal(),
            token.signal(),
            token.has_been_signalled()
        ],
        rows
    );
}
#[test]
fn independent_native_concurrent_one_winner_contract() {
    for row in NATIVE.lines().skip(4) {
        let parts: Vec<_> = row.split('\t').collect();
        let attempts = parts[1].parse::<usize>().unwrap();
        let expected = parts[2].parse::<usize>().unwrap();
        let token = Arc::new(DeliverySignal::new());
        let start = Arc::new(Barrier::new(attempts));
        let threads: Vec<_> = (0..attempts)
            .map(|_| {
                let token = token.clone();
                let start = start.clone();
                std::thread::spawn(move || {
                    start.wait();
                    usize::from(token.signal())
                })
            })
            .collect();
        assert_eq!(
            threads
                .into_iter()
                .map(|t| t.join().unwrap())
                .sum::<usize>(),
            expected
        );
        assert!(token.has_been_signalled());
    }
}
#[test]
fn signalled_flag_does_not_prove_winning_work_completed() {
    // Original portable counterexample: pause winning cleanup after admission.
    let token = Arc::new(DeliverySignal::new());
    let (started_tx, started_rx) = mpsc::channel();
    let (release_tx, release_rx) = mpsc::channel();
    let worker = {
        let token = token.clone();
        std::thread::spawn(move || {
            assert!(token.signal());
            started_tx.send(()).unwrap();
            release_rx.recv().unwrap();
            42
        })
    };
    started_rx.recv().unwrap();
    assert!(token.has_been_signalled());
    assert!(!worker.is_finished());
    assert!(!token.signal());
    release_tx.send(()).unwrap();
    assert_eq!(worker.join().unwrap(), 42);
}
