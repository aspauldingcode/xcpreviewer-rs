//! Variant/override request values. Content category and override names are open
//! String wrappers, not a closed enum or a capability/permission check.
use crate::payload_codec::Value;
use std::collections::BTreeMap;
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RequestPreviewVariantsPayload {
    pub content_category: String,
    pub content_override: Option<String>,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RequestContentOverridePayload {
    pub content_category: String,
    /// Preserve encounter order and duplicates; empty is distinct from missing.
    pub requested_overrides: Vec<String>,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Missing(&'static str),
    Type(&'static str),
    Element { key: &'static str, index: usize },
}
fn text(fields: &BTreeMap<String, Value>, key: &'static str) -> Result<String, Error> {
    match fields.get(key) {
        None => Err(Error::Missing(key)),
        Some(Value::String(value)) => Ok(value.clone()),
        _ => Err(Error::Type(key)),
    }
}
impl RequestPreviewVariantsPayload {
    pub fn decode_dictionary(fields: &BTreeMap<String, Value>) -> Result<Self, Error> {
        let content_category = text(fields, "contentCategory")?;
        let content_override = fields
            .get("contentOverride")
            .map(|_| text(fields, "contentOverride"))
            .transpose()?;
        Ok(Self {
            content_category,
            content_override,
        })
    }
    pub fn to_dictionary(&self) -> BTreeMap<String, Value> {
        let mut fields = BTreeMap::from([(
            "contentCategory".into(),
            Value::String(self.content_category.clone()),
        )]);
        if let Some(value) = &self.content_override {
            fields.insert("contentOverride".into(), Value::String(value.clone()));
        }
        fields
    }
}
impl RequestContentOverridePayload {
    pub fn decode_dictionary(fields: &BTreeMap<String, Value>) -> Result<Self, Error> {
        let content_category = text(fields, "contentCategory")?;
        let values = fields
            .get("requestedOverrides")
            .ok_or(Error::Missing("requestedOverrides"))?;
        let Value::Array(values) = values else {
            return Err(Error::Type("requestedOverrides"));
        };
        let requested_overrides = values
            .iter()
            .enumerate()
            .map(|(index, value)| match value {
                Value::String(value) => Ok(value.clone()),
                _ => Err(Error::Element {
                    key: "requestedOverrides",
                    index,
                }),
            })
            .collect::<Result<_, _>>()?;
        Ok(Self {
            content_category,
            requested_overrides,
        })
    }
    pub fn to_dictionary(&self) -> BTreeMap<String, Value> {
        BTreeMap::from([
            (
                "contentCategory".into(),
                Value::String(self.content_category.clone()),
            ),
            (
                "requestedOverrides".into(),
                Value::Array(
                    self.requested_overrides
                        .iter()
                        .cloned()
                        .map(Value::String)
                        .collect(),
                ),
            ),
        ])
    }
}

/// Identity of a DestinationCapabilitiesCache content-override request.
/// Category and each ordered override ID use qualified Swift canonical Unicode
/// equality. Order, duplicate multiplicity, emptiness and case remain significant.
/// Hash values are Rust-local; native hash bits/cache scheduling are not reproduced.
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct ContentOverrideCacheKey {
    content_category: String,
    requested_overrides: Vec<String>,
}
impl RequestContentOverridePayload {
    /// Build an immutable normalized key without changing wire spellings/order.
    pub fn cache_key(&self) -> ContentOverrideCacheKey {
        use unicode_normalization::UnicodeNormalization;
        ContentOverrideCacheKey {
            content_category: self.content_category.nfd().collect(),
            requested_overrides: self
                .requested_overrides
                .iter()
                .map(|id| id.nfd().collect())
                .collect(),
        }
    }
}
