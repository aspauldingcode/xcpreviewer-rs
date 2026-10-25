//! Sectioned variant-configuration values; no grouping, selection or rendering.
use crate::{
    content_results::{self, PreviewVariant},
    payload_codec::Value,
};
use std::collections::BTreeMap;
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PreviewVariantsConfiguration {
    pub title: String,
    pub sections: Vec<Section>,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Section {
    pub title: Option<String>,
    pub variants: Vec<PreviewVariant>,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Missing(&'static str),
    Type(&'static str),
    Section {
        index: usize,
        cause: Box<Error>,
    },
    Variant {
        index: usize,
        cause: content_results::Error,
    },
}
fn fields(value: &Value) -> Result<&BTreeMap<String, Value>, Error> {
    match value {
        Value::Dictionary(fields) => Ok(fields),
        _ => Err(Error::Type("dictionary")),
    }
}
fn text(fields: &BTreeMap<String, Value>, key: &'static str) -> Result<String, Error> {
    match fields.get(key) {
        None => Err(Error::Missing(key)),
        Some(Value::String(value)) => Ok(value.clone()),
        _ => Err(Error::Type(key)),
    }
}
fn array<'a>(fields: &'a BTreeMap<String, Value>, key: &'static str) -> Result<&'a [Value], Error> {
    match fields.get(key) {
        None => Err(Error::Missing(key)),
        Some(Value::Array(values)) => Ok(values),
        _ => Err(Error::Type(key)),
    }
}
impl PreviewVariantsConfiguration {
    pub fn decode(value: &Value) -> Result<Self, Error> {
        let fields = fields(value)?;
        let title = text(fields, "title")?;
        let sections = array(fields, "sections")?
            .iter()
            .enumerate()
            .map(|(index, value)| {
                Section::decode(value).map_err(|cause| Error::Section {
                    index,
                    cause: Box::new(cause),
                })
            })
            .collect::<Result<_, _>>()?;
        Ok(Self { title, sections })
    }
    pub fn to_value(&self) -> Value {
        Value::Dictionary(BTreeMap::from([
            ("title".into(), Value::String(self.title.clone())),
            (
                "sections".into(),
                Value::Array(self.sections.iter().map(Section::to_value).collect()),
            ),
        ]))
    }
}
impl Section {
    pub fn decode(value: &Value) -> Result<Self, Error> {
        let fields = fields(value)?;
        let title = fields
            .get("title")
            .map(|_| text(fields, "title"))
            .transpose()?;
        let variants = array(fields, "variants")?
            .iter()
            .enumerate()
            .map(|(index, value)| {
                PreviewVariant::decode(value).map_err(|cause| Error::Variant { index, cause })
            })
            .collect::<Result<_, _>>()?;
        Ok(Self { title, variants })
    }
    pub fn to_value(&self) -> Value {
        let mut fields = BTreeMap::from([(
            "variants".into(),
            Value::Array(self.variants.iter().map(PreviewVariant::to_value).collect()),
        )]);
        if let Some(title) = &self.title {
            fields.insert("title".into(), Value::String(title.clone()));
        }
        Value::Dictionary(fields)
    }
}
