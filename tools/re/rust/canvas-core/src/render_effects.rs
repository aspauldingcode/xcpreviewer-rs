//! Effect assembly recovered from PreviewExecutionPoint.updateBehavior.
//! Inputs are already resolved configuration variants. This does not select IDs,
//! resolve content overrides, render content or execute a native update.
use crate::content_results::{PreviewVariant, RenderEffect};
/// Concatenates each override's effects in input order, then the optional variant's
/// effects. Retains duplicates, original spellings and empty effect lists.
pub fn assemble(
    overrides: &[PreviewVariant],
    variant: Option<&PreviewVariant>,
) -> Vec<RenderEffect> {
    overrides
        .iter()
        .chain(variant)
        .flat_map(|v| &v.render_effects)
        .cloned()
        .collect()
}
