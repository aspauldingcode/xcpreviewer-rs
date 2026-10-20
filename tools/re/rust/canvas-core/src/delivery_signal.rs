//! One-winner delivery receipt signal, anchored to owned BSAtomicSignal controls.
//! Native workspace completion and its five-second fallback both invoke a
//! shared signal-protected block. Signalling is not target cancellation,
//! callback completion, capture release or remote/GPU/Mach settlement.
use std::sync::atomic::{AtomicBool, Ordering};
/// Observed FrontBoard workspace fallback interval; not a general action timeout.
pub const OBSERVED_WORKSPACE_FALLBACK_SECONDS: u64 = 5;
#[derive(Debug, Default)]
pub struct DeliverySignal {
    signalled: AtomicBool,
}
impl DeliverySignal {
    pub const fn new() -> Self {
        Self {
            signalled: AtomicBool::new(false),
        }
    }
    /// True for exactly one caller. Memory ordering is an explicit portable
    /// policy; native language-level memory-order equivalence is not claimed.
    pub fn signal(&self) -> bool {
        self.signalled
            .compare_exchange(false, true, Ordering::AcqRel, Ordering::Acquire)
            .is_ok()
    }
    /// True means a caller won admission. Its subsequent work can still run.
    pub fn has_been_signalled(&self) -> bool {
        self.signalled.load(Ordering::Acquire)
    }
}
