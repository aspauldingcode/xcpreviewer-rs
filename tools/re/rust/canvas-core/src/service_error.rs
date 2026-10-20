//! Selected service NSError field projection, separate from CPX envelopes.
//! Code descriptions come from the pinned native factory; runtime coverage is
//! the owned reply-operation-failure case. This does not decode error archives.
use crate::settings_xpc::XpcValue;
use std::collections::BTreeMap;
pub const DOMAIN: &str = "BSServiceConnectionErrorDomain";
/// Native factory table; unknown signed codes retain their numeric identity.
pub fn code_description(code: i64) -> &'static str {
    match code {
        0 => "None",
        1 => "ConnectionInterrupted",
        2 => "ConnectionInvalidated",
        3 => "OperationFailed",
        4 => "CodingFailed",
        _ => "(unknown)",
    }
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ServiceConnectionError {
    pub code: i64,
    pub failure_reason: String,
    /// Other already projected userInfo values; native object classes/archives
    /// require their own adapters. Reserved keys are overwritten on output.
    pub additional_info: BTreeMap<String, XpcValue>,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error { Domain, UserInfo, CodeDescription, FailureReason }
impl ServiceConnectionError {
    pub fn from_fields(domain: &str, code: i64, user_info: &XpcValue) -> Result<Self, Error> {
        if domain != DOMAIN { return Err(Error::Domain); }
        let XpcValue::Dictionary(info) = user_info else { return Err(Error::UserInfo) };
        if info.get("BSErrorCodeDescription") != Some(&XpcValue::String(code_description(code).into())) {
            return Err(Error::CodeDescription);
        }
        let Some(XpcValue::String(reason)) = info.get("NSLocalizedFailureReason") else {
            return Err(Error::FailureReason);
        };
        let mut additional_info = info.clone();
        additional_info.remove("BSErrorCodeDescription");
        additional_info.remove("NSLocalizedFailureReason");
        Ok(Self { code, failure_reason: reason.clone(), additional_info })
    }
    /// Mirrors the recovered factory's extra-info copy, then reserved-key writes.
    pub fn to_user_info(&self) -> XpcValue {
        let mut info = self.additional_info.clone();
        info.insert("BSErrorCodeDescription".into(), XpcValue::String(code_description(self.code).into()));
        info.insert("NSLocalizedFailureReason".into(), XpcValue::String(self.failure_reason.clone()));
        XpcValue::Dictionary(info)
    }
}
