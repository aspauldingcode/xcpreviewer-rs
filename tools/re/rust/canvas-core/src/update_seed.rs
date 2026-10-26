//! Qualified UInt64 update identities and the increment-then-return allocator.
//! Values can repeat after wrap/restart; they do not prove update completion.
use crate::payload_codec::Value;
use std::sync::Mutex;
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Error {
    Number,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct HostUpdateSeed(u64);
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub struct HostUpdateGroupSeed(u64);
/// Foundation UInt64 conversion profile qualified with actual native seed
/// getters. Preserve exact integer precision; accept Bool and finite integral
/// reals in [0,2^64), reject the rounded real endpoint and all other types.
pub(crate) fn uint64(value: &Value) -> Option<u64> {
    match value {
        Value::Unsigned(v) => Some(*v),
        Value::Integer(v) if *v >= 0 => Some(*v as u64),
        Value::Boolean(v) => Some(u64::from(*v)),
        Value::Real(v)
            if v.is_finite() && v.fract() == 0.0 && *v >= 0.0 && *v < 18446744073709551616.0 =>
        {
            Some(*v as u64)
        }
        _ => None,
    }
}
fn canonical(value: u64) -> Value {
    if value <= i64::MAX as u64 {
        Value::Integer(value as i64)
    } else {
        Value::Unsigned(value)
    }
}
impl HostUpdateSeed {
    pub const fn new(value: u64) -> Self {
        Self(value)
    }
    pub const fn value(self) -> u64 {
        self.0
    }
    pub fn decode(value: &Value) -> Result<Self, Error> {
        uint64(value).map(Self).ok_or(Error::Number)
    }
    pub fn to_value(self) -> Value {
        canonical(self.0)
    }
}
impl HostUpdateGroupSeed {
    pub const fn new(value: u64) -> Self {
        Self(value)
    }
    pub const fn value(self) -> u64 {
        self.0
    }
    pub fn decode(value: &Value) -> Result<Self, Error> {
        uint64(value).map(Self).ok_or(Error::Number)
    }
    pub fn to_value(self) -> Value {
        canonical(self.0)
    }
}
#[derive(Debug, Default)]
pub struct UpdateSeeds {
    last: Mutex<u64>,
}
impl UpdateSeeds {
    /// Explicit state injection for owned sessions/boundary tests. The native
    /// process-local allocator initializes last to zero, so its first result is 1.
    pub const fn starting_after(last: u64) -> Self {
        Self {
            last: Mutex::new(last),
        }
    }
    pub fn next_seed(&self) -> HostUpdateSeed {
        // A Rust Mutex models native serialization, not the native lock ABI.
        // Poison handling is original Rust policy; no callback runs under lock.
        let mut last = self.last.lock().expect("update seed mutex poisoned");
        *last = last.wrapping_add(1);
        HostUpdateSeed(*last)
    }
    pub fn last_value(&self) -> u64 {
        *self.last.lock().expect("update seed mutex poisoned")
    }
}
static PROCESS_SEEDS: UpdateSeeds = UpdateSeeds::starting_after(0);
/// Share one original process-local sequence. Separate UpdateSeeds instances
/// deliberately have separate scopes; no cross-process uniqueness is promised.
pub fn next_host_update_seed() -> HostUpdateSeed {
    PROCESS_SEEDS.next_seed()
}
