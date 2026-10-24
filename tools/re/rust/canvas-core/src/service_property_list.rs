//! UVPropertyList's measured data-key boundary, separate from TransportReply's
//! throwing LazyPropertyList. Foundation serialization/parsing is caller-supplied;
//! this adapter neither implements all plist formats nor performs native IPC.
use crate::{payload_codec::Value, settings_xpc::XpcValue};
use std::collections::BTreeMap;
#[derive(Clone, Debug, PartialEq)]
pub enum ServicePropertyList {
    Dictionary(BTreeMap<String, Value>),
    Data(Vec<u8>),
}
impl ServicePropertyList {
    /// Pinned native controls reject absent, wrong-type and zero-byte data.
    /// Nonempty bytes initialize successfully before any plist validation.
    pub fn from_xpc_dictionary(fields: &BTreeMap<String, XpcValue>) -> Option<Self> {
        match fields.get("data") {
            Some(XpcValue::Data(bytes)) if !bytes.is_empty() => Some(Self::Data(bytes.clone())),
            _ => None,
        }
    }
    /// Native dictionary access falls back to an empty dictionary on parser
    /// failure or a non-dictionary root. Existing dictionary storage bypasses
    /// parsing. No computed result is cached; Foundation XML support depends on
    /// the supplied parser. Owned Rust values do not model shared ObjC mutation.
    pub fn dictionary_with<E>(&self, decode: impl FnOnce(&[u8]) -> Result<Value, E>) -> BTreeMap<String, Value> {
        match self {
            Self::Dictionary(fields) => fields.clone(),
            Self::Data(bytes) => match decode(bytes) {
                Ok(Value::Dictionary(fields)) => fields,
                _ => BTreeMap::new(),
            },
        }
    }
    /// Native data access preserves stored data and returns zero bytes on
    /// Foundation serialization failure. Conversion from dictionary storage is
    /// repeated on each access, not cached.
    pub fn data_with<E>(&self, encode: impl FnOnce(&BTreeMap<String, Value>) -> Result<Vec<u8>, E>) -> Vec<u8> {
        match self {
            Self::Data(bytes) => bytes.clone(),
            Self::Dictionary(fields) => encode(fields).unwrap_or_default(),
        }
    }
    /// The raw coder writes exactly the data key, including zero-byte failure
    /// output. It replaces that entry and preserves other destination fields.
    /// A nonempty destination count does not imply valid plist bytes or delivery.
    pub fn encode_to_xpc_dictionary_with<E>(
        &self, destination: &mut BTreeMap<String, XpcValue>,
        encode: impl FnOnce(&BTreeMap<String, Value>) -> Result<Vec<u8>, E>,
    ) {
        destination.insert("data".into(), XpcValue::Data(self.data_with(encode)));
    }
}
