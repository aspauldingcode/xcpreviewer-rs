//! Source-guided remote leaf error archive, canonical portable Value profile.
//! Native Swift objects, wrapper archives and Foundation coercions are excluded.
use crate::payload_codec::Value;
use std::collections::BTreeMap;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Severity {
    Error,
    Info,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RemoteErrorLeaf {
    pub error_type_description: String,
    pub high_value_title: Option<String>,
    pub low_value_title: Option<String>,
    pub additional_info: Option<String>,
    pub additional_diagnostics: Option<String>,
    /// Uninterpreted signed option bits; no native option names are invented.
    pub options: Option<i64>,
    pub severity: Option<Severity>,
    pub is_potential_crash: bool,
    pub is_native: bool,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    MissingDiscriminant,
    InvalidDiscriminant,
    UnsupportedWrapper,
    Type(&'static str),
    Severity,
}
fn string(fields: &BTreeMap<String, Value>, key: &'static str) -> Result<Option<String>, Error> {
    match fields.get(key) {
        None => Ok(None),
        Some(Value::String(value)) => Ok(Some(value.clone())),
        _ => Err(Error::Type(key)),
    }
}
fn boolean(
    fields: &BTreeMap<String, Value>,
    key: &'static str,
    default: bool,
) -> Result<bool, Error> {
    match fields.get(key) {
        None => Ok(default),
        Some(Value::Boolean(value)) => Ok(*value),
        _ => Err(Error::Type(key)),
    }
}
impl RemoteErrorLeaf {
    /// Decode only errorType="leaf"; wrapper remains an explicit unsupported
    /// branch. Optional absence is distinct from a present wrong-type/Null value.
    /// Canonical strings/Int64/bools are supported; NSNumber/Any coercion is not.
    /// Unknown keys are ignored. This does not produce native NSError objects or
    /// reproduce full diagnostic formatting, localization, or target settlement.
    pub fn from_dictionary(fields: &BTreeMap<String, Value>) -> Result<Self, Error> {
        match fields.get("errorType") {
            None => return Err(Error::MissingDiscriminant),
            Some(Value::String(kind)) if kind == "leaf" => (),
            Some(Value::String(kind)) if kind == "wrapper" => {
                return Err(Error::UnsupportedWrapper)
            }
            _ => return Err(Error::InvalidDiscriminant),
        }
        let title = match string(fields, "errorTypeDescription")? {
            None => "[Remote] Unknown Error".into(),
            Some(title) if title.starts_with("[Remote] ") => title,
            Some(title) => format!("[Remote] {title}"),
        };
        let high_value_title = string(fields, "highValueTitle")?;
        let low_value_title = string(fields, "lowValueTitle")?;
        let additional_info = string(fields, "additionalInfo")?;
        let additional_diagnostics = string(fields, "additionalDiagnostics")?;
        let options = match fields.get("options") {
            None => None,
            Some(Value::Integer(bits)) => Some(*bits),
            _ => return Err(Error::Type("options")),
        };
        let severity = match string(fields, "severity")?.as_deref() {
            None => None,
            Some("error") => Some(Severity::Error),
            Some("info") => Some(Severity::Info),
            Some(_) => return Err(Error::Severity),
        };
        Ok(Self {
            error_type_description: title,
            high_value_title,
            low_value_title,
            additional_info,
            additional_diagnostics,
            options,
            severity,
            is_potential_crash: boolean(fields, "isPotentialCrash", true)?,
            is_native: boolean(fields, "isNative", false)?,
        })
    }
    /// Encode the leaf tag and concrete flags; omit absent optional values.
    /// Encoding preserves this struct's title; normalization occurs at decode.
    /// Ignored unknown input keys are not re-emitted. Option bits stay signed.
    pub fn to_dictionary(&self) -> BTreeMap<String, Value> {
        let mut fields = BTreeMap::from([
            ("errorType".into(), Value::String("leaf".into())),
            (
                "errorTypeDescription".into(),
                Value::String(self.error_type_description.clone()),
            ),
            (
                "isPotentialCrash".into(),
                Value::Boolean(self.is_potential_crash),
            ),
            ("isNative".into(), Value::Boolean(self.is_native)),
        ]);
        for (key, value) in [
            ("highValueTitle", &self.high_value_title),
            ("lowValueTitle", &self.low_value_title),
            ("additionalInfo", &self.additional_info),
            ("additionalDiagnostics", &self.additional_diagnostics),
        ] {
            if let Some(value) = value {
                fields.insert(key.into(), Value::String(value.clone()));
            }
        }
        if let Some(bits) = self.options {
            fields.insert("options".into(), Value::Integer(bits));
        }
        if let Some(severity) = self.severity {
            fields.insert(
                "severity".into(),
                Value::String(
                    match severity {
                        Severity::Error => "error",
                        Severity::Info => "info",
                    }
                    .into(),
                ),
            );
        }
        fields
    }
}
