include!("../examples/native_future_cancel.rs");
#[test]
fn native_cancellation_order_and_context_match_portable_state() {
    main();
}
#[test]
fn canceled_cell_returns_later_non_clone_values_and_context() {
    use std::{cell::Cell, rc::Rc};
    struct Token(Rc<Cell<u32>>);
    impl Drop for Token {
        fn drop(&mut self) {
            self.0.set(self.0.get() + 1);
        }
    }
    let first = Rc::new(Cell::new(0));
    let later = Rc::new(Cell::new(0));
    let outcome = Rc::new(Cell::new(0));
    let mut completion = ReplyCompletion::<Token, (), Token>::default();
    assert!(completion.try_cancel(Token(first.clone())).is_ok());
    let rejected_context = completion.try_cancel(Token(later.clone()));
    let rejected_outcome = completion.try_complete(Ok(Token(outcome.clone())));
    assert!(matches!(&rejected_context, Err(_)));
    assert!(matches!(&rejected_outcome, Err(Ok(_))));
    assert_eq!((first.get(), later.get(), outcome.get()), (0, 0, 0));
    drop((rejected_context, rejected_outcome));
    assert_eq!((first.get(), later.get(), outcome.get()), (0, 1, 1));
    drop(completion);
    assert_eq!((first.get(), later.get(), outcome.get()), (1, 1, 1));
}
