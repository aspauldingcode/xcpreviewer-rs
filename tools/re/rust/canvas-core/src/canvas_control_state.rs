//! Ordered CanvasControlState values qualified against shipped Pipeline methods.
//! The adapter's array form is original; no complete native transport schema,
//! request identity, state installation or global resource settlement is claimed.
use crate::{
    hashable_plist_box::{Error as SnapshotError, HashablePlistBox},
    payload_codec::Value,
    plist_value_box::{Error as BoxError, PlistValueBox},
};
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    Array,
    Box { index: usize, cause: BoxError },
    Snapshot { index: usize, cause: SnapshotError },
}
#[derive(Clone, Debug, Default, PartialEq, Eq, Hash)]
pub struct CanvasControlState {
    states: Vec<HashablePlistBox>,
}
impl CanvasControlState {
    pub fn new(states: Vec<HashablePlistBox>) -> Self {
        Self { states }
    }
    pub fn states(&self) -> &[HashablePlistBox] {
        &self.states
    }
    /// Decode every whole box and its qualified snapshot before constructing the
    /// state. Order and duplicates remain significant. An empty array is empty
    /// state; an array containing an empty box is a different nonempty state.
    pub fn decode(value: &Value) -> Result<Self, Error> {
        let Value::Array(values) = value else {
            return Err(Error::Array);
        };
        values
            .iter()
            .enumerate()
            .map(|(index, value)| {
                let b =
                    PlistValueBox::decode(value).map_err(|cause| Error::Box { index, cause })?;
                HashablePlistBox::new(b).map_err(|cause| Error::Snapshot { index, cause })
            })
            .collect::<Result<Vec<_>, _>>()
            .map(Self::new)
    }
    /// Recover each original box value in source order, independently of its
    /// cached equality projection. This does not serialize native container ABI.
    pub fn to_value(&self) -> Value {
        Value::Array(self.states.iter().map(|b| b.value().to_value()).collect())
    }
}
