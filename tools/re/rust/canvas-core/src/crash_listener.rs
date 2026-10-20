//! Source-guided crash-listener value codec. No daemon connection, task, process
//! action, cancellation or target-operation settlement is performed here.
use crate::{binary_plist, crash_report, payload_codec::Value};
use std::collections::BTreeMap;
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum ProcessIdentifier {
    Pid(i32),
    ProcessName(String),
}
#[derive(Clone, Debug, PartialEq)]
pub struct NextCrashRequest {
    pub process: ProcessIdentifier,
    pub timeout: f64,
}
#[derive(Clone, Debug, PartialEq)]
pub struct NextCrashResponse {
    pub crash_report: crash_report::CrashReport,
}
#[derive(Clone, Debug, PartialEq)]
pub enum CrashListenerMessage {
    StartListeningIfNeeded,
    NextCrashReport(NextCrashRequest),
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Plist(binary_plist::Error),
    Missing(&'static str),
    Type(&'static str),
    Range(&'static str),
    UnknownDiscriminant(String),
    Report(crash_report::Error),
}
type Fields = BTreeMap<String, Value>;
fn fields(v: &Value) -> Result<&Fields, Error> {
    if let Value::Dictionary(d) = v {
        Ok(d)
    } else {
        Err(Error::Type("dictionary"))
    }
}
fn required<'a>(d: &'a Fields, k: &'static str) -> Result<&'a Value, Error> {
    d.get(k).ok_or(Error::Missing(k))
}
fn tag(d: &Fields) -> Result<&str, Error> {
    if let Value::String(s) = required(d, "discriminant")? {
        Ok(s)
    } else {
        Err(Error::Type("discriminant"))
    }
}
fn dict(pairs: impl IntoIterator<Item = (&'static str, Value)>) -> Value {
    Value::Dictionary(pairs.into_iter().map(|(k, v)| (k.into(), v)).collect())
}
impl ProcessIdentifier {
    pub fn decode(v: &Value) -> Result<Self, Error> {
        let d = fields(v)?;
        match tag(d)? {
            "pid" => match required(d, "payload")? {
                Value::Integer(n) => Ok(Self::Pid(
                    i32::try_from(*n).map_err(|_| Error::Range("payload"))?,
                )),
                _ => Err(Error::Type("payload")),
            },
            "processName" => match required(d, "payload")? {
                Value::String(s) => Ok(Self::ProcessName(s.clone())),
                _ => Err(Error::Type("payload")),
            },
            s => Err(Error::UnknownDiscriminant(s.into())),
        }
    }
    pub fn to_value(&self) -> Value {
        let (tag, payload) = match self {
            Self::Pid(n) => ("pid", Value::Integer(i64::from(*n))),
            Self::ProcessName(s) => ("processName", Value::String(s.clone())),
        };
        dict([
            ("discriminant", Value::String(tag.into())),
            ("payload", payload),
        ])
    }
}
impl NextCrashRequest {
    pub fn decode(v: &Value) -> Result<Self, Error> {
        let d = fields(v)?;
        let process = ProcessIdentifier::decode(required(d, "process")?)?;
        let timeout = match required(d, "timeout")? {
            Value::Real(t) => *t,
            _ => return Err(Error::Type("timeout")),
        };
        Ok(Self { process, timeout })
    }
    pub fn decode_binary(bytes: &[u8]) -> Result<Self, Error> {
        Self::decode(&binary_plist::decode(bytes).map_err(Error::Plist)?)
    }
    pub fn to_value(&self) -> Value {
        dict([
            ("process", self.process.to_value()),
            ("timeout", Value::Real(self.timeout)),
        ])
    }
}
impl CrashListenerMessage {
    pub fn decode(v: &Value) -> Result<Self, Error> {
        let d = fields(v)?;
        match tag(d)? {
            "startListeningIfNeeded" => Ok(Self::StartListeningIfNeeded),
            "nextCrashReport" => Ok(Self::NextCrashReport(NextCrashRequest::decode(required(
                d, "payload",
            )?)?)),
            s => Err(Error::UnknownDiscriminant(s.into())),
        }
    }
    pub fn decode_binary(bytes: &[u8]) -> Result<Self, Error> {
        Self::decode(&binary_plist::decode(bytes).map_err(Error::Plist)?)
    }
    pub fn to_value(&self) -> Value {
        match self {
            Self::StartListeningIfNeeded => dict([(
                "discriminant",
                Value::String("startListeningIfNeeded".into()),
            )]),
            Self::NextCrashReport(r) => dict([
                ("discriminant", Value::String("nextCrashReport".into())),
                ("payload", r.to_value()),
            ]),
        }
    }
}
impl NextCrashResponse {
    pub fn decode(v: &Value) -> Result<Self, Error> {
        Self::decode_with_entropy(v, &mut || Err(crash_report::Error::EntropyRequired))
    }
    pub fn decode_binary(bytes: &[u8]) -> Result<Self, Error> {
        Self::decode(&binary_plist::decode(bytes).map_err(Error::Plist)?)
    }
    pub fn decode_with_entropy(
        v: &Value,
        entropy: &mut impl FnMut() -> Result<[u8; 16], crash_report::Error>,
    ) -> Result<Self, Error> {
        let d = fields(v)?;
        let crash_report =
            crash_report::CrashReport::decode_with_entropy(required(d, "crashReport")?, entropy)
                .map_err(Error::Report)?;
        Ok(Self { crash_report })
    }
    pub fn to_value(&self) -> Value {
        dict([("crashReport", self.crash_report.to_value())])
    }
}
