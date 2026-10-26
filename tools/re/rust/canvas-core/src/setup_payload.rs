//! Setup wire values with an explicit single-entry incremental-update restriction.
//! No loading, update application, registry or transport execution.
use crate::{
    dynamic_product::{self, DynamicLoadablePreviewProduct},
    incremental_update::{self, PreviewIncrementalUpdate},
    payload_codec::Value,
    static_product::{self, StaticLinkablePreviewProduct},
};
#[derive(Clone, Debug, Default)]
pub struct UpdateSetupPayload {
    pub dynamic_products: Vec<DynamicLoadablePreviewProduct>,
    pub shell_did_load_static_products: bool,
    pub updates: Vec<PreviewIncrementalUpdate>,
    pub logging_output_path: Option<String>,
    pub static_products: Vec<StaticLinkablePreviewProduct>,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Dictionary,
    Missing(&'static str),
    Type(&'static str),
    DynamicProduct {
        index: usize,
        error: dynamic_product::Error,
    },
    StaticProduct {
        index: usize,
        error: static_product::Error,
    },
    Update {
        index: usize,
        error: incremental_update::Error,
    },
}
impl UpdateSetupPayload {
    /// products and updates required; staticProducts defaults empty. A missing
    /// shellDidLoadStaticProducts defaults to whether staticProducts is nonempty.
    /// Present malformed optional values fail. Incremental multi-key ambiguity
    /// propagates as a portable restriction, not a native schema rejection.
    pub fn decode_single_entry_updates(value: &Value) -> Result<Self, Error> {
        let Value::Dictionary(f) = value else {
            return Err(Error::Dictionary);
        };
        let array = |k: &'static str, required: bool| -> Result<&[Value], Error> {
            match f.get(k) {
                Some(Value::Array(a)) => Ok(a),
                Some(_) => Err(Error::Type(k)),
                None if required => Err(Error::Missing(k)),
                None => Ok(&[]),
            }
        };
        let static_products = array("staticProducts", false)?
            .iter()
            .enumerate()
            .map(|(index, v)| {
                StaticLinkablePreviewProduct::decode(v)
                    .map_err(|error| Error::StaticProduct { index, error })
            })
            .collect::<Result<Vec<_>, _>>()?;
        let dynamic_products = array("products", true)?
            .iter()
            .enumerate()
            .map(|(index, v)| {
                DynamicLoadablePreviewProduct::decode(v)
                    .map_err(|error| Error::DynamicProduct { index, error })
            })
            .collect::<Result<Vec<_>, _>>()?;
        let shell_did_load_static_products = match f.get("shellDidLoadStaticProducts") {
            None => !static_products.is_empty(),
            Some(Value::Boolean(b)) => *b,
            Some(Value::Integer(0)) | Some(Value::Unsigned(0)) => false,
            Some(Value::Integer(1)) | Some(Value::Unsigned(1)) => true,
            Some(Value::Real(n)) if *n == 0.0 => false,
            Some(Value::Real(n)) if *n == 1.0 => true,
            _ => return Err(Error::Type("shellDidLoadStaticProducts")),
        };
        let updates = array("updates", true)?
            .iter()
            .enumerate()
            .map(|(index, v)| {
                PreviewIncrementalUpdate::decode_single_entry(v)
                    .map_err(|error| Error::Update { index, error })
            })
            .collect::<Result<Vec<_>, _>>()?;
        let logging_output_path = match f.get("loggingOutputPath") {
            None => None,
            Some(Value::String(s)) => Some(s.clone()),
            _ => return Err(Error::Type("loggingOutputPath")),
        };
        Ok(Self {
            dynamic_products,
            shell_did_load_static_products,
            updates,
            logging_output_path,
            static_products,
        })
    }
    pub fn to_value(&self) -> Value {
        let mut f = std::collections::BTreeMap::from([
            (
                "products".into(),
                Value::Array(
                    self.dynamic_products
                        .iter()
                        .map(DynamicLoadablePreviewProduct::to_value)
                        .collect(),
                ),
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
            (
                "updates".into(),
                Value::Array(
                    self.updates
                        .iter()
                        .map(PreviewIncrementalUpdate::to_value)
                        .collect(),
                ),
            ),
            (
                "shellDidLoadStaticProducts".into(),
                Value::Boolean(self.shell_did_load_static_products),
            ),
        ]);
        if let Some(path) = &self.logging_output_path {
            f.insert("loggingOutputPath".into(), Value::String(path.clone()));
        }
        Value::Dictionary(f)
    }
    pub fn to_binary_plist(&self) -> Result<Vec<u8>, crate::binary_plist_writer::Error> {
        crate::binary_plist_writer::encode_preserving_real_bits(&self.to_value())
    }
}
