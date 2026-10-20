//! Partial RemoteEventPayload codec: agentCrashed notifications only.
//! PreviewRemoteEvents is a crash/diagnostics stream, not pointer/touch input.
//! CrashReport decoding and transport/lifecycle settlement remain unsupported.
use crate::{binary_plist, payload_codec::Value};
use std::collections::BTreeMap;
pub const STREAM_IDENTIFIER: &str = "Ultraviolet.PreviewRemoteEvents";
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum DiagnosticsBehavior {
    WillProvide,
    CanSymbolicate,
    Unavailable,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct AgentCrashNotification {
    pub pid: i32,
    pub agent_behavior: DiagnosticsBehavior,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Plist(binary_plist::Error),
    Missing(&'static str),
    Type(&'static str),
    Range(&'static str),
    UnknownDiscriminant(String),
    UnsupportedCrashReport,
}
type Fields = BTreeMap<String, Value>;
fn dictionary<'a>(v: &'a Value, key: &'static str) -> Result<&'a Fields, Error> {
    match v {
        Value::Dictionary(d) => Ok(d),
        _ => Err(Error::Type(key)),
    }
}
fn required<'a>(d: &'a Fields, key: &'static str) -> Result<&'a Value, Error> {
    d.get(key).ok_or(Error::Missing(key))
}
fn discriminant(d: &Fields) -> Result<&str, Error> {
    match required(d, "discriminant")? {
        Value::String(s) => Ok(s),
        _ => Err(Error::Type("discriminant")),
    }
}
impl DiagnosticsBehavior {
    pub fn decode(v: &Value) -> Result<Self, Error> {
        let d = dictionary(v, "agentBehavior")?;
        match discriminant(d)? {
            "willProvide" => Ok(Self::WillProvide),
            "canSymbolicate" => Ok(Self::CanSymbolicate),
            "unavailable" => Ok(Self::Unavailable),
            s => Err(Error::UnknownDiscriminant(s.into())),
        }
    }
    pub fn to_value(self) -> Value {
        let s = match self {
            Self::WillProvide => "willProvide",
            Self::CanSymbolicate => "canSymbolicate",
            Self::Unavailable => "unavailable",
        };
        Value::Dictionary(BTreeMap::from([(
            "discriminant".into(),
            Value::String(s.into()),
        )]))
    }
}
impl AgentCrashNotification {
    /// A notification is data; it does not establish resource release, operation
    /// settlement or that a PID is still the same process. No process is acted on.
    pub fn decode(v: &Value) -> Result<Self, Error> {
        let d = dictionary(v, "remoteEventPayload")?;
        match discriminant(d)? {
            "agentCrashed" => (),
            "agentCrashedDiagnostics" => return Err(Error::UnsupportedCrashReport),
            s => return Err(Error::UnknownDiscriminant(s.into())),
        }
        // Native order: optional modern behavior, required legacy fallback only
        // when absent, then required Int32 PID. A malformed modern field errors.
        let agent_behavior = match d.get("agentBehavior") {
            Some(v) => DiagnosticsBehavior::decode(v)?,
            None => match required(d, "diagnosticsComing")? {
                Value::Boolean(true) => DiagnosticsBehavior::WillProvide,
                Value::Boolean(false) => DiagnosticsBehavior::Unavailable,
                _ => return Err(Error::Type("diagnosticsComing")),
            },
        };
        let pid = match required(d, "pid")? {
            Value::Integer(n) => i32::try_from(*n).map_err(|_| Error::Range("pid"))?,
            _ => return Err(Error::Type("pid")),
        };
        Ok(Self {
            pid,
            agent_behavior,
        })
    }
    pub fn decode_binary(bytes: &[u8]) -> Result<Self, Error> {
        Self::decode(&binary_plist::decode(bytes).map_err(Error::Plist)?)
    }
    /// Emit the recovered decoded-value tree, including the legacy compatibility
    /// boolean. This is not a binary plist encoder or a transport send operation.
    pub fn to_value(&self) -> Value {
        Value::Dictionary(BTreeMap::from([
            ("discriminant".into(), Value::String("agentCrashed".into())),
            ("pid".into(), Value::Integer(i64::from(self.pid))),
            ("agentBehavior".into(), self.agent_behavior.to_value()),
            (
                "diagnosticsComing".into(),
                Value::Boolean(self.agent_behavior == DiagnosticsBehavior::WillProvide),
            ),
        ]))
    }
}

/// Partial request codec. The requestScreenshot case has no decoded payload.
/// This type describes a request; it does not invoke capture or send a message.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct ScreenshotRequest;
impl ScreenshotRequest {
    pub fn decode(value: &Value) -> Result<Self, Error> {
        match discriminant(dictionary(value, "remoteEventRequest")?)? {
            "requestScreenshot" => Ok(Self),
            "symbolicateCrashedDiagnostics" => Err(Error::UnsupportedCrashReport),
            s => Err(Error::UnknownDiscriminant(s.into())),
        }
    }
    pub fn decode_binary(bytes: &[u8]) -> Result<Self, Error> {
        Self::decode(&binary_plist::decode(bytes).map_err(Error::Plist)?)
    }
    pub fn to_value(self) -> Value {
        Value::Dictionary(BTreeMap::from([(
            "discriminant".into(),
            Value::String("requestScreenshot".into()),
        )]))
    }
}
