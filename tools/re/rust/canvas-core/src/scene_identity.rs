//! Selected native FBSSceneIdentity BSXPCCoder value envelope.
//! No scene lookup, service invocation, identity generation or archive decoding.
use crate::settings_xpc::XpcValue;
use std::collections::BTreeMap;
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct SceneIdentity {
    pub identifier: String,
    pub workspace_identifier: Option<String>,
    /// Explicit encoded `iw`; absence is preserved even when its getter falls back.
    pub internal_workspace_identifier: Option<String>,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Envelope,
    Class,
    Identifier,
    Field,
}
impl SceneIdentity {
    pub fn from_xpc(value: &XpcValue) -> Result<Self, Error> {
        use XpcValue::*;
        let Dictionary(d) = value else {
            return Err(Error::Envelope);
        };
        if d.keys()
            .any(|k| !matches!(k.as_str(), "bsx_class" | "i" | "w" | "iw"))
        {
            return Err(Error::Envelope);
        }
        if d.get("bsx_class") != Some(&String("FBSSceneIdentity".into())) {
            return Err(Error::Class);
        }
        let Some(String(identifier)) = d.get("i") else {
            return Err(Error::Identifier);
        };
        let optional = |key| match d.get(key) {
            None => Ok(None),
            Some(String(s)) => Ok(Some(s.clone())),
            _ => Err(Error::Field),
        };
        Ok(Self {
            identifier: identifier.clone(),
            workspace_identifier: optional("w")?,
            internal_workspace_identifier: optional("iw")?,
        })
    }
    pub fn to_xpc(&self) -> XpcValue {
        use XpcValue::*;
        let mut d = BTreeMap::from([
            ("bsx_class".into(), String("FBSSceneIdentity".into())),
            ("i".into(), String(self.identifier.clone())),
        ]);
        if let Some(s) = &self.workspace_identifier {
            d.insert("w".into(), String(s.clone()));
        }
        if let Some(s) = &self.internal_workspace_identifier {
            d.insert("iw".into(), String(s.clone()));
        }
        Dictionary(d)
    }
    /// Measured native getter fallback; does not insert or normalize `iw`.
    pub fn effective_internal_workspace_identifier(&self) -> Option<&str> {
        self.internal_workspace_identifier
            .as_deref()
            .or(self.workspace_identifier.as_deref())
    }
}
