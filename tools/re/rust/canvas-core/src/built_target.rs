//! Complete built-target wire record for the qualified framework build.
//! No linking, architecture selection, reuse, file access or target execution.
use crate::{
    built_artifact::{
        self, BuiltObjectFileDescription, BuiltStaticArchiveDescription, PlatformVersion,
    },
    jit_load_command::{self, JitLoadCommand},
    payload_codec::Value,
};
use std::collections::{BTreeMap, BTreeSet};
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub enum LinkerFlag {
    AllLoad,
    ObjC,
}
impl LinkerFlag {
    pub fn raw_value(self) -> &'static str {
        match self {
            Self::AllLoad => "allLoad",
            Self::ObjC => "objC",
        }
    }
}
#[derive(Clone, Debug)]
pub struct BuiltTargetDescription {
    pub install_name: String,
    pub is_executable: bool,
    pub buildable_name: Option<String>,
    pub module_name: Option<String>,
    /// Native in-memory field, intentionally absent from the wire schema. Decode
    /// always creates an empty vector; encoding leaves this field unchanged.
    pub merged_module_names: Vec<String>,
    pub platform_version: Option<PlatformVersion>,
    pub object_files: Vec<BuiltObjectFileDescription>,
    pub static_archives: Vec<BuiltStaticArchiveDescription>,
    pub rpaths: Vec<String>,
    pub load_commands: Vec<JitLoadCommand>,
    pub architectures: Vec<String>,
    pub enforce_weak_symbol_paths: bool,
    pub linker_flags: BTreeSet<LinkerFlag>,
    pub opaque_type_erasure_enabled: bool,
    pub output: Option<String>,
    pub diagnostic_info: Vec<String>,
    pub additional_artifact_paths: Vec<String>,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Dictionary,
    Missing(&'static str),
    Type(&'static str),
    StringElement {
        field: &'static str,
        index: usize,
    },
    InvalidLinkerFlag(usize),
    Artifact {
        field: &'static str,
        index: Option<usize>,
        error: built_artifact::Error,
    },
    LoadCommand {
        index: usize,
        error: jit_load_command::Error,
    },
}
fn string(f: &BTreeMap<String, Value>, key: &'static str) -> Result<String, Error> {
    match f.get(key).ok_or(Error::Missing(key))? {
        Value::String(s) => Ok(s.clone()),
        _ => Err(Error::Type(key)),
    }
}
fn optional_string(
    f: &BTreeMap<String, Value>,
    key: &'static str,
) -> Result<Option<String>, Error> {
    f.get(key).map(|_| string(f, key)).transpose()
}
fn array<'a>(f: &'a BTreeMap<String, Value>, key: &'static str) -> Result<&'a [Value], Error> {
    match f.get(key) {
        None => Ok(&[]),
        Some(Value::Array(v)) => Ok(v),
        _ => Err(Error::Type(key)),
    }
}
fn strings(f: &BTreeMap<String, Value>, key: &'static str) -> Result<Vec<String>, Error> {
    array(f, key)?
        .iter()
        .enumerate()
        .map(|(i, v)| match v {
            Value::String(s) => Ok(s.clone()),
            _ => Err(Error::StringElement {
                field: key,
                index: i,
            }),
        })
        .collect()
}
fn boolean(f: &BTreeMap<String, Value>, key: &'static str, default: bool) -> Result<bool, Error> {
    match f.get(key) {
        None => Ok(default),
        Some(Value::Boolean(b)) => Ok(*b),
        Some(Value::Integer(0)) | Some(Value::Unsigned(0)) => Ok(false),
        Some(Value::Integer(1)) | Some(Value::Unsigned(1)) => Ok(true),
        Some(Value::Real(n)) if *n == 0.0 => Ok(false),
        Some(Value::Real(n)) if *n == 1.0 => Ok(true),
        _ => Err(Error::Type(key)),
    }
}
fn put_array(f: &mut BTreeMap<String, Value>, key: &str, values: Vec<Value>) {
    if !values.is_empty() {
        f.insert(key.into(), Value::Array(values));
    }
}
impl BuiltTargetDescription {
    pub fn new(install_name: impl Into<String>) -> Self {
        Self {
            install_name: install_name.into(),
            is_executable: false,
            buildable_name: None,
            module_name: None,
            merged_module_names: vec![],
            platform_version: None,
            object_files: vec![],
            static_archives: vec![],
            rpaths: vec![],
            load_commands: vec![],
            architectures: vec![],
            enforce_weak_symbol_paths: false,
            linker_flags: BTreeSet::new(),
            opaque_type_erasure_enabled: true,
            output: None,
            diagnostic_info: vec![],
            additional_artifact_paths: vec![],
        }
    }
    /// Missing optional arrays/sets become empty; present malformed members fail.
    /// Unknown keys (including mergedModuleNames) are ignored. Arrays preserve
    /// order/duplicates; linker flags are a closed set with original sorted output.
    pub fn decode(value: &Value) -> Result<Self, Error> {
        let Value::Dictionary(f) = value else {
            return Err(Error::Dictionary);
        };
        let mut target = Self::new(string(f, "installName")?);
        target.is_executable = boolean(f, "isExecutable", false)?;
        target.buildable_name = optional_string(f, "buildableName")?;
        target.module_name = optional_string(f, "moduleName")?;
        target.platform_version = f
            .get("platformVersion")
            .map(|v| {
                PlatformVersion::decode(v).map_err(|error| Error::Artifact {
                    field: "platformVersion",
                    index: None,
                    error,
                })
            })
            .transpose()?;
        target.object_files = array(f, "objectFiles")?
            .iter()
            .enumerate()
            .map(|(i, v)| {
                BuiltObjectFileDescription::decode(v).map_err(|error| Error::Artifact {
                    field: "objectFiles",
                    index: Some(i),
                    error,
                })
            })
            .collect::<Result<_, _>>()?;
        target.static_archives = array(f, "staticArchives")?
            .iter()
            .enumerate()
            .map(|(i, v)| {
                BuiltStaticArchiveDescription::decode(v).map_err(|error| Error::Artifact {
                    field: "staticArchives",
                    index: Some(i),
                    error,
                })
            })
            .collect::<Result<_, _>>()?;
        target.rpaths = strings(f, "rpaths")?;
        target.load_commands = array(f, "loadCommands")?
            .iter()
            .enumerate()
            .map(|(index, v)| {
                JitLoadCommand::decode(v).map_err(|error| Error::LoadCommand { index, error })
            })
            .collect::<Result<_, _>>()?;
        target.enforce_weak_symbol_paths = boolean(f, "enforceWeakSymbolPaths", false)?;
        target.architectures = strings(f, "architectures")?;
        target.linker_flags = array(f, "linkerFlags")?
            .iter()
            .enumerate()
            .map(|(i, v)| match v {
                Value::String(s) if s == "allLoad" => Ok(LinkerFlag::AllLoad),
                Value::String(s) if s == "objC" => Ok(LinkerFlag::ObjC),
                _ => Err(Error::InvalidLinkerFlag(i)),
            })
            .collect::<Result<_, _>>()?;
        target.opaque_type_erasure_enabled = boolean(f, "opaqueTypeErasureEnabled", true)?;
        target.output = optional_string(f, "output")?;
        target.diagnostic_info = strings(f, "diagnosticInfo")?;
        target.additional_artifact_paths = strings(f, "additionalArtifactPaths")?;
        Ok(target)
    }
    pub fn to_value(&self) -> Value {
        let mut f = BTreeMap::from([(
            "installName".into(),
            Value::String(self.install_name.clone()),
        )]);
        for (key, value) in [
            ("buildableName", &self.buildable_name),
            ("moduleName", &self.module_name),
            ("output", &self.output),
        ] {
            if let Some(value) = value {
                f.insert(key.into(), Value::String(value.clone()));
            }
        }
        for (key, value, default) in [
            ("isExecutable", self.is_executable, false),
            (
                "enforceWeakSymbolPaths",
                self.enforce_weak_symbol_paths,
                false,
            ),
            (
                "opaqueTypeErasureEnabled",
                self.opaque_type_erasure_enabled,
                true,
            ),
        ] {
            if value != default {
                f.insert(key.into(), Value::Boolean(value));
            }
        }
        if let Some(value) = &self.platform_version {
            f.insert("platformVersion".into(), value.to_value());
        }
        put_array(
            &mut f,
            "objectFiles",
            self.object_files
                .iter()
                .map(BuiltObjectFileDescription::to_value)
                .collect(),
        );
        put_array(
            &mut f,
            "staticArchives",
            self.static_archives
                .iter()
                .map(BuiltStaticArchiveDescription::to_value)
                .collect(),
        );
        put_array(
            &mut f,
            "loadCommands",
            self.load_commands
                .iter()
                .map(JitLoadCommand::to_value)
                .collect(),
        );
        for (key, values) in [
            ("rpaths", &self.rpaths),
            ("architectures", &self.architectures),
            ("diagnosticInfo", &self.diagnostic_info),
            ("additionalArtifactPaths", &self.additional_artifact_paths),
        ] {
            put_array(
                &mut f,
                key,
                values.iter().cloned().map(Value::String).collect(),
            );
        }
        put_array(
            &mut f,
            "linkerFlags",
            self.linker_flags
                .iter()
                .map(|flag| Value::String(flag.raw_value().into()))
                .collect(),
        );
        Value::Dictionary(f)
    }
}
