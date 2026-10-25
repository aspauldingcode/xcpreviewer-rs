//! Prepare-to-relaunch request values only; decoding does not prepare an agent.
use crate::{
    agent_descriptor::{AgentDescriptor, Error},
    payload_codec::Value,
};
use std::collections::BTreeMap;
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PrepareToRelaunchPayload {
    pub agent_descriptor: AgentDescriptor,
}
impl PrepareToRelaunchPayload {
    /// Retry agentIdentifier after any agentDescriptor decoding failure. Final
    /// portable error describes the fallback; native NSError identity excluded.
    pub fn decode_dictionary(fields: &BTreeMap<String, Value>) -> Result<Self, Error> {
        let decode = |key| AgentDescriptor::decode(fields.get(key).ok_or(Error::Missing(key))?);
        let agent_descriptor = decode("agentDescriptor").or_else(|_| decode("agentIdentifier"))?;
        Ok(Self { agent_descriptor })
    }
    pub fn to_dictionary(&self) -> BTreeMap<String, Value> {
        BTreeMap::from([
            ("agentDescriptor".into(), self.agent_descriptor.to_value()),
            // Legacy representation is only the bundle, not the full descriptor.
            (
                "agentIdentifier".into(),
                self.agent_descriptor.bundle.to_value(),
            ),
        ])
    }
}
