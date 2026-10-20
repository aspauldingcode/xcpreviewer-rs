//! Local scene-response settings projection. Slot1 contains a native
//! UVPropertyList wrapper; here it is represented as a decoded dictionary.
//! This is not BSXPC serialization or native Canvas transport.
use crate::binary_plist;
use crate::payload_codec::Value;
use std::collections::BTreeMap;
pub const PAYLOAD: i64 = 1;
#[derive(Clone, Debug, PartialEq, Default)]
pub struct SceneReply {
    /// Absent differs from a present empty dictionary.
    pub payload: Option<BTreeMap<String, Value>>,
}
#[derive(Clone, Debug, PartialEq)]
pub enum Error {
    PropertyList(binary_plist::Error),
    DictionaryRequired,
}
impl SceneReply {
    /// Decode caller-extracted UVPropertyList.data. None means no payload
    /// wrapper. Validates a binary plist dictionary, without native coercions.
    pub fn from_property_list_data(data: Option<&[u8]>) -> Result<Self, Error> {
        let payload = match data {
            None => None,
            Some(data) => match binary_plist::decode(data).map_err(Error::PropertyList)? {
                Value::Dictionary(d) => Some(d),
                _ => return Err(Error::DictionaryRequired),
            },
        };
        Ok(Self { payload })
    }
    /// Decoded value projection only. Unknown numbered settings are ignored.
    pub fn from_settings(info: Option<&BTreeMap<i64, Value>>) -> Result<Self, Error> {
        let payload = match info.and_then(|i| i.get(&PAYLOAD)) {
            None => None,
            Some(Value::Dictionary(d)) => Some(d.clone()),
            _ => return Err(Error::DictionaryRequired),
        };
        Ok(Self { payload })
    }
    pub fn to_settings(&self) -> BTreeMap<i64, Value> {
        self.payload
            .as_ref()
            .map(|d| BTreeMap::from([(PAYLOAD, Value::Dictionary(d.clone()))]))
            .unwrap_or_default()
    }
}
