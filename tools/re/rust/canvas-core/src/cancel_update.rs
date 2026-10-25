//! Cancel-update identity values only. Sending a message, cancelling an update,
//! matching a live request or settling resources is outside this value codec.
use crate::payload_codec::Value;
use std::collections::BTreeMap;
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CancelUpdatePayload {
    pub pid: i32,
    pub content_identifier: String,
    /// Native PreviewUpdateSeed is UInt64, distinct from signed scene timing seeds.
    pub update_seed: u64,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Error {
    Missing(&'static str),
    Type(&'static str),
    Range(&'static str),
}
impl CancelUpdatePayload {
    pub fn decode_dictionary(fields: &BTreeMap<String, Value>) -> Result<Self, Error> {
        let value = fields.get("pid").ok_or(Error::Missing("pid"))?;
        let pid = crate::service_process::integer(value, i64::from(i32::MIN), i64::from(i32::MAX))
            .ok_or(Error::Range("pid"))? as i32;
        let Value::String(content_identifier) = fields
            .get("contentIdentifier")
            .ok_or(Error::Missing("contentIdentifier"))?
        else {
            return Err(Error::Type("contentIdentifier"));
        };
        let value = fields
            .get("updateSeed")
            .ok_or(Error::Missing("updateSeed"))?;
        // Measured Foundation primitive UInt64 casts; fractional, negative,
        // nonfinite and the rounded Double(2^64) endpoint reject.
        let update_seed = match value {
            Value::Unsigned(n) => *n,
            Value::Integer(n) if *n >= 0 => *n as u64,
            Value::Boolean(n) => u64::from(*n),
            Value::Real(n)
                if n.is_finite()
                    && n.fract() == 0.0
                    && *n >= 0.0
                    && *n < 18446744073709551616.0 =>
            {
                *n as u64
            }
            _ => return Err(Error::Range("updateSeed")),
        };
        Ok(Self {
            pid,
            content_identifier: content_identifier.clone(),
            update_seed,
        })
    }
    pub fn to_dictionary(&self) -> BTreeMap<String, Value> {
        BTreeMap::from([
            ("pid".into(), Value::Integer(i64::from(self.pid))),
            (
                "contentIdentifier".into(),
                Value::String(self.content_identifier.clone()),
            ),
            (
                "updateSeed".into(),
                if self.update_seed <= i64::MAX as u64 {
                    Value::Integer(self.update_seed as i64)
                } else {
                    Value::Unsigned(self.update_seed)
                },
            ),
        ])
    }
}
