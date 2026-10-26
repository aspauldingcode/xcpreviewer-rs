//! Ordered display/override/variant projections after native request admission.
//! Native identity lookup, stored/default mode resolution, full fields and execution
//! are caller-owned. These types are original projections, not native wire types.
use crate::{
    content_results::PreviewVariant,
    effective_overrides::{
        effective_groups_and_overrides, grid_request_overrides, OverrideSettings,
    },
    variants_reply::PreviewVariantGroup,
};
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum HostLocation {
    InCanvas,
    External,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum CanvasMode<'a> {
    Live(HostLocation),
    Grid(&'a PreviewVariantGroup),
    Static,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Capabilities {
    pub supports_continuous_live_preview: bool,
    pub supports_static_previews: bool,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum DisplayMode {
    /// Preserve the native enum's unnamed Bool payload without assigning it a
    /// broader UI or runtime meaning. Live(inCanvas) and non-live requests use
    /// true; Live(external) uses false.
    Interactive(bool),
    Static,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RequestProjection {
    pub display_mode: DisplayMode,
    pub overrides: Vec<PreviewVariant>,
    pub variant: Option<PreviewVariant>,
}
/// Project the ordered requests after earlier native admission checks succeed.
/// Live always adds an interactive request. Other modes add one only when
/// continuous live preview is supported. Without static support, return those.
/// With static support, add a variant-less static request for Static mode or an
/// empty current list. Grid then appends a static request per section variant,
/// keeping duplicates and using the grid association-filtered override list.
/// Variant-less requests use all effective overrides (excluding grid ID only).
/// Inputs are unchanged; each output owns its values. No request deduplication.
pub fn admitted_request_projections(
    groups: &[PreviewVariantGroup],
    settings: &OverrideSettings,
    mode: CanvasMode<'_>,
    capabilities: Capabilities,
) -> Vec<RequestProjection> {
    let grid = match mode {
        CanvasMode::Grid(group) => Some(group),
        _ => None,
    };
    let overrides: Vec<_> =
        effective_groups_and_overrides(groups, settings, grid.map(|g| g.id.as_str()))
            .into_iter()
            .flat_map(|e| e.overrides)
            .collect();
    let mut requests = Vec::new();
    if matches!(mode, CanvasMode::Live(_)) || capabilities.supports_continuous_live_preview {
        requests.push(RequestProjection {
            display_mode: DisplayMode::Interactive(!matches!(
                mode,
                CanvasMode::Live(HostLocation::External)
            )),
            overrides: overrides.clone(),
            variant: None,
        });
    }
    if !capabilities.supports_static_previews {
        return requests;
    }
    if matches!(mode, CanvasMode::Static) || requests.is_empty() {
        requests.push(RequestProjection {
            display_mode: DisplayMode::Static,
            overrides,
            variant: None,
        });
    }
    if let Some(grid) = grid {
        let overrides = grid_request_overrides(groups, settings, grid);
        for variant in grid.grid_variants() {
            requests.push(RequestProjection {
                display_mode: DisplayMode::Static,
                overrides: overrides.clone(),
                variant: Some(variant),
            });
        }
    }
    requests
}

/// Source-guided settings projection. T represents an opaque boxed control-state
/// value/host handle; no native HashableBox identity or contents are interpreted.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PreviewSettings<T> {
    pub is_enabled: bool,
    pub boxed_canvas_control_states: Vec<T>,
}
impl<T> Default for PreviewSettings<T> {
    fn default() -> Self {
        Self {
            is_enabled: false,
            boxed_canvas_control_states: Vec::new(),
        }
    }
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ConfiguredRequestProjection<T> {
    pub request: RequestProjection,
    pub control_states: Vec<T>,
}
/// The caller resolves the actual structured DiscoveredItem.ID.preview key and
/// supplies its optional stored row. A present row wins as a whole, even disabled
/// or empty; otherwise use default settings. Disabled returns no requests. Every
/// enabled request receives a clone of the selected ordered control-state array.
/// No merge, filtering, deduplication, state installation or persistence occurs.
/// T cloning/handle lifetime remains host-owned; this is not native box equality,
/// transport serialization, resource settlement or complete request construction.
pub fn configured_request_projections<T: Clone>(
    groups: &[PreviewVariantGroup],
    overrides: &OverrideSettings,
    mode: CanvasMode<'_>,
    capabilities: Capabilities,
    stored: Option<&PreviewSettings<T>>,
    defaults: &PreviewSettings<T>,
) -> Vec<ConfiguredRequestProjection<T>> {
    let selected = stored.unwrap_or(defaults);
    if !selected.is_enabled {
        return Vec::new();
    }
    admitted_request_projections(groups, overrides, mode, capabilities)
        .into_iter()
        .map(|request| ConfiguredRequestProjection {
            request,
            control_states: selected.boxed_canvas_control_states.clone(),
        })
        .collect()
}
