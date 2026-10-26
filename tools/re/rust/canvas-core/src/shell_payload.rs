//! Complete ShellUpdatePayload fields, with inherited portable profile exclusions.
//! No transport, update execution, native scheduling or resource settlement.
use crate::{
    payload_codec::Value,
    preview_type::{self, PreviewType},
    setup_payload::{self, UpdateSetupPayload},
    shell_control_states::{self, ShellControlStates},
    static_product::{self, StaticLinkablePreviewProduct},
    update_seed::{self, HostUpdateGroupSeed, HostUpdateSeed},
};
use std::collections::BTreeMap;
/// Distinct content roles retain raw Strings. Native identity/equality unqualified.
#[derive(Clone, Debug)]
pub struct ContentIdentifier(pub String);
#[derive(Clone, Debug)]
pub struct ContentCategory(pub String);
#[derive(Clone, Debug)]
pub struct ContentOverride(pub String);
#[derive(Clone, Debug)]
pub struct ShellUpdatePayload {
    pub pid: i32,
    pub host_update_seed: Option<HostUpdateSeed>,
    pub host_update_group_seed: Option<HostUpdateGroupSeed>,
    pub preview_type: PreviewType,
    pub content_identifier: ContentIdentifier,
    pub content_category: ContentCategory,
    pub content_override: Option<ContentOverride>,
    pub content_payload: BTreeMap<String, Value>,
    pub static_products: Vec<StaticLinkablePreviewProduct>,
    pub setup_payload: UpdateSetupPayload,
    pub control_states: ShellControlStates,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Dictionary,
    Missing(&'static str),
    Type(&'static str),
    Pid,
    Seed {
        field: &'static str,
        error: update_seed::Error,
    },
    PreviewType(preview_type::Error),
    StaticProduct {
        index: usize,
        error: static_product::Error,
    },
    Setup(setup_payload::Error),
    Controls(shell_control_states::Error),
}
fn pid(value: &Value) -> Option<i32> {
    match value {
        Value::Integer(v) => i32::try_from(*v).ok(),
        Value::Unsigned(v) => i32::try_from(*v).ok(),
        Value::Boolean(v) => Some(i32::from(*v)),
        Value::Real(v)
            if v.is_finite()
                && v.fract() == 0.0
                && *v >= i32::MIN as f64
                && *v <= i32::MAX as f64 =>
        {
            Some(*v as i32)
        }
        _ => None,
    }
}
impl ShellUpdatePayload {
    /// setupPayload/pid/previewType/contentIdentifier/contentCategory/contentPayload
    /// required. Missing staticProducts is empty; seeds/override/controls absent.
    /// Multi-key incremental updates and canonical control-box key collisions remain
    /// explicit inherited portable exclusions. No simultaneous-invalid error priority.
    pub fn decode_single_entry_updates(value: &Value) -> Result<Self, Error> {
        let Value::Dictionary(f) = value else {
            return Err(Error::Dictionary);
        };
        let required = |key: &'static str| f.get(key).ok_or(Error::Missing(key));
        let text = |key: &'static str| match required(key)? {
            Value::String(v) => Ok(v.clone()),
            _ => Err(Error::Type(key)),
        };
        let setup_payload =
            UpdateSetupPayload::decode_single_entry_updates(required("setupPayload")?)
                .map_err(Error::Setup)?;
        let pid = pid(required("pid")?).ok_or(Error::Pid)?;
        let host_update_seed = f
            .get("hostUpdateSeed")
            .map(|v| {
                HostUpdateSeed::decode(v).map_err(|error| Error::Seed {
                    field: "hostUpdateSeed",
                    error,
                })
            })
            .transpose()?;
        let host_update_group_seed = f
            .get("hostUpdateGroupSeed")
            .map(|v| {
                HostUpdateGroupSeed::decode(v).map_err(|error| Error::Seed {
                    field: "hostUpdateGroupSeed",
                    error,
                })
            })
            .transpose()?;
        let preview_type =
            PreviewType::decode(required("previewType")?).map_err(Error::PreviewType)?;
        let content_identifier = ContentIdentifier(text("contentIdentifier")?);
        let content_category = ContentCategory(text("contentCategory")?);
        let content_override = f
            .get("contentOverride")
            .map(|v| match v {
                Value::String(s) => Ok(ContentOverride(s.clone())),
                _ => Err(Error::Type("contentOverride")),
            })
            .transpose()?;
        let Value::Dictionary(content_payload) = required("contentPayload")? else {
            return Err(Error::Type("contentPayload"));
        };
        let static_products = match f.get("staticProducts") {
            None => vec![],
            Some(Value::Array(values)) => values
                .iter()
                .enumerate()
                .map(|(index, v)| {
                    StaticLinkablePreviewProduct::decode(v)
                        .map_err(|error| Error::StaticProduct { index, error })
                })
                .collect::<Result<Vec<_>, _>>()?,
            _ => return Err(Error::Type("staticProducts")),
        };
        let control_states = ShellControlStates::read_from(value).map_err(Error::Controls)?;
        Ok(Self {
            pid,
            host_update_seed,
            host_update_group_seed,
            preview_type,
            content_identifier,
            content_category,
            content_override,
            content_payload: content_payload.clone(),
            static_products,
            setup_payload,
            control_states,
        })
    }
    pub fn to_value(&self) -> Value {
        let mut f = BTreeMap::from([
            ("pid".into(), Value::Integer(self.pid as i64)),
            ("previewType".into(), self.preview_type.to_value()),
            (
                "contentIdentifier".into(),
                Value::String(self.content_identifier.0.clone()),
            ),
            (
                "contentCategory".into(),
                Value::String(self.content_category.0.clone()),
            ),
            (
                "contentPayload".into(),
                Value::Dictionary(self.content_payload.clone()),
            ),
            (
                "staticProducts".into(),
                Value::Array(
                    self.static_products
                        .iter()
                        .map(StaticLinkablePreviewProduct::to_value)
                        .collect(),
                ),
            ),
            ("setupPayload".into(), self.setup_payload.to_value()),
        ]);
        if let Some(seed) = self.host_update_seed {
            f.insert("hostUpdateSeed".into(), seed.to_value());
        }
        if let Some(seed) = self.host_update_group_seed {
            f.insert("hostUpdateGroupSeed".into(), seed.to_value());
        }
        if let Some(v) = &self.content_override {
            f.insert("contentOverride".into(), Value::String(v.0.clone()));
        }
        self.control_states
            .write_to(&Value::Dictionary(f))
            .expect("fixed shell field keys")
    }
    pub fn to_binary_plist(&self) -> Result<Vec<u8>, crate::binary_plist_writer::Error> {
        crate::binary_plist_writer::encode_preserving_real_bits(&self.to_value())
    }
}
