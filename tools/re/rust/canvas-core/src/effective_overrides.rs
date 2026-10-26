//! Scoped EditorSettings selection, row-state calculation and group alignment.
//! Native UI bindings, animation and persistence remain caller-owned.
use crate::{
    content_results::PreviewVariant, variant_id_set::VariantIdSet,
    variants_reply::PreviewVariantGroup,
};
use std::collections::{btree_map::Entry, BTreeMap};
use unicode_normalization::UnicodeNormalization;
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct VariantGroupSettings {
    pub is_enabled: bool,
    pub selection: VariantIdSet,
}
/// Canonical group-ID lookup with first-key spelling and last-value assignment.
#[derive(Clone, Debug, Default)]
pub struct OverrideSettings {
    values: BTreeMap<String, (String, VariantGroupSettings)>,
}
impl OverrideSettings {
    pub fn new() -> Self {
        Self::default()
    }
    pub fn insert(
        &mut self,
        id: String,
        value: VariantGroupSettings,
    ) -> Option<VariantGroupSettings> {
        match self.values.entry(id.nfd().collect()) {
            Entry::Vacant(e) => {
                e.insert((id, value));
                None
            }
            Entry::Occupied(mut e) => Some(std::mem::replace(&mut e.get_mut().1, value)),
        }
    }
    /// Original key spellings in deterministic canonical-key order.
    pub fn iter(&self) -> impl Iterator<Item = (&str, &VariantGroupSettings)> {
        self.values.values().map(|(id, value)| (id.as_str(), value))
    }
    /// Read-only UI-row fallback. Missing state is disabled with configuration
    /// defaults, or an empty selection without a configuration. Never installs it.
    pub fn row_settings(&self, group: &PreviewVariantGroup) -> VariantGroupSettings {
        self.get(&group.id)
            .cloned()
            .unwrap_or_else(|| VariantGroupSettings {
                is_enabled: false,
                selection: group
                    .overrides_configuration
                    .as_ref()
                    .map(|c| c.default_selection())
                    .unwrap_or_default(),
            })
    }
    /// Read the row fallback, replace enablement, and always store the complete row.
    /// A write installs missing disabled/default state even if the Bool is equal.
    /// Native binding notifications and persistence are caller-owned.
    pub fn set_row_enabled(&mut self, group: &PreviewVariantGroup, enabled: bool) {
        let mut state = self.row_settings(group);
        state.is_enabled = enabled;
        self.insert(group.id.clone(), state);
    }
    pub fn get(&self, id: &str) -> Option<&VariantGroupSettings> {
        self.values
            .get(&id.nfd().collect::<String>())
            .map(|(_, v)| v)
    }
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct EffectiveGroup<'a> {
    pub group: &'a PreviewVariantGroup,
    pub overrides: Vec<PreviewVariant>,
}
/// `grid_group_id` projects CanvasMode.grid's associated group's ID. Live/static
/// modes use None; the other associated group fields have no effect here.
/// Groups retain input order and duplicates. Child expansion visits only the
/// initially selected direct variants, once per occurrence, and only one level.
pub fn effective_groups_and_overrides<'a>(
    groups: &'a [PreviewVariantGroup],
    settings: &OverrideSettings,
    grid_group_id: Option<&str>,
) -> Vec<EffectiveGroup<'a>> {
    let grid = grid_group_id.map(|s| s.nfd().collect::<String>());
    groups
        .iter()
        .filter_map(|group| {
            let state = settings.get(&group.id)?;
            if !state.is_enabled
                || grid
                    .as_ref()
                    .is_some_and(|id| *id == group.id.nfd().collect::<String>())
            {
                return None;
            }
            let config = group.overrides_configuration.as_ref()?;
            let mut overrides: Vec<_> = config
                .variants
                .iter()
                .filter(|v| state.selection.contains(&v.id))
                .cloned()
                .collect();
            let initial_count = overrides.len();
            for i in 0..initial_count {
                if let Some(child) = config.child_variant_configurations.get(&overrides[i].id) {
                    overrides.extend(
                        child
                            .variants
                            .iter()
                            .filter(|v| state.selection.contains(&v.id))
                            .cloned(),
                    );
                }
            }
            Some(EffectiveGroup { group, overrides })
        })
        .collect()
}

/// Original report of alignment effects, not a native wire type.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Alignment {
    /// Directive to clear storedCanvasMode. It may be a no-op if already absent.
    pub clear_stored_canvas_mode: bool,
    pub removed_settings: usize,
}
/// Removes settings whose canonical IDs are absent from discovered groups.
/// Surviving values/spellings are unchanged; missing settings/defaults are not added.
/// `effective_grid_group_id` is projected from storedCanvasMode ?? defaultCanvasMode.
/// A missing grid ID requests clearing stored mode; mode payloads are caller-owned.
pub fn align_settings(
    groups: &[PreviewVariantGroup],
    settings: &mut OverrideSettings,
    effective_grid_group_id: Option<&str>,
) -> Alignment {
    let ids: VariantIdSet = groups.iter().map(|g| g.id.clone()).collect();
    let clear_stored_canvas_mode = effective_grid_group_id.is_some_and(|id| !ids.contains(id));
    let before = settings.values.len();
    settings.values.retain(|_, (id, _)| ids.contains(id));
    Alignment {
        clear_stored_canvas_mode,
        removed_settings: before - settings.values.len(),
    }
}

/// Source-guided result of rebuilding a multi-select row's child configurations.
/// Replace the caller's child rows with this whole array, including when selection
/// membership did not change. UI binding writes/animation remain caller-owned.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct MultiSelectionUpdate<'a> {
    pub child_configurations:
        Vec<&'a crate::overrides_configuration::PreviewOverridesConfiguration>,
    pub selection_changed: bool,
}
impl VariantGroupSettings {
    /// Rebuild immediate child rows from selected direct variants in source order,
    /// retaining duplicates. Union their recursive defaults into the requested set.
    /// Own defaults and child-added IDs do not activate more rows at this level.
    /// Preserve enablement; equal membership preserves the stored representatives.
    pub fn update_multi_selection<'a>(
        &mut self,
        configuration: &'a crate::overrides_configuration::PreviewOverridesConfiguration,
        requested: VariantIdSet,
    ) -> MultiSelectionUpdate<'a> {
        let child_configurations: Vec<_> = configuration
            .variants
            .iter()
            .filter(|variant| requested.contains(&variant.id))
            .filter_map(|variant| configuration.child_variant_configurations.get(&variant.id))
            .collect();
        let mut selection = requested;
        for child in &child_configurations {
            for id in child.default_selection().iter() {
                selection.insert(id.into());
            }
        }
        let selection_changed = self.selection != selection;
        if selection_changed {
            self.selection = selection;
        }
        MultiSelectionUpdate {
            child_configurations,
            selection_changed,
        }
    }
}

/// Complete replacement child rows and state-change report for a single-ID edit.
/// Native UI binding writes, animation and persistence remain caller-owned.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct SingleSelectionUpdate<'a> {
    pub child_configurations:
        Vec<&'a crate::overrides_configuration::PreviewOverridesConfiguration>,
    pub selection_changed: bool,
}
impl VariantGroupSettings {
    /// Remove other direct roots and their immediate child variant IDs from the
    /// current selection, even when those roots were not selected. Preserve all
    /// other IDs, including grandchildren and existing selected-child values.
    /// Insert the requested opaque ID, then union defaults of its direct child
    /// rows. Enablement and equal-membership stored representatives are preserved.
    pub fn update_single_selection<'a>(
        &mut self,
        configuration: &'a crate::overrides_configuration::PreviewOverridesConfiguration,
        requested: String,
    ) -> SingleSelectionUpdate<'a> {
        let initial: VariantIdSet = [requested.clone()].into_iter().collect();
        let mut selection = self.selection.clone();
        for variant in &configuration.variants {
            if !initial.contains(&variant.id) {
                selection.remove(&variant.id);
                if let Some(child) = configuration.child_variant_configurations.get(&variant.id) {
                    for variant in &child.variants {
                        selection.remove(&variant.id);
                    }
                }
            }
        }
        selection.insert(requested);
        let child_configurations: Vec<_> = configuration
            .variants
            .iter()
            .filter(|variant| initial.contains(&variant.id))
            .filter_map(|variant| configuration.child_variant_configurations.get(&variant.id))
            .collect();
        for child in &child_configurations {
            for id in child.default_selection().iter() {
                selection.insert(id.into());
            }
        }
        let selection_changed = self.selection != selection;
        if selection_changed {
            self.selection = selection;
        }
        SingleSelectionUpdate {
            child_configurations,
            selection_changed,
        }
    }
}

/// Eligible read results, retaining stored spellings for direct-root matches.
/// Native Set iteration chooses one ID; this report does not reproduce that order.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct SingleSelectionCandidates {
    pub candidates: VariantIdSet,
    pub uses_defaults: bool,
}
impl SingleSelectionCandidates {
    /// Deterministic portable choice in decomposed-key order. With several IDs,
    /// this may differ from the shipped UI's randomized Set iteration.
    pub fn portable_value(&self) -> Option<&str> {
        self.candidates.iter().next()
    }
}
impl VariantGroupSettings {
    /// Per-call projection of the binding factory/read closure, not a retained
    /// SwiftUI Binding. Availability requires nonempty recursive defaults.
    /// Prefer stored IDs matching direct variants; otherwise return defaults.
    /// Enablement, selection behavior style and child-only matches do not gate it.
    pub fn single_selection_candidates(
        &self,
        configuration: &crate::overrides_configuration::PreviewOverridesConfiguration,
    ) -> Option<SingleSelectionCandidates> {
        let defaults = configuration.default_selection();
        if defaults.is_empty() {
            return None;
        }
        let roots: VariantIdSet = configuration
            .variants
            .iter()
            .map(|v| v.id.clone())
            .collect();
        let matching: VariantIdSet = self
            .selection
            .iter()
            .filter(|id| roots.contains(id))
            .map(str::to_owned)
            .collect();
        let uses_defaults = matching.is_empty();
        Some(SingleSelectionCandidates {
            candidates: if uses_defaults { defaults } else { matching },
            uses_defaults,
        })
    }
}

/// Flatten effective overrides for the grid request branch of previewRequests.
/// The supplied group is the CanvasMode.grid payload, even when not present in
/// discovered groups. Exclude equal IDs and direct associations in either
/// direction. Do not follow transitive associations or alter stored state.
/// Preserve surviving group/variant order and duplicates, including child values
/// already selected by effective_groups_and_overrides. This does not choose a
/// canvas mode, evaluate capability fallback, or construct a complete request.
pub fn grid_request_overrides(
    groups: &[PreviewVariantGroup],
    settings: &OverrideSettings,
    grid_group: &PreviewVariantGroup,
) -> Vec<PreviewVariant> {
    effective_groups_and_overrides(groups, settings, Some(&grid_group.id))
        .into_iter()
        .filter(|entry| {
            !entry.group.associated_group_ids.contains(&grid_group.id)
                && !grid_group.associated_group_ids.contains(&entry.group.id)
        })
        .flat_map(|entry| entry.overrides)
        .collect()
}
