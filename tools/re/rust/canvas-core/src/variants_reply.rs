//! Grouped variants payload values. No transport correlation, graph resolution or rendering.
use crate::{
    overrides_configuration::{self, PreviewOverridesConfiguration},
    payload_codec::Value,
    variant_id_set::VariantIdSet,
    variants_configuration::{self, PreviewVariantsConfiguration},
};
use std::collections::BTreeMap;
/// Opaque group IDs use the same qualified Unicode equality as variant IDs.
pub type AssociatedGroupIds = VariantIdSet;
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PreviewVariantGroup {
    pub id: String,
    pub associated_group_ids: AssociatedGroupIds,
    pub overrides_configuration: Option<PreviewOverridesConfiguration>,
    pub variants_configuration: Option<PreviewVariantsConfiguration>,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PreviewVariantsPayload {
    pub groups: Vec<PreviewVariantGroup>,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Missing(&'static str),
    Type(&'static str),
    AssociatedId { index: usize },
    Overrides(overrides_configuration::Error),
    Variants(variants_configuration::Error),
    Group { index: usize, cause: Box<Error> },
}
fn fields(v: &Value) -> Result<&BTreeMap<String, Value>, Error> {
    match v {
        Value::Dictionary(f) => Ok(f),
        _ => Err(Error::Type("dictionary")),
    }
}
impl PreviewVariantGroup {
    pub fn decode(v: &Value) -> Result<Self, Error> {
        let f = fields(v)?;
        let id = match f.get("id") {
            None => return Err(Error::Missing("id")),
            Some(Value::String(v)) => v.clone(),
            _ => return Err(Error::Type("id")),
        };
        let mut associated_group_ids = AssociatedGroupIds::new();
        if let Some(v) = f.get("associatedGroupIDsArray") {
            let values = match v {
                Value::Array(v) => v,
                _ => return Err(Error::Type("associatedGroupIDsArray")),
            };
            for (index, v) in values.iter().enumerate() {
                match v {
                    Value::String(id) => {
                        associated_group_ids.insert(id.clone());
                    }
                    _ => return Err(Error::AssociatedId { index }),
                }
            }
        }
        let overrides_configuration = f
            .get("overridesConfiguration")
            .map(PreviewOverridesConfiguration::decode)
            .transpose()
            .map_err(Error::Overrides)?;
        let variants_configuration = f
            .get("variantsConfiguration")
            .map(PreviewVariantsConfiguration::decode)
            .transpose()
            .map_err(Error::Variants)?;
        Ok(Self {
            id,
            associated_group_ids,
            overrides_configuration,
            variants_configuration,
        })
    }
    pub fn to_value(&self) -> Value {
        let mut f = BTreeMap::from([
            ("id".into(), Value::String(self.id.clone())),
            (
                "associatedGroupIDsArray".into(),
                Value::Array(
                    self.associated_group_ids
                        .iter()
                        .map(|id| Value::String(id.into()))
                        .collect(),
                ),
            ),
        ]);
        if let Some(v) = &self.overrides_configuration {
            f.insert("overridesConfiguration".into(), v.to_value());
        }
        if let Some(v) = &self.variants_configuration {
            f.insert("variantsConfiguration".into(), v.to_value());
        }
        Value::Dictionary(f)
    }
}
impl PreviewVariantsPayload {
    pub fn decode(v: &Value) -> Result<Self, Error> {
        let f = fields(v)?;
        let values = match f.get("groups") {
            None => return Err(Error::Missing("groups")),
            Some(Value::Array(v)) => v,
            _ => return Err(Error::Type("groups")),
        };
        let groups = values
            .iter()
            .enumerate()
            .map(|(index, v)| {
                PreviewVariantGroup::decode(v).map_err(|cause| Error::Group {
                    index,
                    cause: Box::new(cause),
                })
            })
            .collect::<Result<_, _>>()?;
        Ok(Self { groups })
    }
    pub fn to_value(&self) -> Value {
        Value::Dictionary(BTreeMap::from([(
            "groups".into(),
            Value::Array(
                self.groups
                    .iter()
                    .map(PreviewVariantGroup::to_value)
                    .collect(),
            ),
        )]))
    }
}
