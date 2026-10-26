//! Incremental-update single-entry wire subset. Native multi-key selection is
//! randomized dictionary iteration; callers must resolve that ambiguity explicitly.
use crate::payload_codec::Value;
#[derive(Clone, Debug)]
pub struct PreviewIncrementalUpdate {
    key: String,
    value: Value,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Dictionary,
    Empty,
    AmbiguousNativeSelection { entries: usize },
    UnsupportedValue,
}
impl PreviewIncrementalUpdate {
    /// Accept one key with a String, numeric, Bool or Data value. Native decoding
    /// rejects Date/Array/Dictionary values through its protocol-composition cast.
    /// Multiple keys are a portable restriction, not a native schema rejection.
    pub fn decode_single_entry(value: &Value) -> Result<Self, Error> {
        let Value::Dictionary(fields) = value else {
            return Err(Error::Dictionary);
        };
        if fields.is_empty() {
            return Err(Error::Empty);
        }
        if fields.len() != 1 {
            return Err(Error::AmbiguousNativeSelection {
                entries: fields.len(),
            });
        }
        let (key, value) = fields.first_key_value().unwrap();
        Self::new(key.clone(), value.clone())
    }
    pub fn new(key: String, value: Value) -> Result<Self, Error> {
        if !matches!(
            value,
            Value::String(_)
                | Value::Boolean(_)
                | Value::Integer(_)
                | Value::Unsigned(_)
                | Value::Real(_)
                | Value::Data(_)
        ) {
            return Err(Error::UnsupportedValue);
        }
        Ok(Self { key, value })
    }
    /// Preserve IEEE Real bits, including native-qualified nonfinite values.
    pub fn to_binary_plist(&self) -> Result<Vec<u8>, crate::binary_plist_writer::Error> {
        crate::binary_plist_writer::encode_preserving_real_bits(&self.to_value())
    }
    pub fn key(&self) -> &str {
        &self.key
    }
    pub fn value(&self) -> &Value {
        &self.value
    }
    pub fn to_value(&self) -> Value {
        Value::Dictionary(
            [(self.key.clone(), self.value.clone())]
                .into_iter()
                .collect(),
        )
    }
}
