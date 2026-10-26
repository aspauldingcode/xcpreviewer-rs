//! Qualified PreviewRunnable.Configuration.ID field selection and equality.
//! This is not the outer PreviewConfiguration.ID or a complete request identity.
use crate::{
    canvas_control_state::CanvasControlState, content_results::PreviewVariant,
    payload_codec::Value, request_projection::DisplayMode,
};
use std::hash::{Hash, Hasher};
use unicode_normalization::UnicodeNormalization;
#[derive(Clone, Debug)]
pub struct RunnableConfigurationId {
    display_mode: DisplayMode,
    override_ids: Vec<String>,
    override_keys: Vec<String>,
    control_state: CanvasControlState,
}
impl RunnableConfigurationId {
    /// Copy ordered IDs only; labels, effects and orientation are not ID fields.
    /// Caller-provided variants are already typed/validated. The control-state
    /// values use the qualified Foundation-origin snapshot profile.
    pub fn new(
        display_mode: DisplayMode,
        overrides: &[PreviewVariant],
        control_state: CanvasControlState,
    ) -> Self {
        let override_ids: Vec<_> = overrides.iter().map(|v| v.id.clone()).collect();
        let override_keys = override_ids.iter().map(|id| id.nfd().collect()).collect();
        Self {
            display_mode,
            override_ids,
            override_keys,
            control_state,
        }
    }
    pub fn display_mode(&self) -> DisplayMode {
        self.display_mode
    }
    pub fn override_ids(&self) -> &[String] {
        &self.override_ids
    }
    pub fn control_state(&self) -> &CanvasControlState {
        &self.control_state
    }
    /// Original-tool projection of native ID fields, preserving original String
    /// spellings and box values. It is not a native ID wire serialization.
    pub fn to_value(&self) -> Value {
        let mode = match self.display_mode {
            DisplayMode::Interactive(value) => Value::Dictionary(
                [
                    ("discriminant".into(), Value::String("interactive".into())),
                    ("value".into(), Value::Boolean(value)),
                ]
                .into_iter()
                .collect(),
            ),
            DisplayMode::Static => Value::Dictionary(
                [("discriminant".into(), Value::String("static".into()))]
                    .into_iter()
                    .collect(),
            ),
        };
        Value::Dictionary(
            [
                ("displayMode".into(), mode),
                (
                    "overrideIDs".into(),
                    Value::Array(
                        self.override_ids
                            .iter()
                            .cloned()
                            .map(Value::String)
                            .collect(),
                    ),
                ),
                ("controlState".into(), self.control_state.to_value()),
            ]
            .into_iter()
            .collect(),
        )
    }
}
impl PartialEq for RunnableConfigurationId {
    fn eq(&self, other: &Self) -> bool {
        self.display_mode == other.display_mode
            && self.override_keys == other.override_keys
            && self.control_state == other.control_state
    }
}
impl Eq for RunnableConfigurationId {}
impl Hash for RunnableConfigurationId {
    fn hash<H: Hasher>(&self, state: &mut H) {
        match self.display_mode {
            DisplayMode::Interactive(false) => 0u8,
            DisplayMode::Interactive(true) => 1u8,
            DisplayMode::Static => 2u8,
        }
        .hash(state);
        self.override_keys.hash(state);
        self.control_state.hash(state);
    }
}
