//! Dynamic product wire description only. This module does not load or execute products.
use crate::payload_codec::Value;
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Location {
    Absolute,
    EmbeddedFrameworks,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum LoadingStrategy {
    Bundle,
    Direct,
    Xojit,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ExternalFunctionBinding {
    Default,
    Immediate,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct DynamicLoadablePreviewProduct {
    pub path: String,
    pub executable_path: String,
    pub location: Location,
    pub loading_strategy: LoadingStrategy,
    pub module_name: String,
    pub external_function_binding: ExternalFunctionBinding,
    pub is_required: bool,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Dictionary,
    Missing(&'static str),
    Type(&'static str),
    InvalidValue(&'static str),
}
macro_rules! wire_enum {
 ($t:ident, $($variant:ident => $wire:literal),+ $(,)?) => {
  impl $t {
   pub fn raw_value(self) -> &'static str { match self { $(Self::$variant => $wire),+ } }
   fn decode(value:&Value,key:&'static str)->Result<Self,Error> {
    match value { Value::String(s)=>match s.as_str() { $($wire=>Ok(Self::$variant),)+ _=>Err(Error::InvalidValue(key)) }, _=>Err(Error::Type(key)) }
   }
  }
 };
}
wire_enum!(Location, Absolute=>"absolute", EmbeddedFrameworks=>"embeddedFrameworks");
wire_enum!(LoadingStrategy, Bundle=>"bundle", Direct=>"direct", Xojit=>"xojit");
wire_enum!(ExternalFunctionBinding, Default=>"default", Immediate=>"immediate");
impl DynamicLoadablePreviewProduct {
    /// Missing optional fields default; malformed present fields propagate errors.
    /// Preserve String data; ignore unknown members. No filesystem validation.
    pub fn decode(value: &Value) -> Result<Self, Error> {
        let Value::Dictionary(f) = value else {
            return Err(Error::Dictionary);
        };
        let required = |k: &'static str| f.get(k).ok_or(Error::Missing(k));
        let string = |k: &'static str| match required(k)? {
            Value::String(s) => Ok(s.clone()),
            _ => Err(Error::Type(k)),
        };
        let is_required = match f.get("isRequired") {
            None => true,
            Some(Value::Boolean(b)) => *b,
            Some(Value::Integer(0)) | Some(Value::Unsigned(0)) => false,
            Some(Value::Integer(1)) | Some(Value::Unsigned(1)) => true,
            Some(Value::Real(n)) if *n == 0.0 => false,
            Some(Value::Real(n)) if *n == 1.0 => true,
            Some(_) => return Err(Error::Type("isRequired")),
        };
        Ok(Self {
            path: string("path")?,
            executable_path: string("executablePath")?,
            location: match f.get("location") {
                Some(v) => Location::decode(v, "location")?,
                None => Location::Absolute,
            },
            loading_strategy: LoadingStrategy::decode(
                required("loadingStrategy")?,
                "loadingStrategy",
            )?,
            module_name: string("moduleName")?,
            external_function_binding: ExternalFunctionBinding::decode(
                required("externalFunctionBinding")?,
                "externalFunctionBinding",
            )?,
            is_required,
        })
    }
    pub fn to_value(&self) -> Value {
        Value::Dictionary(
            [
                ("path".into(), Value::String(self.path.clone())),
                (
                    "executablePath".into(),
                    Value::String(self.executable_path.clone()),
                ),
                (
                    "location".into(),
                    Value::String(self.location.raw_value().into()),
                ),
                (
                    "loadingStrategy".into(),
                    Value::String(self.loading_strategy.raw_value().into()),
                ),
                ("moduleName".into(), Value::String(self.module_name.clone())),
                (
                    "externalFunctionBinding".into(),
                    Value::String(self.external_function_binding.raw_value().into()),
                ),
                ("isRequired".into(), Value::Boolean(self.is_required)),
            ]
            .into_iter()
            .collect(),
        )
    }
}
