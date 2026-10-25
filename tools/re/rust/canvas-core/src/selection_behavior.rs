//! Selection behavior values; no variant selection or application.
use crate::{
    multi_select_configuration::{self, MultiSelectConfiguration},
    payload_codec::Value,
    single_select_configuration::{self, SingleSelectConfiguration},
};
use std::collections::BTreeMap;
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum SelectionBehavior {
    SingleSelect(SingleSelectConfiguration),
    MultiSelect(MultiSelectConfiguration),
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Missing(&'static str),
    Type(&'static str),
    InvalidDiscriminant,
    SingleSelect(single_select_configuration::Error),
    MultiSelect(multi_select_configuration::Error),
}
impl SelectionBehavior {
    pub fn decode(value: &Value) -> Result<Self, Error> {
        let fields = match value {
            Value::Dictionary(fields) => fields,
            _ => return Err(Error::Type("dictionary")),
        };
        let tag = match fields.get("discriminant") {
            None => return Err(Error::Missing("discriminant")),
            Some(Value::String(tag)) => tag,
            _ => return Err(Error::Type("discriminant")),
        };
        match tag.as_str() {
            "singleSelect" => SingleSelectConfiguration::decode(
                fields
                    .get("singleSelectConfiguration")
                    .ok_or(Error::Missing("singleSelectConfiguration"))?,
            )
            .map(Self::SingleSelect)
            .map_err(Error::SingleSelect),
            "multiSelect" => MultiSelectConfiguration::decode(
                fields
                    .get("multiSelectConfiguration")
                    .ok_or(Error::Missing("multiSelectConfiguration"))?,
            )
            .map(Self::MultiSelect)
            .map_err(Error::MultiSelect),
            _ => Err(Error::InvalidDiscriminant),
        }
    }
    pub fn discriminant(&self) -> &'static str {
        match self {
            Self::SingleSelect(_) => "singleSelect",
            Self::MultiSelect(_) => "multiSelect",
        }
    }
    pub fn to_value(&self) -> Value {
        let (key, payload) = match self {
            Self::SingleSelect(value) => ("singleSelectConfiguration", value.to_value()),
            Self::MultiSelect(value) => ("multiSelectConfiguration", value.to_value()),
        };
        Value::Dictionary(BTreeMap::from([
            (
                "discriminant".into(),
                Value::String(self.discriminant().into()),
            ),
            (key.into(), payload),
        ]))
    }
}
