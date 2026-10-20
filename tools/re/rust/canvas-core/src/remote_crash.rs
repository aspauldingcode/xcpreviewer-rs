//! Remote crash notification, diagnostics report and request codecs.
//! PreviewRemoteEvents is a crash/diagnostics stream, not pointer/touch input.
//! Transport and lifecycle settlement remain separate acceptance tracks.
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
    /// Narrow helpers cannot represent a report; use the full event/request enums.
    UnsupportedCrashReport,
    Report(crate::crash_report::Error),
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

/// Complete structural coverage of the two recovered event cases. Native error
/// payloads, transport and resource settlement are separate acceptance tracks.
#[derive(Clone, Debug, PartialEq)]
pub enum RemoteEventPayload {
    AgentCrashed(AgentCrashNotification),
    AgentCrashedDiagnostics(crate::crash_report::CrashReport),
}
#[derive(Clone, Debug, PartialEq)]
pub enum RemoteEventRequest {
    RequestScreenshot,
    SymbolicateCrashedDiagnostics(crate::crash_report::CrashReport),
}
fn report(
    v: &Value,
    entropy: &mut impl FnMut() -> Result<[u8; 16], crate::crash_report::Error>,
) -> Result<crate::crash_report::CrashReport, Error> {
    crate::crash_report::CrashReport::decode_with_entropy(v, entropy).map_err(Error::Report)
}
impl RemoteEventPayload {
    pub fn decode(v: &Value) -> Result<Self, Error> {
        Self::decode_with_entropy(v, &mut || Err(crate::crash_report::Error::EntropyRequired))
    }
    pub fn decode_binary(bytes: &[u8]) -> Result<Self, Error> {
        Self::decode(&binary_plist::decode(bytes).map_err(Error::Plist)?)
    }
    pub fn decode_with_entropy(
        v: &Value,
        entropy: &mut impl FnMut() -> Result<[u8; 16], crate::crash_report::Error>,
    ) -> Result<Self, Error> {
        let d = dictionary(v, "remoteEventPayload")?;
        match discriminant(d)? {
            "agentCrashed" => Ok(Self::AgentCrashed(AgentCrashNotification::decode(v)?)),
            "agentCrashedDiagnostics" => Ok(Self::AgentCrashedDiagnostics(report(
                required(d, "crashReport")?,
                entropy,
            )?)),
            s => Err(Error::UnknownDiscriminant(s.into())),
        }
    }
    pub fn to_value(&self) -> Value {
        match self {
            Self::AgentCrashed(n) => n.to_value(),
            Self::AgentCrashedDiagnostics(r) => Value::Dictionary(Fields::from([
                (
                    "discriminant".into(),
                    Value::String("agentCrashedDiagnostics".into()),
                ),
                ("crashReport".into(), r.to_value()),
            ])),
        }
    }
}
impl RemoteEventRequest {
    pub fn decode(v: &Value) -> Result<Self, Error> {
        Self::decode_with_entropy(v, &mut || Err(crate::crash_report::Error::EntropyRequired))
    }
    pub fn decode_binary(bytes: &[u8]) -> Result<Self, Error> {
        Self::decode(&binary_plist::decode(bytes).map_err(Error::Plist)?)
    }
    pub fn decode_with_entropy(
        v: &Value,
        entropy: &mut impl FnMut() -> Result<[u8; 16], crate::crash_report::Error>,
    ) -> Result<Self, Error> {
        let d = dictionary(v, "remoteEventRequest")?;
        match discriminant(d)? {
            "requestScreenshot" => Ok(Self::RequestScreenshot),
            "symbolicateCrashedDiagnostics" => Ok(Self::SymbolicateCrashedDiagnostics(report(
                required(d, "crashReport")?,
                entropy,
            )?)),
            s => Err(Error::UnknownDiscriminant(s.into())),
        }
    }
    pub fn to_value(&self) -> Value {
        match self {
            Self::RequestScreenshot => ScreenshotRequest.to_value(),
            Self::SymbolicateCrashedDiagnostics(r) => Value::Dictionary(Fields::from([
                (
                    "discriminant".into(),
                    Value::String("symbolicateCrashedDiagnostics".into()),
                ),
                ("crashReport".into(), r.to_value()),
            ])),
        }
    }
}
