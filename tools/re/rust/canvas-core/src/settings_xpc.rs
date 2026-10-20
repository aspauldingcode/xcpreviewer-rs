//! Strict projection of observed BSSettings XPC dictionaries.
//! Caller supplies already typed XPC values. No Mach/XPC byte parser, secure
//! archive decoder, native object construction, or attachment transfer occurs.
use std::collections::BTreeMap;
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum XpcValue {
    Dictionary(BTreeMap<String, XpcValue>),
    Array(Vec<XpcValue>),
    UInt64(u64),
    Int64(i64),
    Bool(bool),
    Null,
    /// Raw IEEE-754 binary64 bits; equality preserves signed zero and NaN payloads.
    /// No floating-point arithmetic or normalization is performed by the codec.
    DoubleBits(u64),
    Data(Vec<u8>),
    String(String),
    /// Opaque attachment-table ordinal, never a portable OS descriptor/right.
    DescriptorRef(u32),
}
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct ArchivedSettings {
    pub flags: BTreeMap<u64, bool>,
    /// Opaque native secure archives, including every byte of their header.
    /// These are NOT the bplist00 values handled by binary_plist.
    pub objects: BTreeMap<u64, Vec<u8>>,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error { Envelope, Bucket, Entry, DuplicateSlot, UnsupportedObject }
impl ArchivedSettings {
    /// Accept only the observed root-data/marker-2 object variant. Unsupported
    /// variants fail closed; this is deliberately narrower than native decoding.
    pub fn from_xpc(value: &XpcValue) -> Result<Self, Error> {
        use XpcValue::*;
        let Dictionary(d) = value else { return Err(Error::Envelope) };
        if d.keys().any(|k| k != "flags" && k != "objects") { return Err(Error::Envelope); }
        let mut result = Self::default();
        for (name, bucket) in d {
            let Array(entries) = bucket else { return Err(Error::Bucket) };
            for entry in entries {
                let Array(parts) = entry else { return Err(Error::Entry) };
                let Some(UInt64(slot)) = parts.first() else { return Err(Error::Entry) };
                if name == "flags" {
                    let [UInt64(_), Bool(flag)] = parts.as_slice() else { return Err(Error::Entry) };
                    if result.flags.insert(*slot, *flag).is_some() { return Err(Error::DuplicateSlot); }
                } else {
                    let [UInt64(_), Dictionary(object), Int64(2)] = parts.as_slice() else { return Err(Error::UnsupportedObject) };
                    let Some(Data(bytes)) = object.get("root") else { return Err(Error::UnsupportedObject) };
                    if object.len() != 1 { return Err(Error::UnsupportedObject); }
                    if result.objects.insert(*slot, bytes.clone()).is_some() { return Err(Error::DuplicateSlot); }
                }
            }
        }
        Ok(result)
    }
    /// Canonical ordering of the observed envelope; preserves opaque archives.
    /// This does not create fresh native secure archives from portable values.
    pub fn to_xpc(&self) -> XpcValue {
        use XpcValue::*;
        let mut d = BTreeMap::new();
        if !self.flags.is_empty() {
            d.insert("flags".into(), Array(self.flags.iter().map(|(&k, &v)| Array(vec![UInt64(k), Bool(v)])).collect()));
        }
        if !self.objects.is_empty() {
            d.insert("objects".into(), Array(self.objects.iter().map(|(&k, v)| Array(vec![UInt64(k), Dictionary(BTreeMap::from([("root".into(), Data(v.clone()))])), Int64(2)])).collect()));
        }
        Dictionary(d)
    }
    /// None is native's observed absent flag; false is an explicit stored flag.
    pub fn flag(&self, slot: u64) -> Option<bool> { self.flags.get(&slot).copied() }
}
