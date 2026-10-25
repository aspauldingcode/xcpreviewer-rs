//! Scoped EditorSettings selection and discovered-group alignment.
//! This does not install defaults, persist native modes or apply updates.
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
