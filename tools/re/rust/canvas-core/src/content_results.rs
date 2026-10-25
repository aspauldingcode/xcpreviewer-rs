//! Individual variant entries and selected-override replies. Group/configuration
//! decoding, reply correlation and applying render effects remain separate.
use crate::{forward_payload::PreviewOrientation, payload_codec::Value};
use std::collections::BTreeMap;
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RenderEffect {
    pub id: String,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PreviewVariant {
    pub id: String,
    pub display_name: String,
    pub render_effects: Vec<RenderEffect>,
    pub interface_orientation_override: Option<PreviewOrientation>,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ContentOverridePayload {
    pub content_override: Option<String>,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Missing(&'static str),
    Type(&'static str),
    Element { key: &'static str, index: usize },
    InvalidOrientation,
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
impl RenderEffect {
    pub fn decode(value: &Value) -> Result<Self, Error> {
        Ok(Self {
            id: text(fields(value)?, "id")?,
        })
    }
    pub fn to_value(&self) -> Value {
        Value::Dictionary(BTreeMap::from([(
            "id".into(),
            Value::String(self.id.clone()),
        )]))
    }
}
impl PreviewVariant {
    pub fn decode(value: &Value) -> Result<Self, Error> {
        let fields = fields(value)?;
        // Native compatibility checks this optional array first. Only absence
        // retries the required legacy single effect; malformed present rejects.
        let render_effects = match fields.get("renderEffects") {
            Some(Value::Array(values)) => values
                .iter()
                .enumerate()
                .map(|(index, value)| {
                    RenderEffect::decode(value).map_err(|_| Error::Element {
                        key: "renderEffects",
                        index,
                    })
                })
                .collect::<Result<_, _>>()?,
            Some(_) => return Err(Error::Type("renderEffects")),
            None => vec![RenderEffect::decode(
                fields
                    .get("renderEffect")
                    .ok_or(Error::Missing("renderEffect"))?,
            )?],
        };
        let id = text(fields, "id")?;
        let display_name = text(fields, "displayName")?;
        let interface_orientation_override = fields
            .get("interfaceOrientationOverride")
            .map(|_| {
                let raw = text(fields, "interfaceOrientationOverride")?;
                PreviewOrientation::from_raw(&raw).ok_or(Error::InvalidOrientation)
            })
            .transpose()?;
        Ok(Self {
            id,
            display_name,
            render_effects,
            interface_orientation_override,
        })
    }
    /// Modern array plus legacy first effect. Native empty-array compatibility
    /// output uses the literal effect ID "Missing"; this is not a real effect.
    pub fn to_value(&self) -> Value {
        let legacy = self
            .render_effects
            .first()
            .cloned()
            .unwrap_or_else(|| RenderEffect {
                id: "Missing".into(),
            });
        let mut fields = BTreeMap::from([
            ("id".into(), Value::String(self.id.clone())),
            (
                "displayName".into(),
                Value::String(self.display_name.clone()),
            ),
            (
                "renderEffects".into(),
                Value::Array(
                    self.render_effects
                        .iter()
                        .map(RenderEffect::to_value)
                        .collect(),
                ),
            ),
            ("renderEffect".into(), legacy.to_value()),
        ]);
        if let Some(value) = self.interface_orientation_override {
            fields.insert(
                "interfaceOrientationOverride".into(),
                Value::String(value.as_str().into()),
            );
        }
        Value::Dictionary(fields)
    }
}
impl ContentOverridePayload {
    pub fn decode(value: &Value) -> Result<Self, Error> {
        let fields = fields(value)?;
        let content_override = fields
            .get("contentOverride")
            .map(|_| text(fields, "contentOverride"))
            .transpose()?;
        Ok(Self { content_override })
    }
    pub fn to_value(&self) -> Value {
        Value::Dictionary(
            self.content_override
                .as_ref()
                .map_or_else(BTreeMap::new, |value| {
                    BTreeMap::from([("contentOverride".into(), Value::String(value.clone()))])
                }),
        )
    }
}
