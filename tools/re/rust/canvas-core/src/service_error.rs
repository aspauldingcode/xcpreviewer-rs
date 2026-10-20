//! Selected service NSError field projection and optional archive diagnostics.
//! Code descriptions come from the pinned native factory; runtime coverage is
//! the owned reply-operation-failure case. The archive entry point delegates to
//! the separately bounded string-valued NSErrorDetails profile.
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
pub enum Error { Domain, UserInfo, CodeDescription, FailureReason, Archive(crate::nserror_archive::Error) }
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

impl ServiceConnectionError {
    /// Project the measured string-valued archive diagnostics into this model.
    pub fn from_archive(bytes: &[u8]) -> Result<Self, Error> {
        let details = crate::nserror_archive::NSErrorDetails::decode(bytes).map_err(Error::Archive)?;
        let info = XpcValue::Dictionary(details.user_info.into_iter().map(|(k,v)|(k,XpcValue::String(v))).collect());
        Self::from_fields(&details.error.domain, details.error.code, &info)
    }
}
