//! Command classification recovered from the pinned MessagingHost enum.
//! No capture execution, transport ordering or completion semantics are implied.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum AgentMessageKind {
    PreviewInstances,
    IncrementalPreviewInstances,
    Render,
    IncrementalRender,
    Display,
    IncrementalDisplay,
    LayerHost,
    IncrementalLayerHost,
    CaptureIOSurface,
    IncrementalCaptureIOSurface,
}
impl AgentMessageKind {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::PreviewInstances => "previewInstances",
            Self::IncrementalPreviewInstances => "incrementalPreviewInstances",
            Self::Render => "render",
            Self::IncrementalRender => "incrementalRender",
            Self::Display => "display",
            Self::IncrementalDisplay => "incrementalDisplay",
            Self::LayerHost => "layerHost",
            Self::IncrementalLayerHost => "incrementalLayerHost",
            Self::CaptureIOSurface => "captureIOSurface",
            Self::IncrementalCaptureIOSurface => "incrementalCaptureIOSurface",
        }
    }
    /// Exact case-sensitive strings only; unsupported values remain explicit.
    pub fn from_raw(value: &str) -> Option<Self> {
        Some(match value {
            "previewInstances" => Self::PreviewInstances,
            "incrementalPreviewInstances" => Self::IncrementalPreviewInstances,
            "render" => Self::Render,
            "incrementalRender" => Self::IncrementalRender,
            "display" => Self::Display,
            "incrementalDisplay" => Self::IncrementalDisplay,
            "layerHost" => Self::LayerHost,
            "incrementalLayerHost" => Self::IncrementalLayerHost,
            "captureIOSurface" => Self::CaptureIOSurface,
            "incrementalCaptureIOSurface" => Self::IncrementalCaptureIOSurface,
            _ => return None,
        })
    }
    pub const fn is_incremental(self) -> bool {
        matches!(self, Self::IncrementalPreviewInstances | Self::IncrementalRender
            | Self::IncrementalDisplay | Self::IncrementalLayerHost
            | Self::IncrementalCaptureIOSurface)
    }
    /// Return the incremental member of this pair. Native already-incremental
    /// cases also take a diagnostic path; this API does not reproduce logging.
    pub const fn incremental_variant(self) -> Self {
        match self {
            Self::PreviewInstances | Self::IncrementalPreviewInstances => Self::IncrementalPreviewInstances,
            Self::Render | Self::IncrementalRender => Self::IncrementalRender,
            Self::Display | Self::IncrementalDisplay => Self::IncrementalDisplay,
            Self::LayerHost | Self::IncrementalLayerHost => Self::IncrementalLayerHost,
            Self::CaptureIOSurface | Self::IncrementalCaptureIOSurface => Self::IncrementalCaptureIOSurface,
        }
    }
}

/// Scoped legacy message selection from PlatformPreviewUpdateContext.
/// These values configure subsequent updates; creating this value sends nothing.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct LegacyAgentMessages {
    pub hosted: AgentMessageKind,
    pub static_message: AgentMessageKind,
}
impl Default for LegacyAgentMessages {
    fn default() -> Self {
        Self { hosted: AgentMessageKind::Display, static_message: AgentMessageKind::Render }
    }
}
