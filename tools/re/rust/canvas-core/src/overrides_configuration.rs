//! Recursive override configuration values. No selection, application or rendering.
use crate::{
    content_results::{self, PreviewVariant},
    payload_codec::Value,
    selection_behavior::{self, SelectionBehavior},
};
use std::collections::{btree_map::Entry, BTreeMap};
use unicode_normalization::UnicodeNormalization;
#[derive(Clone, Debug, Default)]
pub struct ChildConfigurations {
    values: BTreeMap<String, (String, PreviewOverridesConfiguration)>,
}
impl ChildConfigurations {
    pub fn new() -> Self {
        Self::default()
    }
    /// Canonical ID lookup; the first key spelling survives value replacement.
    pub fn insert(
        &mut self,
        key: String,
        value: PreviewOverridesConfiguration,
    ) -> Option<PreviewOverridesConfiguration> {
        match self.values.entry(key.nfd().collect()) {
            Entry::Vacant(e) => {
                e.insert((key, value));
                None
            }
            Entry::Occupied(mut e) => Some(std::mem::replace(&mut e.get_mut().1, value)),
        }
    }
    pub fn get(&self, key: &str) -> Option<&PreviewOverridesConfiguration> {
        self.values
            .get(&key.nfd().collect::<String>())
            .map(|v| &v.1)
    }
    pub fn len(&self) -> usize {
        self.values.len()
    }
    pub fn is_empty(&self) -> bool {
        self.values.is_empty()
    }
    pub fn iter(&self) -> impl Iterator<Item = (&str, &PreviewOverridesConfiguration)> {
        self.values.values().map(|(k, v)| (k.as_str(), v))
    }
}
impl PartialEq for ChildConfigurations {
    fn eq(&self, other: &Self) -> bool {
        self.values
            .iter()
            .map(|(k, (_, v))| (k, v))
            .eq(other.values.iter().map(|(k, (_, v))| (k, v)))
    }
}
impl Eq for ChildConfigurations {}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PreviewOverridesConfiguration {
    pub title: String,
    pub selection_behavior: SelectionBehavior,
    pub variants: Vec<PreviewVariant>,
    pub child_variant_configurations: ChildConfigurations,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Missing(&'static str),
    Type(&'static str),
    Selection(selection_behavior::Error),
    Variant {
        index: usize,
        cause: content_results::Error,
    },
    Child {
        index: usize,
        cause: Box<Error>,
    },
    CanonicalKeyCollision,
    Depth,
}
impl PreviewOverridesConfiguration {
    pub fn decode(value: &Value) -> Result<Self, Error> {
        Self::decode_at(value, 0)
    }
    fn decode_at(value: &Value, depth: usize) -> Result<Self, Error> {
        if depth > 64 {
            return Err(Error::Depth);
        }
        let f = match value {
            Value::Dictionary(f) => f,
            _ => return Err(Error::Type("dictionary")),
        };
        let title = match f.get("title") {
            None => return Err(Error::Missing("title")),
            Some(Value::String(v)) => v.clone(),
            _ => return Err(Error::Type("title")),
        };
        let selection_behavior = SelectionBehavior::decode(
            f.get("selectionBehavior")
                .ok_or(Error::Missing("selectionBehavior"))?,
        )
        .map_err(Error::Selection)?;
        let variants = match f.get("variants") {
            None => return Err(Error::Missing("variants")),
            Some(Value::Array(values)) => values
                .iter()
                .enumerate()
                .map(|(index, v)| {
                    PreviewVariant::decode(v).map_err(|cause| Error::Variant { index, cause })
                })
                .collect::<Result<_, _>>()?,
            _ => return Err(Error::Type("variants")),
        };
        let mut children = ChildConfigurations::new();
        if let Some(value) = f.get("childVariantConfigurations") {
            let fields = match value {
                Value::Dictionary(fields) => fields,
                _ => return Err(Error::Type("childVariantConfigurations")),
            };
            // A Swift String-key dictionary cannot represent two canonical-equivalent
            // keys. Refuse ambiguous raw Value input instead of guessing bridge order.
            let mut keys = std::collections::BTreeSet::new();
            for key in fields.keys() {
                if !keys.insert(key.nfd().collect::<String>()) {
                    return Err(Error::CanonicalKeyCollision);
                }
            }
            for (index, (key, value)) in fields.iter().enumerate() {
                let child = Self::decode_at(value, depth + 1).map_err(|cause| Error::Child {
                    index,
                    cause: Box::new(cause),
                })?;
                children.insert(key.clone(), child);
            }
        }
        Ok(Self {
            title,
            selection_behavior,
            variants,
            child_variant_configurations: children,
        })
    }
    pub fn to_value(&self) -> Value {
        Value::Dictionary(BTreeMap::from([
            ("title".into(), Value::String(self.title.clone())),
            (
                "selectionBehavior".into(),
                self.selection_behavior.to_value(),
            ),
            (
                "variants".into(),
                Value::Array(self.variants.iter().map(PreviewVariant::to_value).collect()),
            ),
            (
                "childVariantConfigurations".into(),
                Value::Dictionary(
                    self.child_variant_configurations
                        .iter()
                        .map(|(id, v)| (id.into(), v.to_value()))
                        .collect(),
                ),
            ),
        ]))
    }
}
