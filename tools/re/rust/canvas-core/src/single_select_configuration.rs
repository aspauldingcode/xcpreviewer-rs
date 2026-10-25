//! Single-select configuration values. Does not choose or apply a variant.
use crate::payload_codec::Value;
use std::collections::BTreeMap;
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Style {
    List,
    Range,
}
impl Style {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::List => "list",
            Self::Range => "range",
        }
    }
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct SingleSelectConfiguration {
    pub style: Style,
    pub default_variant: String,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Missing(&'static str),
    Type(&'static str),
    InvalidStyle,
}
fn text(fields: &BTreeMap<String, Value>, key: &'static str) -> Result<String, Error> {
    match fields.get(key) {
        None => Err(Error::Missing(key)),
        Some(Value::String(value)) => Ok(value.clone()),
        _ => Err(Error::Type(key)),
    }
}
impl SingleSelectConfiguration {
    pub fn decode(value: &Value) -> Result<Self, Error> {
        let fields = match value {
            Value::Dictionary(fields) => fields,
            _ => return Err(Error::Type("dictionary")),
        };
        let style = match text(fields, "style")?.as_str() {
            "list" => Style::List,
            "range" => Style::Range,
            _ => return Err(Error::InvalidStyle),
        };
        let default_variant = text(fields, "defaultVariant")?;
        Ok(Self {
            style,
            default_variant,
        })
    }
    pub fn to_value(&self) -> Value {
        Value::Dictionary(BTreeMap::from([
            ("style".into(), Value::String(self.style.as_str().into())),
            (
                "defaultVariant".into(),
                Value::String(self.default_variant.clone()),
            ),
        ]))
    }
}
