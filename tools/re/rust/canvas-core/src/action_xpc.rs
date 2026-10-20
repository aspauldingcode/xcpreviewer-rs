//! Observed no-responder BSAction XPC envelope and UVPropertyList variant.
//! Typed XPC input only: no packet parsing, endpoint import or native execution.
use crate::{binary_plist, payload_codec::Value, settings_xpc::{ArchivedSettings, XpcValue}};
use std::collections::BTreeMap;
#[derive(Clone, Debug, PartialEq)]
pub struct ActionEnvelope { pub info: Option<ActionInfo> }
#[derive(Clone, Debug, PartialEq)]
pub struct ActionInfo {
    archived: ArchivedSettings,
    property_lists: BTreeMap<u64, PropertyList>,
}
#[derive(Clone, Debug, PartialEq)]
struct PropertyList { data: Vec<u8>, dictionary: BTreeMap<String, Value> }
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error { Envelope, Class, Entry, DuplicateSlot, Settings(crate::settings_xpc::Error), PropertyList(binary_plist::Error), DictionaryRequired }
fn dictionary(v: &XpcValue) -> Result<&BTreeMap<String, XpcValue>, Error> {
    if let XpcValue::Dictionary(d) = v { Ok(d) } else { Err(Error::Envelope) }
}
fn class(d: &BTreeMap<String, XpcValue>, key: &str, expected: &str) -> Result<(), Error> {
    if d.get(key) == Some(&XpcValue::String(expected.into())) { Ok(()) } else { Err(Error::Class) }
}
impl ActionEnvelope {
    /// Deliberately excludes reply endpoints and all unobserved root fields.
    /// Absent info differs from an explicitly empty class-tagged BSSettings.
    pub fn from_xpc(value: &XpcValue) -> Result<Self, Error> {
        use XpcValue::*;
        let root = dictionary(value)?;
        if root.keys().any(|k| k != "i") { return Err(Error::Envelope); }
        let Some(value) = root.get("i") else { return Ok(Self { info: None }) };
        let mut body = dictionary(value)?.clone();
        class(&body, "bsx_class", "BSSettings")?;
        body.remove("bsx_class");
        let mut property_lists = BTreeMap::new();
        if let Some(bucket) = body.remove("objects") {
            let Array(entries) = bucket else { return Err(Error::Entry) };
            let mut opaque = Vec::new();
            for entry in entries {
                let Array(parts) = &entry else { return Err(Error::Entry) };
                if let [UInt64(slot), Dictionary(wrapper), Int64(1)] = parts.as_slice() {
                    class(wrapper, "__BSXPCSecureClass", "UVPropertyList")?;
                    if wrapper.len() != 2 { return Err(Error::Entry); }
                    let inner = dictionary(wrapper.get("__BSXPCSecureValue").ok_or(Error::Entry)?)?;
                    class(inner, "bsx_class", "UVPropertyList")?;
                    if inner.len() != 2 { return Err(Error::Entry); }
                    let Some(Data(data)) = inner.get("data") else { return Err(Error::Entry) };
                    let Value::Dictionary(dictionary) = binary_plist::decode(data).map_err(Error::PropertyList)? else { return Err(Error::DictionaryRequired) };
                    if property_lists.insert(*slot, PropertyList { data: data.clone(), dictionary }).is_some() { return Err(Error::DuplicateSlot); }
                } else { opaque.push(entry); }
            }
            if !opaque.is_empty() { body.insert("objects".into(), Array(opaque)); }
        }
        let archived = ArchivedSettings::from_xpc(&Dictionary(body)).map_err(Error::Settings)?;
        if property_lists.keys().any(|slot| archived.objects.contains_key(slot)) { return Err(Error::DuplicateSlot); }
        Ok(Self { info: Some(ActionInfo { archived, property_lists }) })
    }
    /// Rebuild the observed typed envelope, preserving every native archive byte.
    /// No fresh native secure archive is synthesized and no endpoint is exported.
    pub fn to_xpc(&self) -> XpcValue {
        use XpcValue::*;
        let mut root = BTreeMap::new();
        if let Some(info) = &self.info {
            let Dictionary(mut body) = info.archived.to_xpc() else { unreachable!() };
            body.insert("bsx_class".into(), String("BSSettings".into()));
            let mut entries = BTreeMap::new();
            if let Some(Array(opaque)) = body.remove("objects") {
                for entry in opaque { if let Array(parts) = &entry { if let UInt64(slot) = parts[0] { entries.insert(slot,entry); } } }
            }
            for (&slot, plist) in &info.property_lists {
                let inner = Dictionary(BTreeMap::from([("bsx_class".into(),String("UVPropertyList".into())),("data".into(),Data(plist.data.clone()))]));
                let wrapper = Dictionary(BTreeMap::from([("__BSXPCSecureClass".into(),String("UVPropertyList".into())),("__BSXPCSecureValue".into(),inner)]));
                entries.insert(slot, Array(vec![UInt64(slot),wrapper,Int64(1)]));
            }
            if !entries.is_empty() { body.insert("objects".into(),Array(entries.into_values().collect())); }
            root.insert("i".into(),Dictionary(body));
        }
        Dictionary(root)
    }
}
impl ActionInfo {
    pub fn archived_settings(&self) -> &ArchivedSettings { &self.archived }
    pub fn property_list(&self, slot: u64) -> Option<&BTreeMap<String, Value>> { self.property_lists.get(&slot).map(|p| &p.dictionary) }
}
