include!("../examples/repeated_reply.rs");
#[test]
fn native_repeated_callbacks_preserve_first_values_and_failures() {
    main();
}
#[test]
fn rejected_completion_returns_ownership_and_retains_first() {
    use std::{cell::Cell, rc::Rc};
    struct Token(Rc<Cell<u32>>);
    impl Drop for Token {
        fn drop(&mut self) {
            self.0.set(self.0.get() + 1);
        }
    }
    let first = Rc::new(Cell::new(0));
    let later = Rc::new(Cell::new(0));
    let mut completion = ReplyCompletion::<Token, Token>::new();
    assert!(completion.try_complete(Ok(Token(first.clone()))).is_ok());
    let rejected = completion.try_complete(Err(Token(later.clone())));
    assert!(matches!(&rejected, Err(Err(_))));
    assert_eq!((first.get(), later.get()), (0, 0));
    drop(rejected);
    assert_eq!((first.get(), later.get()), (0, 1));
    drop(completion);
    assert_eq!((first.get(), later.get()), (1, 1));
}
