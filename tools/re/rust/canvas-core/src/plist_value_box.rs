//! Scoped PlistValueBox dictionary codec and delegated typed value access.
//! Native HashableBox equality/identity and full transport remain host-owned.
use crate::payload_codec::Value;
use std::collections::{BTreeMap, BTreeSet};
use unicode_normalization::UnicodeNormalization;
#[derive(Clone, Debug)]
pub struct PlistValueBox {
    fields: BTreeMap<String, Value>,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Dictionary,
    CanonicalKeyCollision,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum UnboxError<E> {
    MissingValue,
    Decode(E),
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum ArrayError {
    Array,
    Element { index: usize, cause: Error },
}
impl PlistValueBox {
    /// Retain the entire PropertyList dictionary without requiring or typing
    /// its `value` member. Raw canonically equivalent outer keys are outside
    /// the supported portable domain; native bridging may collapse them.
    pub fn decode(value: &Value) -> Result<Self, Error> {
        let Value::Dictionary(fields) = value else {
            return Err(Error::Dictionary);
        };
        let mut keys = BTreeSet::new();
        for key in fields.keys() {
            if !keys.insert(key.nfd().collect::<String>()) {
                return Err(Error::CanonicalKeyCollision);
            }
        }
        Ok(Self {
            fields: fields.clone(),
        })
    }
    pub fn from_value(value: Value) -> Self {
        Self {
            fields: [("value".into(), value)].into_iter().collect(),
        }
    }
    pub fn to_value(&self) -> Value {
        Value::Dictionary(self.fields.clone())
    }
    pub fn value(&self) -> Option<&Value> {
        self.fields.get("value")
    }
    pub fn field_count(&self) -> usize {
        self.fields.len()
    }
    /// Missing member fails without calling decode. Present values delegate all
    /// type/content validation and errors to the caller's representable codec.
    pub fn required_with<T, E>(
        &self,
        decode: impl FnOnce(&Value) -> Result<T, E>,
    ) -> Result<T, UnboxError<E>> {
        decode(self.value().ok_or(UnboxError::MissingValue)?).map_err(UnboxError::Decode)
    }
    /// Only an absent member becomes None. Present decoding failures propagate.
    /// A present empty String, zero, false, or opaque value is not absent.
    pub fn optional_with<T, E>(
        &self,
        decode: impl FnOnce(&Value) -> Result<T, E>,
    ) -> Result<Option<T>, E> {
        self.value().map(decode).transpose()
    }
}
pub fn decode_boxes(value: &Value) -> Result<Vec<PlistValueBox>, ArrayError> {
    let Value::Array(values) = value else {
        return Err(ArrayError::Array);
    };
    values
        .iter()
        .enumerate()
        .map(|(index, v)| {
            PlistValueBox::decode(v).map_err(|cause| ArrayError::Element { index, cause })
        })
        .collect()
}
