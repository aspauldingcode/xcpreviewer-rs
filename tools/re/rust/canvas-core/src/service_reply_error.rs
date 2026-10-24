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
