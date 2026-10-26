//! Built artifact wire descriptions. No file access, version parsing or loading.
use crate::payload_codec::Value;
use std::collections::BTreeMap;
use unicode_normalization::UnicodeNormalization;
#[derive(Clone, Debug, Default)]
pub struct SourceFilePaths(BTreeMap<String, String>);
impl SourceFilePaths {
    /// Native String-set membership: canonical Unicode duplicates collapse and the
    /// first spelling survives. Original deterministic encoding orders by NFD key;
    /// native randomized Set iteration/wire order is deliberately not reproduced.
    pub fn new(paths: impl IntoIterator<Item = String>) -> Self {
        let mut values = BTreeMap::new();
        for path in paths {
            values.entry(path.nfd().collect()).or_insert(path);
        }
        Self(values)
    }
    pub fn len(&self) -> usize {
        self.0.len()
    }
    pub fn is_empty(&self) -> bool {
        self.0.is_empty()
    }
    pub fn paths(&self) -> impl Iterator<Item = &str> {
        self.0.values().map(String::as_str)
    }
    fn decode(value: &Value) -> Result<Self, Error> {
        let Value::Array(values) = value else {
            return Err(Error::Type("sourceFilePaths"));
        };
        let paths = values
            .iter()
            .enumerate()
            .map(|(i, v)| match v {
                Value::String(s) => Ok(s.clone()),
                _ => Err(Error::SourceFilePath(i)),
            })
            .collect::<Result<Vec<_>, _>>()?;
        Ok(Self::new(paths))
    }
    fn to_value(&self) -> Value {
        Value::Array(self.paths().map(|s| Value::String(s.into())).collect())
    }
}
#[derive(Clone, Debug)]
pub struct BuiltObjectFileDescription {
    pub identifier: Option<String>,
    pub path: String,
    pub source_file_paths: SourceFilePaths,
    pub for_replacement: bool,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct BuiltStaticArchiveDescription {
    pub identifier: Option<String>,
    pub path: String,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PlatformVersion {
    pub name: String,
    pub min_version: String,
    pub sdk_version: String,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Dictionary,
    Missing(&'static str),
    Type(&'static str),
    SourceFilePath(usize),
}
fn fields(value: &Value) -> Result<&BTreeMap<String, Value>, Error> {
    match value {
        Value::Dictionary(f) => Ok(f),
        _ => Err(Error::Dictionary),
    }
}
fn string(f: &BTreeMap<String, Value>, key: &'static str) -> Result<String, Error> {
    match f.get(key).ok_or(Error::Missing(key))? {
        Value::String(s) => Ok(s.clone()),
        _ => Err(Error::Type(key)),
    }
}
fn identifier(f: &BTreeMap<String, Value>) -> Result<Option<String>, Error> {
    f.get("identifier")
        .map(|_| string(f, "identifier"))
        .transpose()
}
fn base(path: &str, id: &Option<String>) -> BTreeMap<String, Value> {
    let mut f = BTreeMap::from([("path".into(), Value::String(path.into()))]);
    if let Some(id) = id {
        f.insert("identifier".into(), Value::String(id.clone()));
    }
    f
}
impl BuiltStaticArchiveDescription {
    pub fn decode(value: &Value) -> Result<Self, Error> {
        let f = fields(value)?;
        Ok(Self {
            identifier: identifier(f)?,
            path: string(f, "path")?,
        })
    }
    pub fn to_value(&self) -> Value {
        Value::Dictionary(base(&self.path, &self.identifier))
    }
}
impl BuiltObjectFileDescription {
    pub fn decode(value: &Value) -> Result<Self, Error> {
        let f = fields(value)?;
        let identifier = identifier(f)?;
        let path = string(f, "path")?;
        let source_file_paths = f
            .get("sourceFilePaths")
            .map(SourceFilePaths::decode)
            .transpose()?
            .unwrap_or_default();
        let for_replacement = match f.get("forReplacement") {
            None => true,
            Some(Value::Boolean(b)) => *b,
            Some(Value::Integer(0)) | Some(Value::Unsigned(0)) => false,
            Some(Value::Integer(1)) | Some(Value::Unsigned(1)) => true,
            Some(Value::Real(n)) if *n == 0.0 => false,
            Some(Value::Real(n)) if *n == 1.0 => true,
            Some(_) => return Err(Error::Type("forReplacement")),
        };
        Ok(Self {
            identifier,
            path,
            source_file_paths,
            for_replacement,
        })
    }
    pub fn to_value(&self) -> Value {
        let mut f = base(&self.path, &self.identifier);
        if !self.source_file_paths.is_empty() {
            f.insert("sourceFilePaths".into(), self.source_file_paths.to_value());
        }
        if !self.for_replacement {
            f.insert("forReplacement".into(), Value::Boolean(false));
        }
        Value::Dictionary(f)
    }
}
impl PlatformVersion {
    pub fn decode(value: &Value) -> Result<Self, Error> {
        let f = fields(value)?;
        Ok(Self {
            name: string(f, "name")?,
            min_version: string(f, "minVersion")?,
            sdk_version: string(f, "sdkVersion")?,
        })
    }
    pub fn to_value(&self) -> Value {
        Value::Dictionary(
            [
                ("name".into(), Value::String(self.name.clone())),
                ("minVersion".into(), Value::String(self.min_version.clone())),
                ("sdkVersion".into(), Value::String(self.sdk_version.clone())),
            ]
            .into_iter()
            .collect(),
        )
    }
}
