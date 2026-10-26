//! The controlStates field of ShellUpdatePayload, independently of other fields.
//! This facet does not validate a complete shell update or send/install state.
use crate::{
    canvas_control_state::CanvasControlState,
    hashable_plist_box::HashablePlistBox,
    payload_codec::Value,
    plist_value_box::{decode_boxes, ArrayError, Error as BoxError, PlistValueBox},
};
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Envelope(BoxError),
    States(ArrayError),
}
/// Absence and a present empty ordered array are different wire values.
#[derive(Clone, Debug, Default)]
pub enum ShellControlStates {
    #[default]
    Absent,
    Present(Vec<PlistValueBox>),
}
impl ShellControlStates {
    /// Read only this field. Other envelope members remain opaque. A present
    /// malformed array/element fails; it never falls back to absence. Each box
    /// retains its entire dictionary, without interpreting the `value` member.
    /// Canonically colliding outer keys are a portable profile exclusion.
    pub fn read_from(envelope: &Value) -> Result<Self, Error> {
        PlistValueBox::decode(envelope).map_err(Error::Envelope)?;
        let Value::Dictionary(fields) = envelope else {
            unreachable!()
        };
        fields
            .get("controlStates")
            .map(|v| decode_boxes(v).map(Self::Present).map_err(Error::States))
            .unwrap_or(Ok(Self::Absent))
    }
    /// Match the source-recovered PreviewExecutionPoint.updateBehavior mapping:
    /// read every configured wrapper's original value, retaining source order
    /// and duplicates. Even empty input produces a present array. The native
    /// key-path getter is runtime-qualified; full behavior construction and
    /// downstream updater routing/transport are not executed by this adapter.
    pub fn from_configuration_states(states: &[HashablePlistBox]) -> Self {
        Self::Present(states.iter().map(|b| b.value().clone()).collect())
    }
    /// Apply the same ordered value projection to a Canvas state container.
    /// This does not establish equivalence of the two native owner types.
    pub fn from_canvas_state(state: &CanvasControlState) -> Self {
        Self::from_configuration_states(state.states())
    }
    pub fn boxes(&self) -> Option<&[PlistValueBox]> {
        match self {
            Self::Absent => None,
            Self::Present(boxes) => Some(boxes),
        }
    }
    /// Return an owned envelope with this field installed or removed. Preserve
    /// all other members verbatim; no validation of those members is implied.
    pub fn write_to(&self, envelope: &Value) -> Result<Value, Error> {
        PlistValueBox::decode(envelope).map_err(Error::Envelope)?;
        let Value::Dictionary(mut fields) = envelope.clone() else {
            unreachable!()
        };
        match self {
            Self::Absent => {
                fields.remove("controlStates");
            }
            Self::Present(boxes) => {
                fields.insert(
                    "controlStates".into(),
                    Value::Array(boxes.iter().map(PlistValueBox::to_value).collect()),
                );
            }
        }
        Ok(Value::Dictionary(fields))
    }
}
