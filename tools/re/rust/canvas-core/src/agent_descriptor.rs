//! Agent identity values recovered from MessagingHost. Paths and bundle IDs are
//! opaque strings: no file lookup, launch, authorization or identity validation.
use crate::payload_codec::Value;
use std::collections::BTreeMap;
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct AgentBundle {
    pub bundle_id: String,
    pub path: Option<String>,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct AgentDescriptor {
    pub id_across_relaunches: String,
    pub bundle: AgentBundle,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Missing(&'static str),
    Type(&'static str),
}
fn fields(value: &Value) -> Result<&BTreeMap<String, Value>, Error> {
    match value {
        Value::Dictionary(fields) => Ok(fields),
        _ => Err(Error::Type("agentDictionary")),
    }
}
fn text(fields: &BTreeMap<String, Value>, key: &'static str) -> Result<String, Error> {
    match fields.get(key) {
        None => Err(Error::Missing(key)),
        Some(Value::String(value)) => Ok(value.clone()),
        _ => Err(Error::Type(key)),
    }
}
impl AgentBundle {
    pub fn decode(value: &Value) -> Result<Self, Error> {
        let fields = fields(value)?;
        let bundle_id = text(fields, "bundleID")?;
        let path = fields
            .get("path")
            .map(|_| text(fields, "path"))
            .transpose()?;
        // Native decoder reads bundleID/path directly, ignoring discriminant.
        Ok(Self { bundle_id, path })
    }
    pub fn to_value(&self) -> Value {
        let mut fields = BTreeMap::from([
            ("bundleID".into(), Value::String(self.bundle_id.clone())),
            (
                "discriminant".into(),
                Value::String(
                    if self.path.is_some() {
                        "pathAndBundleID"
                    } else {
                        "bundleID"
                    }
                    .into(),
                ),
            ),
        ]);
        if let Some(path) = &self.path {
            fields.insert("path".into(), Value::String(path.clone()));
        }
        Value::Dictionary(fields)
    }
}
impl AgentDescriptor {
    /// Any modern decode error retries a flat bundle on the whole dictionary.
    /// On fallback, idAcrossRelaunches is the empty string; no ID is allocated.
    pub fn decode(value: &Value) -> Result<Self, Error> {
        let modern = || {
            let fields = fields(value)?;
            let id_across_relaunches = text(fields, "idAcrossRelaunches")?;
            let bundle =
                AgentBundle::decode(fields.get("bundle").ok_or(Error::Missing("bundle"))?)?;
            Ok(Self {
                id_across_relaunches,
                bundle,
            })
        };
        modern().or_else(|_: Error| {
            AgentBundle::decode(value).map(|bundle| Self {
                id_across_relaunches: String::new(),
                bundle,
            })
        })
    }
    pub fn to_value(&self) -> Value {
        Value::Dictionary(BTreeMap::from([
            (
                "idAcrossRelaunches".into(),
                Value::String(self.id_across_relaunches.clone()),
            ),
            ("bundle".into(), self.bundle.to_value()),
        ]))
    }
}
