//! Modern shell-update service envelope. Value construction sends nothing.
//! The nested shell decoder retains its explicit single-entry update profile.
use crate::{
    binary_plist,
    payload_codec::Value,
    service_envelope::IDENTIFIER_KEY,
    shell_payload::{self, ShellUpdatePayload},
};
use std::collections::BTreeMap;
#[derive(Clone, Debug)]
pub struct ShellServiceEnvelope {
    pub identifier: Option<String>,
    pub shell: ShellUpdatePayload,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Plist(binary_plist::Error),
    Dictionary,
    Missing(&'static str),
    Type(&'static str),
    UnsupportedMessageType,
    Shell(shell_payload::Error),
}
impl ShellServiceEnvelope {
    /// Allocate from the same process-local sequence as other service requests.
    pub fn new(shell: ShellUpdatePayload) -> Self {
        Self {
            identifier: Some(crate::service_identifier::next_service_identifier()),
            shell,
        }
    }
    pub fn decode_single_entry_updates(value: &Value) -> Result<Self, Error> {
        let Value::Dictionary(root) = value else {
            return Err(Error::Dictionary);
        };
        match root
            .get("messageType")
            .ok_or(Error::Missing("messageType"))?
        {
            Value::String(kind) if kind == "update" => {}
            Value::String(_) => return Err(Error::UnsupportedMessageType),
            _ => return Err(Error::Type("messageType")),
        }
        let payload = root.get("payload").ok_or(Error::Missing("payload"))?;
        let Value::Dictionary(fields) = payload else {
            return Err(Error::Type("payload"));
        };
        let identifier = match fields.get(IDENTIFIER_KEY) {
            None => None,
            Some(Value::String(id)) => Some(id.clone()),
            _ => return Err(Error::Type(IDENTIFIER_KEY)),
        };
        let shell =
            ShellUpdatePayload::decode_single_entry_updates(payload).map_err(Error::Shell)?;
        Ok(Self { identifier, shell })
    }
    pub fn decode_binary(bytes: &[u8]) -> Result<Self, Error> {
        Self::decode_single_entry_updates(&binary_plist::decode(bytes).map_err(Error::Plist)?)
    }
    pub fn to_value(&self) -> Value {
        let Value::Dictionary(mut payload) = self.shell.to_value() else {
            unreachable!()
        };
        if let Some(id) = &self.identifier {
            payload.insert(IDENTIFIER_KEY.into(), Value::String(id.clone()));
        }
        Value::Dictionary(BTreeMap::from([
            ("messageType".into(), Value::String("update".into())),
            ("payload".into(), Value::Dictionary(payload)),
        ]))
    }
    pub fn to_binary_plist(&self) -> Result<Vec<u8>, crate::binary_plist_writer::Error> {
        crate::binary_plist_writer::encode_preserving_real_bits(&self.to_value())
    }
}
