//! Source-guided scene seed/timing and partial host-to-shell message parts.
//! A fence token indicates presence only: no wait, signal, transfer or completion
//! is performed. Parts are not an invented native wire/envelope encoding.
use crate::payload_codec::Value;
use std::collections::BTreeMap;
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct SceneUpdateSeed(pub i64);
/// Caller-owned sequence state. The native constructor's process-global plain
/// load/add/store has no atomic operations here; external synchronization/domain
/// ownership remain a separate requirement. No global uniqueness is promised.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct SceneSeedCounter {
    last: SceneUpdateSeed,
}
impl SceneSeedCounter {
    pub fn from_last(last: SceneUpdateSeed) -> Self {
        Self { last }
    }
    pub fn next_seed(&mut self) -> SceneUpdateSeed {
        self.last.0 = self.last.0.wrapping_add(1);
        self.last
    }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum SceneTiming {
    Fenced,
    Async,
}
impl SceneTiming {
    pub fn from_fence_presence(present: bool) -> Self {
        if present {
            Self::Fenced
        } else {
            Self::Async
        }
    }
    pub fn raw(self) -> &'static str {
        match self {
            Self::Fenced => "fenced",
            Self::Async => "async",
        }
    }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum HostSceneMessageKind {
    PreferencesResolved,
    ConfirmReadyForDisplayAfterSceneResize,
    HardwareEvent,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    UnknownMessageType(String),
    UnexpectedFence,
    MissingSeed,
    SeedType,
    UnsupportedHardwareEvent,
    MissingEventData,
    EventDataType,
    InvalidHardwareEvent,
}
impl HostSceneMessageKind {
    pub fn parse(tag: &str) -> Result<Self, Error> {
        match tag {
            "preferencesResolved" => Ok(Self::PreferencesResolved),
            "confirmReadyForDisplayAfterSceneResize" => {
                Ok(Self::ConfirmReadyForDisplayAfterSceneResize)
            }
            "hardwareEvent" => Ok(Self::HardwareEvent),
            s => Err(Error::UnknownMessageType(s.into())),
        }
    }
    pub fn validate_fence(self, present: bool) -> Result<(), Error> {
        if present && self != Self::PreferencesResolved {
            Err(Error::UnexpectedFence)
        } else {
            Ok(())
        }
    }
}
/// Known host-message parts. Event validation is an explicit platform boundary;
/// the default decoder cannot validate CoreGraphics event data. F owns its
/// lifetime/drop policy. No method here posts an event or executes native code.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum HostSceneMessage<F> {
    PreferencesResolved {
        seed: SceneUpdateSeed,
        fence: Option<F>,
    },
    ConfirmReadyForDisplayAfterSceneResize,
    HardwareEvent {
        event_data: Vec<u8>,
    },
}
impl<F> HostSceneMessage<F> {
    pub fn decode_parts(
        tag: &str,
        payload: &BTreeMap<String, Value>,
        fence: Option<F>,
    ) -> Result<Self, Error> {
        let kind = HostSceneMessageKind::parse(tag)?;
        kind.validate_fence(fence.is_some())?;
        match kind {
            HostSceneMessageKind::PreferencesResolved => {
                let seed = match payload.get("seed").ok_or(Error::MissingSeed)? {
                    Value::Integer(n) => SceneUpdateSeed(*n),
                    _ => return Err(Error::SeedType),
                };
                Ok(Self::PreferencesResolved { seed, fence })
            }
            HostSceneMessageKind::ConfirmReadyForDisplayAfterSceneResize => {
                Ok(Self::ConfirmReadyForDisplayAfterSceneResize)
            }
            HostSceneMessageKind::HardwareEvent => Err(Error::UnsupportedHardwareEvent),
        }
    }
    /// Extract the native eventData carrier only after the supplied validator
    /// accepts it. The callback must validate the complete CoreGraphics event;
    /// a successful callback is trusted, not independently established here.
    /// Native validation should run in an isolated bounded worker: malformed
    /// truncated data crashed both observed Apple decoders. A callback failure
    /// must include worker crash/timeout, not just ordinary native rejection.
    /// This does not supply a portable CoreGraphics event decoder or dispatch.
    pub fn decode_parts_with_event_validator(
        tag: &str,
        payload: &BTreeMap<String, Value>,
        fence: Option<F>,
        validate: impl FnOnce(&[u8]) -> bool,
    ) -> Result<Self, Error> {
        let kind = HostSceneMessageKind::parse(tag)?;
        kind.validate_fence(fence.is_some())?;
        if kind != HostSceneMessageKind::HardwareEvent {
            return Self::decode_parts(tag, payload, fence);
        }
        let bytes = match payload.get("eventData").ok_or(Error::MissingEventData)? {
            Value::Data(bytes) => bytes,
            _ => return Err(Error::EventDataType),
        };
        if !validate(bytes) {
            return Err(Error::InvalidHardwareEvent);
        }
        Ok(Self::HardwareEvent {
            event_data: bytes.clone(),
        })
    }
    pub fn timing(&self) -> SceneTiming {
        match self {
            Self::PreferencesResolved { fence, .. } => {
                SceneTiming::from_fence_presence(fence.is_some())
            }
            Self::ConfirmReadyForDisplayAfterSceneResize | Self::HardwareEvent { .. } => {
                SceneTiming::Async
            }
        }
    }
}
