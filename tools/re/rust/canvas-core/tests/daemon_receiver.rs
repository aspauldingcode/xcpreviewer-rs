include!("../examples/daemon_receiver.rs");
#[test]
fn native_receiver_lazy_bytes_reply_capability_and_acknowledgement_match() {
    main();
}
#[test]
fn rejected_wire_never_creates_or_forwards_a_daemon_reply() {
    let mut created = 0;
    let rejected = prepare_observed_service_data::<()>(None, || {
        created += 1;
        Some(())
    });
    assert!(rejected.is_none());
    assert_eq!(created, 0);
}
