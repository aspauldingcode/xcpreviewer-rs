//! Selected native scene-action proxy invocation value envelope.
//! Actions are opaque pre-encoded values; this does not encode native NSSet
//! elements, export a completion capability or execute a service request.
use crate::{scene_identity::SceneIdentity, settings_xpc::XpcValue};
use std::collections::BTreeMap;
pub const SELECTOR: &str = "sceneID:sendActions:toExtension:completion:";
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct WorkspaceActionInvocation {
    pub connection_id: u64,
    pub identity: SceneIdentity,
    /// Preserve already encoded action values and their observed array order.
    /// Native element encoding and unordered NSSet iteration are separate.
    pub actions: Vec<XpcValue>,
    pub extension: Option<String>,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error { Envelope, Route, Selector, Identity, Actions, Extension }
impl WorkspaceActionInvocation {
    /// Strict projection of the measured forward invocation. Reverse routes and
    /// unobserved fields reject as an original fail-closed policy.
    pub fn from_xpc(value: &XpcValue) -> Result<Self, Error> {
        use XpcValue::*;
        let Dictionary(d) = value else { return Err(Error::Envelope) };
        if d.keys().any(|k| !matches!(k.as_str(), "bsxpc_CID" | "bsxpc_CIDr" | "bsxpc_SEL" | "1" | "2" | "3")) { return Err(Error::Envelope); }
        let Some(UInt64(connection_id)) = d.get("bsxpc_CID") else { return Err(Error::Route) };
        if d.get("bsxpc_CIDr") != Some(&Bool(false)) { return Err(Error::Route); }
        if d.get("bsxpc_SEL") != Some(&String(SELECTOR.into())) { return Err(Error::Selector); }
        let identity = SceneIdentity::from_xpc(d.get("1").ok_or(Error::Identity)?).map_err(|_| Error::Identity)?;
        let Some(Array(actions)) = d.get("2") else { return Err(Error::Actions) };
        let extension = match d.get("3") { None => None, Some(String(s)) => Some(s.clone()), _ => return Err(Error::Extension) };
        Ok(Self { connection_id: *connection_id, identity, actions: actions.clone(), extension })
    }
    /// Value snapshot only. Completion travels through the transport reply path;
    /// it has no inline fourth argument in the measured dictionary.
    pub fn to_xpc(&self) -> XpcValue {
        use XpcValue::*;
        let mut d = BTreeMap::from([
            ("bsxpc_CID".into(), UInt64(self.connection_id)),
            ("bsxpc_CIDr".into(), Bool(false)),
            ("bsxpc_SEL".into(), String(SELECTOR.into())),
            ("1".into(), self.identity.to_xpc()),
            ("2".into(), Array(self.actions.clone())),
        ]);
        if let Some(s) = &self.extension { d.insert("3".into(), String(s.clone())); }
        Dictionary(d)
    }
}

/// Measured nullable NSError completion argument. Archives stay opaque; this
/// adapter does not interpret bplist17, reconstruct NSError or assert validity.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct WorkspaceActionCompletion {
    pub error_archive: Option<Vec<u8>>,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum CompletionError { Envelope, ErrorClass, Archive }
impl WorkspaceActionCompletion {
    /// Strict projection of the selected reply argument payload. Unknown keys
    /// reject as original policy; the native selected decoder ignores slot 2.
    pub fn from_xpc(value: &XpcValue) -> Result<Self, CompletionError> {
        use XpcValue::*;
        let Dictionary(d) = value else { return Err(CompletionError::Envelope) };
        if d.keys().any(|k| k != "1") { return Err(CompletionError::Envelope); }
        let Some(value) = d.get("1") else { return Ok(Self::default()) };
        let Dictionary(error) = value else { return Err(CompletionError::Envelope) };
        if error.len() != 2 { return Err(CompletionError::Envelope); }
        if error.get("bsx_class") != Some(&String("NSError".into())) { return Err(CompletionError::ErrorClass); }
        let Some(Data(bytes)) = error.get("root") else { return Err(CompletionError::Archive) };
        Ok(Self { error_archive: Some(bytes.clone()) })
    }
    /// Preserve every archive byte, without synthesizing or validating archives.
    pub fn to_xpc(&self) -> XpcValue {
        use XpcValue::*;
        Dictionary(match &self.error_archive {
            None => BTreeMap::new(),
            Some(bytes) => BTreeMap::from([("1".into(), Dictionary(BTreeMap::from([
                ("bsx_class".into(), String("NSError".into())), ("root".into(), Data(bytes.clone())),
            ])))]),
        })
    }
}
