//! Product identity and seed wire values. No artifact reuse/rank arbitration is implied.
use crate::{
    payload_codec::Value,
    update_seed::{uint64, HostUpdateSeed},
};
use std::collections::BTreeMap;
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PreviewProductIdentity {
    pub source_identifier: String,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct PreviewProductSeed {
    pub content_seed: u64,
    pub capabilities_rank: i64,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Dictionary,
    Missing(&'static str),
    Type(&'static str),
}
fn fields(value: &Value) -> Result<&BTreeMap<String, Value>, Error> {
    match value {
        Value::Dictionary(f) => Ok(f),
        _ => Err(Error::Dictionary),
    }
}
fn required<'a>(f: &'a BTreeMap<String, Value>, key: &'static str) -> Result<&'a Value, Error> {
    f.get(key).ok_or(Error::Missing(key))
}
// Qualified native Int conversion for serialized primitives. Real2^63 is accepted
// and saturates to max; an integer2^63 fails. Do not reuse UInt64 conversion here.
fn rank(value: &Value) -> Option<i64> {
    match value {
        Value::Integer(n) => Some(*n),
        Value::Unsigned(n) => i64::try_from(*n).ok(),
        Value::Boolean(b) => Some(i64::from(*b)),
        Value::Real(n)
            if n.is_finite()
                && n.fract() == 0.0
                && *n >= -9223372036854775808.0
                && *n <= 9223372036854775808.0 =>
        {
            Some(*n as i64)
        }
        _ => None,
    }
}
impl PreviewProductIdentity {
    pub fn decode(value: &Value) -> Result<Self, Error> {
        let f = fields(value)?;
        match required(f, "sourceIdentifier")? {
            Value::String(s) => Ok(Self {
                source_identifier: s.clone(),
            }),
            _ => Err(Error::Type("sourceIdentifier")),
        }
    }
    pub fn to_value(&self) -> Value {
        Value::Dictionary(
            [(
                "sourceIdentifier".into(),
                Value::String(self.source_identifier.clone()),
            )]
            .into_iter()
            .collect(),
        )
    }
}
impl PreviewProductSeed {
    pub fn decode(value: &Value) -> Result<Self, Error> {
        let f = fields(value)?;
        let content_seed = uint64(required(f, "contentSeed")?).ok_or(Error::Type("contentSeed"))?;
        let capabilities_rank =
            rank(required(f, "capabilitiesRank")?).ok_or(Error::Type("capabilitiesRank"))?;
        Ok(Self {
            content_seed,
            capabilities_rank,
        })
    }
    pub fn to_value(&self) -> Value {
        Value::Dictionary(
            [
                (
                    "contentSeed".into(),
                    HostUpdateSeed::new(self.content_seed).to_value(),
                ),
                (
                    "capabilitiesRank".into(),
                    Value::Integer(self.capabilities_rank),
                ),
            ]
            .into_iter()
            .collect(),
        )
    }
}
