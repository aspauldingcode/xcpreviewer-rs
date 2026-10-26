//! JIT load-command wire descriptions only. No dylib loading or symbol resolution.
use crate::payload_codec::Value;
use std::collections::BTreeMap;
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Linkage {
    Strong,
    Weak,
}
impl Linkage {
    pub fn raw_value(self) -> &'static str {
        match self {
            Self::Strong => "strong",
            Self::Weak => "weak",
        }
    }
    fn decode(value: &Value) -> Result<Self, Error> {
        match value {
            Value::String(s) => match s.as_str() {
                "strong" => Ok(Self::Strong),
                "weak" => Ok(Self::Weak),
                _ => Err(Error::InvalidLinkage),
            },
            _ => Err(Error::Type("linkage")),
        }
    }
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct LoadDylib {
    pub path: String,
    pub linkage: Linkage,
    pub symbols_path: Option<String>,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum JitLoadCommand {
    LoadDylib(LoadDylib),
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Dictionary,
    Missing(&'static str),
    Type(&'static str),
    InvalidLinkage,
    InvalidDiscriminant,
    Command(Box<Error>),
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
fn string(f: &BTreeMap<String, Value>, key: &'static str) -> Result<String, Error> {
    match required(f, key)? {
        Value::String(s) => Ok(s.clone()),
        _ => Err(Error::Type(key)),
    }
}
impl LoadDylib {
    /// Missing linkage defaults strong. Missing symbolsPath is None; empty String
    /// remains present. Malformed present optionals propagate errors.
    pub fn decode(value: &Value) -> Result<Self, Error> {
        let f = fields(value)?;
        let path = string(f, "path")?;
        let linkage = f
            .get("linkage")
            .map(Linkage::decode)
            .transpose()?
            .unwrap_or(Linkage::Strong);
        let symbols_path = f
            .get("symbolsPath")
            .map(|_| string(f, "symbolsPath"))
            .transpose()?;
        Ok(Self {
            path,
            linkage,
            symbols_path,
        })
    }
    pub fn to_value(&self) -> Value {
        let mut f = BTreeMap::from([
            ("path".into(), Value::String(self.path.clone())),
            (
                "linkage".into(),
                Value::String(self.linkage.raw_value().into()),
            ),
        ]);
        if let Some(path) = &self.symbols_path {
            f.insert("symbolsPath".into(), Value::String(path.clone()));
        }
        Value::Dictionary(f)
    }
}
impl JitLoadCommand {
    /// Closed single-case enum. The required nested wire key is command; it is
    /// distinct from the loadDylib tag. Ignore unknown envelope/nested members.
    pub fn decode(value: &Value) -> Result<Self, Error> {
        let f = fields(value)?;
        if string(f, "discriminant")? != "loadDylib" {
            return Err(Error::InvalidDiscriminant);
        }
        LoadDylib::decode(required(f, "command")?)
            .map(Self::LoadDylib)
            .map_err(|e| Error::Command(Box::new(e)))
    }
    pub fn to_value(&self) -> Value {
        let Self::LoadDylib(command) = self;
        Value::Dictionary(
            [
                ("discriminant".into(), Value::String("loadDylib".into())),
                ("command".into(), command.to_value()),
            ]
            .into_iter()
            .collect(),
        )
    }
}
