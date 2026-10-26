//! PreviewType/HostLocation wire values. These are distinct from the pipeline's
//! CanvasMode and request-projection HostLocation. No scene routing is performed.
use crate::payload_codec::Value;
use std::collections::BTreeMap;
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum HostLocation {
    InjectedScene { scene_identifier: String },
    MainScene,
    SimDisplayScene,
    External,
    NsPreview,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum PreviewType {
    Static,
    Hosted(HostLocation),
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Dictionary,
    Missing(&'static str),
    Type(&'static str),
    InvalidDiscriminant,
    HostLocation(Box<Error>),
}
fn fields(value: &Value) -> Result<&BTreeMap<String, Value>, Error> {
    match value {
        Value::Dictionary(v) => Ok(v),
        _ => Err(Error::Dictionary),
    }
}
fn required<'a>(
    fields: &'a BTreeMap<String, Value>,
    key: &'static str,
) -> Result<&'a Value, Error> {
    fields.get(key).ok_or(Error::Missing(key))
}
fn string<'a>(fields: &'a BTreeMap<String, Value>, key: &'static str) -> Result<&'a str, Error> {
    match required(fields, key)? {
        Value::String(v) => Ok(v),
        _ => Err(Error::Type(key)),
    }
}
fn tagged(discriminant: &str) -> BTreeMap<String, Value> {
    [("discriminant".into(), Value::String(discriminant.into()))]
        .into_iter()
        .collect()
}
impl HostLocation {
    /// A closed tag set. Only injectedScene reads sceneIdentifier, a required
    /// String that may be empty. Ignore unknown and inactive payload fields.
    pub fn decode(value: &Value) -> Result<Self, Error> {
        let f = fields(value)?;
        match string(f, "discriminant")? {
            "mainScene" => Ok(Self::MainScene),
            "simDisplayScene" => Ok(Self::SimDisplayScene),
            "external" => Ok(Self::External),
            "nsPreview" => Ok(Self::NsPreview),
            "injectedScene" => Ok(Self::InjectedScene {
                scene_identifier: string(f, "sceneIdentifier")?.to_owned(),
            }),
            _ => Err(Error::InvalidDiscriminant),
        }
    }
    pub fn discriminant(&self) -> &'static str {
        match self {
            Self::InjectedScene { .. } => "injectedScene",
            Self::MainScene => "mainScene",
            Self::SimDisplayScene => "simDisplayScene",
            Self::External => "external",
            Self::NsPreview => "nsPreview",
        }
    }
    pub fn to_value(&self) -> Value {
        let mut f = tagged(self.discriminant());
        if let Self::InjectedScene { scene_identifier } = self {
            f.insert(
                "sceneIdentifier".into(),
                Value::String(scene_identifier.clone()),
            );
        }
        Value::Dictionary(f)
    }
}
impl PreviewType {
    /// static reads no hostLocation; hosted requires a valid nested dictionary.
    /// Re-encode only the active payload. Preserve original scene String data.
    pub fn decode(value: &Value) -> Result<Self, Error> {
        let f = fields(value)?;
        match string(f, "discriminant")? {
            "static" => Ok(Self::Static),
            "hosted" => HostLocation::decode(required(f, "hostLocation")?)
                .map(Self::Hosted)
                .map_err(|e| Error::HostLocation(Box::new(e))),
            _ => Err(Error::InvalidDiscriminant),
        }
    }
    pub fn discriminant(&self) -> &'static str {
        match self {
            Self::Static => "static",
            Self::Hosted(_) => "hosted",
        }
    }
    pub fn to_value(&self) -> Value {
        let mut f = tagged(self.discriminant());
        if let Self::Hosted(location) = self {
            f.insert("hostLocation".into(), location.to_value());
        }
        Value::Dictionary(f)
    }
}
