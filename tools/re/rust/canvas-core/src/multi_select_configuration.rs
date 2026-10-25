//! Multi-select default values; does not choose or apply variants.
use crate::{payload_codec::Value, variant_id_set::VariantIdSet};
use std::collections::BTreeMap;
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct MultiSelectConfiguration {
    pub default_variants: VariantIdSet,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Missing(&'static str),
    Type(&'static str),
    Element { key: &'static str, index: usize },
}
impl MultiSelectConfiguration {
    pub fn decode(value: &Value) -> Result<Self, Error> {
        let fields = match value {
            Value::Dictionary(fields) => fields,
            _ => return Err(Error::Type("dictionary")),
        };
        let values = match fields.get("defaultVariants") {
            None => return Err(Error::Missing("defaultVariants")),
            Some(Value::Array(values)) => values,
            _ => return Err(Error::Type("defaultVariants")),
        };
        let mut default_variants = VariantIdSet::new();
        for (index, value) in values.iter().enumerate() {
            match value {
                Value::String(value) => {
                    default_variants.insert(value.clone());
                }
                _ => {
                    return Err(Error::Element {
                        key: "defaultVariants",
                        index,
                    })
                }
            }
        }
        Ok(Self { default_variants })
    }
    pub fn to_value(&self) -> Value {
        Value::Dictionary(BTreeMap::from([(
            "defaultVariants".into(),
            Value::Array(
                self.default_variants
                    .iter()
                    .map(|id| Value::String(id.into()))
                    .collect(),
            ),
        )]))
    }
}
