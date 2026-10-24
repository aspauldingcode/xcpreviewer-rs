//! Scoped macOS static capture routing recovered from DeveloperTools.
//! This does not open a connection, own a surface, or establish frame freshness.
use crate::{agent_message_kind::AgentMessageKind, iosurface_payload, payload_codec::Value};
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum MacOSStaticRenderingMethod {
    LayerHost,
    IOSurface,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    /// Remote layer-host rendering is not implemented by this portable decoder.
    UnsupportedLayerHost,
    Surface(iosurface_payload::Error),
}
impl MacOSStaticRenderingMethod {
    pub const fn request_kind(self) -> AgentMessageKind {
        match self {
            Self::LayerHost => AgentMessageKind::LayerHost,
            Self::IOSurface => AgentMessageKind::CaptureIOSurface,
        }
    }
    /// Decode the scoped surface route; never silently reinterpret layer data.
    /// Existing surface decoder bounds/type errors are original portable policy.
    pub fn decode_surface_reply(self, value: &Value) -> Result<iosurface_payload::IOSurfacePayload, Error> {
        match self {
            Self::LayerHost => Err(Error::UnsupportedLayerHost),
            Self::IOSurface => iosurface_payload::IOSurfacePayload::decode(value).map_err(Error::Surface),
        }
    }
}
