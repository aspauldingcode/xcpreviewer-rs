//! Purge request value only. Does not purge state, kill agents, resolve a
//! workspace or establish authority to perform any corresponding native action.
use crate::payload_codec::Value;
use std::collections::BTreeMap;
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PurgePayload {
    pub workspace_id: String,
    pub kill_agents: bool,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Error {
    Missing(&'static str),
    Type(&'static str),
}
impl PurgePayload {
    /// Missing killAgents defaults false; a present invalid value still rejects.
    pub fn decode_dictionary(fields: &BTreeMap<String, Value>) -> Result<Self, Error> {
        let Value::String(workspace_id) = fields
            .get("workspaceID")
            .ok_or(Error::Missing("workspaceID"))?
        else {
            return Err(Error::Type("workspaceID"));
        };
        let kill_agents = match fields.get("killAgents") {
            None => false,
            Some(value) => {
                crate::service_envelope::primitive_bool(value).ok_or(Error::Type("killAgents"))?
            }
        };
        Ok(Self {
            workspace_id: workspace_id.clone(),
            kill_agents,
        })
    }
    /// Canonical output includes an explicit false even when input omitted it.
    pub fn to_dictionary(&self) -> BTreeMap<String, Value> {
        BTreeMap::from([
            (
                "workspaceID".into(),
                Value::String(self.workspace_id.clone()),
            ),
            ("killAgents".into(), Value::Boolean(self.kill_agents)),
        ])
    }
}
