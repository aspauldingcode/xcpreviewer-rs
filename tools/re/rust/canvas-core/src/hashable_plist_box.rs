//! Bounded property-list HashableBox value/snapshot semantics.
//!
//! Derived from shipped native methods and an owned native helper. This profile
//! supports full signed/unsigned 64-bit integers, finite Real/Date, Bool, String,
//! Data, arrays and dictionaries in the qualified Foundation-origin profile.
//! Null, nonfinite values, canonical dictionary-key collisions and nesting beyond
//! 64 are explicitly unsupported. Native hash bits and generic type identity are
//! not reproduced. Equality uses a cached projection; the original value survives.
use crate::{payload_codec::Value, plist_value_box::PlistValueBox};
use std::{
    collections::BTreeMap,
    hash::{Hash, Hasher},
};
use unicode_normalization::UnicodeNormalization;
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Null,
    Nonfinite,
    CanonicalKeyCollision,
    Depth,
}
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
enum Key {
    Bool(bool),
    Integer(i128),
    Real(u64),
    Date(u64),
    String(String),
    Data(Vec<u8>),
    Array(Vec<Key>),
    Dictionary(BTreeMap<String, Key>),
}
fn key(value: &Value, depth: usize) -> Result<Key, Error> {
    if depth > 64 {
        return Err(Error::Depth);
    }
    Ok(match value {
        Value::Null => return Err(Error::Null),
        Value::Boolean(v) => Key::Bool(*v),
        Value::Integer(v) => Key::Integer(*v as i128),
        Value::Unsigned(v) => Key::Integer(*v as i128),
        Value::Real(v) => {
            if !v.is_finite() {
                return Err(Error::Nonfinite);
            }
            // Foundation-origin NSNumber -> AnyHashable selects Int64 first.
            // At binary64 2^63, its native Int64 projection saturates to MAX.
            // Larger exactly integral values below 2^64 select UInt64 instead.
            if v.fract() == 0.0 && *v >= -9223372036854775808.0 && *v <= 9223372036854775808.0 {
                Key::Integer((*v as i64) as i128)
            } else if v.fract() == 0.0 && *v > 9223372036854775808.0 && *v < 18446744073709551616.0
            {
                Key::Integer((*v as u64) as i128)
            } else {
                Key::Real(v.to_bits())
            }
        }
        Value::Date(v) => {
            if !v.is_finite() {
                return Err(Error::Nonfinite);
            }
            Key::Date(if *v == 0.0 { 0 } else { v.to_bits() })
        }
        Value::String(v) => Key::String(v.nfd().collect()),
        Value::Data(v) => Key::Data(v.clone()),
        Value::Array(v) => Key::Array(
            v.iter()
                .map(|v| key(v, depth + 1))
                .collect::<Result<_, _>>()?,
        ),
        Value::Dictionary(v) => {
            let mut fields = BTreeMap::new();
            for (name, value) in v {
                if fields
                    .insert(name.nfd().collect(), key(value, depth + 1)?)
                    .is_some()
                {
                    return Err(Error::CanonicalKeyCollision);
                }
            }
            Key::Dictionary(fields)
        }
    })
}
#[derive(Clone, Debug)]
pub struct HashablePlistBox {
    value: PlistValueBox,
    snapshot: Key,
}
impl HashablePlistBox {
    pub fn new(value: PlistValueBox) -> Result<Self, Error> {
        let snapshot = key(&value.to_value(), 0)?;
        Ok(Self { value, snapshot })
    }
    pub fn value(&self) -> &PlistValueBox {
        &self.value
    }
}
impl PartialEq for HashablePlistBox {
    fn eq(&self, other: &Self) -> bool {
        self.snapshot == other.snapshot
    }
}
impl Eq for HashablePlistBox {}
impl Hash for HashablePlistBox {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.snapshot.hash(state);
    }
}
