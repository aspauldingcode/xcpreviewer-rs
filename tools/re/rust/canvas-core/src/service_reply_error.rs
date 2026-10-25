//! Recognize the recovered service reply error dictionary after plist decoding.
//! This is separate from NSError archives. A failed field match stays payload.
//! Numeric bridging covers measured Foundation NSNumber-to-Int cases only;
//! arbitrary Objective-C objects and private NSError construction are excluded.
use crate::{payload_codec::Value, transport_reply::LazyReply};
use std::collections::BTreeMap;
#[derive(Clone, Debug, PartialEq)]
pub struct ServiceReplyError {
    pub domain: String,
    pub code: i64,
    pub user_info: BTreeMap<String, Value>,
}
fn integer(value: &Value) -> Option<i64> {
    match value {
        Value::Integer(n) => Some(*n),
        Value::Boolean(n) => Some(i64::from(*n)),
        Value::Real(n) if n.is_finite() && n.fract() == 0.0
            // Foundation control accepts the upper endpoint as Int.max. Rust
            // saturating float-to-int conversion reproduces that measured edge.
            && *n >= -9223372036854775808.0 && *n <= 9223372036854775808.0 => Some(*n as i64),
        _ => None,
    }
}
impl ServiceReplyError {
    /// Project the native one-time fallback after an actual encoding attempt.
    /// `encoded_entry_count` is the destination XPC dictionary count observed by
    /// the caller, not this value map's length. A nonempty result needs no retry.
    /// The caller supplies NSError.localizedDescription: this portable adapter
    /// does not recreate Foundation localization or invoke UVPropertyList/XPC.
    /// It neither validates the retry result nor proves that a send completed.
    pub fn retry_dictionary_if_empty(
        &self, encoded_entry_count: usize, localized_description: &str,
    ) -> Option<BTreeMap<String, Value>> {
        if encoded_entry_count != 0 { return None; }
        let fallback = Self {
            domain: self.domain.clone(),
            code: self.code,
            user_info: BTreeMap::from([
                ("NSLocalizedDescription".into(), Value::String(localized_description.into())),
                ("NSDebugDescription".into(), Value::String(
                    "Failed to encode full userInfo due to incompatible types".into())),
            ]),
        };
        Some(fallback.to_dictionary())
    }
    /// Build the recovered outbound value dictionary before UVPropertyList/XPC
    /// serialization. This does not validate arbitrary Objective-C userInfo,
    /// implement the native encoding fallback, or report transport completion.
    pub fn to_dictionary(&self) -> BTreeMap<String, Value> {
        self.clone().into_dictionary()
    }
    /// Move owned fields into the wire-value dictionary without cloning large
    /// userInfo before a bounded serializer gets to inspect it.
    pub fn into_dictionary(self) -> BTreeMap<String, Value> {
        BTreeMap::from([
            ("domain".into(), Value::String(self.domain)),
            ("code".into(), Value::Integer(self.code)),
            ("userInfo".into(), Value::Dictionary(self.user_info)),
        ])
    }
    /// The native helper requires domain:String, code:Int and userInfo:[String:Any].
    /// Additional root keys are ignored. No special error marker is required.
    pub fn recognize(fields: &BTreeMap<String, Value>) -> Option<Self> {
        let Value::String(domain) = fields.get("domain")? else { return None };
        let code = integer(fields.get("code")?)?;
        let Value::Dictionary(user_info) = fields.get("userInfo")? else { return None };
        Some(Self { domain: domain.clone(), code, user_info: user_info.clone() })
    }
}
/// Classify an already decoded dictionary into the observed nullable callback
/// shape. Error match => (nil,error); otherwise retain complete payload =>
/// (payload,nil). This reports no native transport or target settlement.
pub fn split_dictionary_reply(fields: BTreeMap<String, Value>) -> (Option<LazyReply>, Option<ServiceReplyError>) {
    match ServiceReplyError::recognize(&fields) {
        Some(error) => (None, Some(error)),
        None => (Some(LazyReply::Deserialized(fields)), None),
    }
}
