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
    /// Value-only compatibility profile for locally constructed XPC data.
    /// Empty Vec cannot retain native byte-pointer availability. The measured
    /// local empty object rejects, while received empty data can initialize.
    /// Use from_observed_xpc_data when the transport supplies that observation.
    /// Nonempty bytes initialize before plist validation.
    pub fn from_xpc_dictionary(fields: &BTreeMap<String, XpcValue>) -> Option<Self> {
        match fields.get("data") {
            Some(XpcValue::Data(bytes)) if !bytes.is_empty() => Some(Self::Data(bytes.clone())),
            _ => None,
        }
    }
    /// Project the actual xpc_dictionary_get_data byte-availability result.
    /// None means unavailable bytes (including missing/wrong-type data). A
    /// nonnull native byte pointer can expose a zero-length slice after XPC
    /// receipt; Some(&[]) initializes successfully and keeps empty data lazy.
    /// No address is stored or fabricated by this portable observation API.
    pub fn from_observed_xpc_data(bytes: Option<&[u8]>) -> Option<Self> {
        bytes.map(|bytes| Self::Data(bytes.to_vec()))
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
