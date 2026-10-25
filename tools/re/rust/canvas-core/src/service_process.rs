//! Service ProcessID wire values, distinct from crash-listener ProcessIdentifier.
//! Synthetic audit-token words are data only: no task lookup, authorization,
//! signalling, process-control operation or resource settlement is performed.
use crate::payload_codec::Value;
use std::collections::BTreeMap;
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum ProcessTarget {
    AuditToken([u32; 8]),
    Pid(i32),
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Error {
    Type(&'static str),
    Missing(&'static str),
    Range(&'static str),
}
// Primitive Foundation NSNumber compatibility profile. Arbitrary native objects
// are excluded; caller-owned decoded values remain separate from native rights.
fn integer(value: &Value, min: i64, max: i64) -> Option<i64> {
    match value {
        Value::Integer(n) if *n >= min && *n <= max => Some(*n),
        Value::Boolean(n) => Some(i64::from(*n)),
        Value::Real(n)
            if n.is_finite() && n.fract() == 0.0 && *n >= min as f64 && *n <= max as f64 =>
        {
            Some(*n as i64)
        }
        _ => None,
    }
}
fn token(value: &Value) -> Option<[u32; 8]> {
    let Value::Dictionary(fields) = value else {
        return None;
    };
    let Value::Array(values) = fields.get("val")? else {
        return None;
    };
    if values.len() != 8 {
        return None;
    }
    let mut words = [0; 8];
    for (word, value) in words.iter_mut().zip(values) {
        *word = integer(value, 0, i64::from(u32::MAX))? as u32;
    }
    Some(words)
}
impl ProcessTarget {
    /// Prefer a valid auditToken only under that exact discriminant. Any primary
    /// decode failure retries legacy pid, including unknown/missing/wrong-type
    /// discriminants and malformed token fields. Final errors describe the pid
    /// fallback using original portable categories, not native NSError identity.
    pub fn decode(value: &Value) -> Result<Self, Error> {
        let Value::Dictionary(fields) = value else {
            return Err(Error::Type("process"));
        };
        Self::decode_dictionary(fields)
    }
    pub fn decode_dictionary(fields: &BTreeMap<String, Value>) -> Result<Self, Error> {
        if matches!(fields.get("discriminant"),Some(Value::String(s)) if s=="auditToken") {
            if let Some(words) = fields.get("auditToken").and_then(token) {
                return Ok(Self::AuditToken(words));
            }
        }
        let value = fields.get("pid").ok_or(Error::Missing("pid"))?;
        let pid = integer(value, i64::from(i32::MIN), i64::from(i32::MAX)).ok_or(match value {
            Value::Integer(_) | Value::Real(_) => Error::Range("pid"),
            _ => Error::Type("pid"),
        })?;
        Ok(Self::Pid(pid as i32))
    }
    /// SDK audit_token_to_pid selects word5 interpreted as signed pid_t. This is
    /// value extraction, not validation of token origin or authority.
    pub fn pid(&self) -> i32 {
        match self {
            Self::Pid(pid) => *pid,
            Self::AuditToken(words) => words[5] as i32,
        }
    }
    /// Canonical output retains legacy pid even for the audit-token form. A
    /// conflicting input pid is replaced with the token-derived value.
    pub fn to_dictionary(&self) -> BTreeMap<String, Value> {
        let mut fields = BTreeMap::from([("pid".into(), Value::Integer(i64::from(self.pid())))]);
        let tag = match self {
            Self::Pid(_) => "pid",
            Self::AuditToken(words) => {
                fields.insert(
                    "auditToken".into(),
                    Value::Dictionary(BTreeMap::from([(
                        "val".into(),
                        Value::Array(
                            words
                                .iter()
                                .map(|word| Value::Integer(i64::from(*word)))
                                .collect(),
                        ),
                    )])),
                );
                "auditToken"
            }
        };
        fields.insert("discriminant".into(), Value::String(tag.into()));
        fields
    }
    pub fn to_value(&self) -> Value {
        Value::Dictionary(self.to_dictionary())
    }
}
