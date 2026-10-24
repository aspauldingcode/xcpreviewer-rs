//! Source-guided ServiceMessage identifier allocation: process-local unsigned
//! counter, initially zero, return-old wrapping increment, decimal description.
//! IDs can repeat after wrap or process restart. They imply no reply correlation
//! or completed target work. The native OS unfair lock is represented by Mutex.
use std::sync::Mutex;

#[derive(Debug, Default)]
pub struct ServiceIdentifiers {
    next: Mutex<u64>,
}
impl ServiceIdentifiers {
    /// Explicit state injection for owned sessions, boundary tests or recovery;
    /// the native global's initial state is zero, not caller-supplied.
    pub const fn starting_at(next: u64) -> Self {
        Self { next: Mutex::new(next) }
    }
    pub fn next_identifier(&self) -> String {
        let value = {
            // No user callback or fallible formatting runs inside the lock.
            // Poison handling is an original Rust invariant policy.
            let mut next = self.next.lock().expect("identifier sequence mutex poisoned");
            let value = *next;
            *next = next.wrapping_add(1);
            value
        };
        value.to_string()
    }
}
static PROCESS_IDENTIFIERS: ServiceIdentifiers = ServiceIdentifiers::starting_at(0);
/// Share one native-style sequence across connections in this process.
/// Separately owned ServiceIdentifiers values deliberately have separate scopes.
pub fn next_service_identifier() -> String {
    PROCESS_IDENTIFIERS.next_identifier()
}
