//! Value projection of native UVPreviewSceneAction BSSettings fields.
//! These numbered object slots are not a binary plist envelope or BSXPC/Mach
//! serialization. F is already a caller-validated fence attachment/token.
use crate::payload_codec::Value;
use std::collections::BTreeMap;
pub const MESSAGE_TYPE: i64 = 0;
pub const PAYLOAD: i64 = 1;
pub const FENCE_HANDLE: i64 = 2;

#[derive(Clone, Debug, PartialEq)]
pub enum Setting<F> {
    Value(Value),
    Fence(F),
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    MissingInfo,
    MissingMessageType,
    MessageType,
    Payload,
    FenceHandle,
}
#[derive(Clone, Debug, PartialEq)]
pub struct SceneAction<F> {
    pub message_type: String,
    /// None remains distinct from an explicitly empty native payload object.
    pub payload: Option<BTreeMap<String, Value>>,
    pub fence: Option<F>,
}
/// Native diagnostic slot labels. Unknown indices have no description here.
pub fn setting_name(key: i64) -> Option<&'static str> {
    match key {
        MESSAGE_TYPE => Some("messageType"),
        PAYLOAD => Some("payload"),
        FENCE_HANDLE => Some("fenceHandle"),
        _ => None,
    }
}
impl<F: Clone> SceneAction<F> {
    /// Strict typed-value adapter. Foundation object coercions/Swift errors are
    /// not reproduced. Unknown slots are ignored by these selected getters.
    /// Cloning Value owns a deep value snapshot; native Objective-C object
    /// aliasing/retention is a separate contract, not modeled by this projection.
    pub fn from_settings(info: Option<&BTreeMap<i64, Setting<F>>>) -> Result<Self, Error> {
        let info = info.ok_or(Error::MissingInfo)?;
        let message_type = match info.get(&MESSAGE_TYPE).ok_or(Error::MissingMessageType)? {
            Setting::Value(Value::String(s)) => s.clone(),
            _ => return Err(Error::MessageType),
        };
        let payload = match info.get(&PAYLOAD) {
            None => None,
            Some(Setting::Value(Value::Dictionary(d))) => Some(d.clone()),
            _ => return Err(Error::Payload),
        };
        let fence = match info.get(&FENCE_HANDLE) {
            None => None,
            Some(Setting::Fence(f)) => Some(f.clone()),
            _ => return Err(Error::FenceHandle),
        };
        Ok(Self {
            message_type,
            payload,
            fence,
        })
    }
    pub fn to_settings(&self) -> BTreeMap<i64, Setting<F>> {
        let mut out = BTreeMap::from([(
            MESSAGE_TYPE,
            Setting::Value(Value::String(self.message_type.clone())),
        )]);
        if let Some(p) = &self.payload {
            out.insert(PAYLOAD, Setting::Value(Value::Dictionary(p.clone())));
        }
        if let Some(f) = &self.fence {
            out.insert(FENCE_HANDLE, Setting::Fence(f.clone()));
        }
        out
    }
}
impl<F> SceneAction<F> {
    /// The selected native receiver's missing-payload path supplies an empty
    /// dictionary to its typed message constructor. This does not validate the
    /// message-specific payload, execute a callback or dispatch a hardware event.
    pub fn into_message_parts(self) -> (String, BTreeMap<String, Value>, Option<F>) {
        (
            self.message_type,
            self.payload.unwrap_or_default(),
            self.fence,
        )
    }
}
