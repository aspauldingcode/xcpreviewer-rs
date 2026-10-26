//! Static product wire record only. No linking, installation or reuse decision.
use crate::{
    built_target::{self, BuiltTargetDescription},
    payload_codec::Value,
    product_value::{self, PreviewProductIdentity, PreviewProductSeed},
};
use std::collections::BTreeMap;
#[derive(Clone, Debug, Default)]
pub struct StaticLinkablePreviewProduct {
    pub product_identity: Option<PreviewProductIdentity>,
    pub seed: Option<PreviewProductSeed>,
    pub built_target_descriptions: Vec<BuiltTargetDescription>,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Dictionary,
    Type(&'static str),
    Identity(product_value::Error),
    Seed(product_value::Error),
    Target {
        index: usize,
        error: built_target::Error,
    },
}
impl StaticLinkablePreviewProduct {
    /// All fields optional on wire. Missing target array becomes empty; present
    /// malformed values/elements propagate errors. Preserve array order/duplicates.
    pub fn decode(value: &Value) -> Result<Self, Error> {
        let Value::Dictionary(f) = value else {
            return Err(Error::Dictionary);
        };
        let product_identity = f
            .get("productIdentity")
            .map(|v| PreviewProductIdentity::decode(v).map_err(Error::Identity))
            .transpose()?;
        let seed = f
            .get("seed")
            .map(|v| PreviewProductSeed::decode(v).map_err(Error::Seed))
            .transpose()?;
        let built_target_descriptions = match f.get("builtTargetDescriptions") {
            None => vec![],
            Some(Value::Array(values)) => values
                .iter()
                .enumerate()
                .map(|(index, v)| {
                    BuiltTargetDescription::decode(v)
                        .map_err(|error| Error::Target { index, error })
                })
                .collect::<Result<_, _>>()?,
            _ => return Err(Error::Type("builtTargetDescriptions")),
        };
        Ok(Self {
            product_identity,
            seed,
            built_target_descriptions,
        })
    }
    pub fn to_value(&self) -> Value {
        let mut f = BTreeMap::new();
        if let Some(identity) = &self.product_identity {
            f.insert("productIdentity".into(), identity.to_value());
        }
        if let Some(seed) = &self.seed {
            f.insert("seed".into(), seed.to_value());
        }
        if !self.built_target_descriptions.is_empty() {
            f.insert(
                "builtTargetDescriptions".into(),
                Value::Array(
                    self.built_target_descriptions
                        .iter()
                        .map(BuiltTargetDescription::to_value)
                        .collect(),
                ),
            );
        }
        Value::Dictionary(f)
    }
}
