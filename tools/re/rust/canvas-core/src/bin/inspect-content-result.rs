//! Bounded inspection of an individual variant or selected-override result.
use canvas_core::{
    binary_plist, binary_plist_writer,
    content_results::{ContentOverridePayload, PreviewVariant},
    multi_select_configuration::MultiSelectConfiguration,
    overrides_configuration::PreviewOverridesConfiguration,
    payload_codec::Value,
    selection_behavior::SelectionBehavior,
    single_select_configuration::SingleSelectConfiguration,
    variants_configuration::{PreviewVariantsConfiguration, Section},
    variants_reply::{PreviewVariantGroup, PreviewVariantsPayload},
};
use std::io::{Read, Write};
const USAGE: &str = "usage: inspect-content-result [--canonical] variant|override|configuration|section|single-selection|multi-selection|selection-behavior|overrides-configuration|group|variants-reply|default-selection INPUT.bplist|-";
fn string(out: &mut impl Write, key: &str, value: Option<&str>) -> std::io::Result<()> {
    if let Some(value) = value {
        let preview: String = value.chars().take(256).collect();
        writeln!(
            out,
            "{key}={preview:?}\n{key}Bytes={}\n{key}Truncated={}",
            value.len(),
            preview.len() < value.len()
        )
    } else {
        writeln!(out, "{key}=absent")
    }
}
fn section_summary(out: &mut impl Write, key: &str, section: &Section) -> std::io::Result<()> {
    string(out, &format!("{key}.title"), section.title.as_deref())?;
    writeln!(out, "{key}.variants={}", section.variants.len())?;
    for (index, variant) in section.variants.iter().take(4).enumerate() {
        string(out, &format!("{key}.variant{index}.id"), Some(&variant.id))?;
        string(
            out,
            &format!("{key}.variant{index}.displayName"),
            Some(&variant.display_name),
        )?;
    }
    writeln!(out, "{key}.variantsShown={}", section.variants.len().min(4))
}
fn group_summary(
    out: &mut impl Write,
    key: &str,
    value: &PreviewVariantGroup,
) -> std::io::Result<()> {
    string(out, &format!("{key}.id"), Some(&value.id))?;
    writeln!(
        out,
        "{key}.associatedGroupIDs={}",
        value.associated_group_ids.len()
    )?;
    for (index, id) in value.associated_group_ids.iter().take(4).enumerate() {
        string(out, &format!("{key}.associated{index}"), Some(id))?;
    }
    writeln!(
        out,
        "{key}.associatedGroupIDsShown={}",
        value.associated_group_ids.len().min(4)
    )?;
    string(
        out,
        &format!("{key}.overridesTitle"),
        value
            .overrides_configuration
            .as_ref()
            .map(|v| v.title.as_str()),
    )?;
    string(
        out,
        &format!("{key}.variantsTitle"),
        value
            .variants_configuration
            .as_ref()
            .map(|v| v.title.as_str()),
    )
}
fn run() -> Result<(), String> {
    let mut args = std::env::args_os().skip(1);
    let first = args.next().ok_or(USAGE)?;
    if first == "--help" && args.next().is_none() {
        println!("{USAGE}\nValues only. Choose the expected kind explicitly; variants-reply handles payload values without transport correlation.\n--canonical emits normalized bplist00 stdout. No effects or overrides are applied.");
        return Ok(());
    }
    let canonical = first == "--canonical";
    let kind = if canonical {
        args.next().ok_or(USAGE)?
    } else {
        first
    };
    if kind != "variant"
        && kind != "override"
        && kind != "configuration"
        && kind != "section"
        && kind != "single-selection"
        && kind != "multi-selection"
        && kind != "selection-behavior"
        && kind != "overrides-configuration"
        && kind != "group"
        && kind != "variants-reply"
        && kind != "default-selection"
    {
        return Err(USAGE.into());
    }
    let input = args.next().ok_or(USAGE)?;
    if args.next().is_some() {
        return Err(USAGE.into());
    }
    let reader: Box<dyn Read> = if input == "-" {
        Box::new(std::io::stdin())
    } else {
        Box::new(std::fs::File::open(input).map_err(|e| format!("input: {e}"))?)
    };
    let mut bytes = Vec::new();
    reader
        .take(64 * 1024 * 1024 + 1)
        .read_to_end(&mut bytes)
        .map_err(|e| format!("input: {e}"))?;
    if bytes.len() > 64 * 1024 * 1024 {
        return Err("input exceeds 64 MiB".into());
    }
    let value = binary_plist::decode(&bytes).map_err(|e| format!("plist: {e:?}"))?;
    let mut out = std::io::stdout().lock();
    let normalized: Value = if kind == "default-selection" {
        let value = PreviewOverridesConfiguration::decode(&value)
            .map_err(|e| format!("default-selection: {e:?}"))?;
        let selected = value.default_selection();
        if !canonical {
            writeln!(out, "result=default-selection\nselected={}", selected.len())
                .map_err(|e| e.to_string())?;
            for (index, id) in selected.iter().take(8).enumerate() {
                string(&mut out, &format!("selected{index}"), Some(id))
                    .map_err(|e| e.to_string())?;
            }
            writeln!(out, "selectedShown={}", selected.len().min(8)).map_err(|e| e.to_string())?;
        }
        Value::Array(selected.iter().map(|id| Value::String(id.into())).collect())
    } else if kind == "variants-reply" {
        let value =
            PreviewVariantsPayload::decode(&value).map_err(|e| format!("variants-reply: {e:?}"))?;
        if !canonical {
            writeln!(out, "result=variants-reply\ngroups={}", value.groups.len())
                .map_err(|e| e.to_string())?;
            for (index, group) in value.groups.iter().take(4).enumerate() {
                group_summary(&mut out, &format!("group{index}"), group)
                    .map_err(|e| e.to_string())?;
            }
            writeln!(out, "groupsShown={}", value.groups.len().min(4))
                .map_err(|e| e.to_string())?;
        }
        value.to_value()
    } else if kind == "group" {
        let value = PreviewVariantGroup::decode(&value).map_err(|e| format!("group: {e:?}"))?;
        if !canonical {
            writeln!(out, "result=group").map_err(|e| e.to_string())?;
            group_summary(&mut out, "group", &value).map_err(|e| e.to_string())?;
        }
        value.to_value()
    } else if kind == "overrides-configuration" {
        let value = PreviewOverridesConfiguration::decode(&value)
            .map_err(|e| format!("overrides-configuration: {e:?}"))?;
        if !canonical {
            writeln!(out, "result=overrides-configuration").map_err(|e| e.to_string())?;
            string(&mut out, "title", Some(&value.title)).map_err(|e| e.to_string())?;
            writeln!(
                out,
                "selectionBehavior={}\nvariants={}\nchildren={}",
                value.selection_behavior.discriminant(),
                value.variants.len(),
                value.child_variant_configurations.len()
            )
            .map_err(|e| e.to_string())?;
            for (index, variant) in value.variants.iter().take(4).enumerate() {
                string(&mut out, &format!("variant{index}.id"), Some(&variant.id))
                    .map_err(|e| e.to_string())?;
            }
            for (index, (id, child)) in value
                .child_variant_configurations
                .iter()
                .take(4)
                .enumerate()
            {
                string(&mut out, &format!("child{index}.id"), Some(id))
                    .map_err(|e| e.to_string())?;
                string(&mut out, &format!("child{index}.title"), Some(&child.title))
                    .map_err(|e| e.to_string())?;
            }
            writeln!(
                out,
                "variantsShown={}\nchildrenShown={}",
                value.variants.len().min(4),
                value.child_variant_configurations.len().min(4)
            )
            .map_err(|e| e.to_string())?;
        }
        value.to_value()
    } else if kind == "selection-behavior" {
        let value =
            SelectionBehavior::decode(&value).map_err(|e| format!("selection-behavior: {e:?}"))?;
        if !canonical {
            writeln!(
                out,
                "result=selection-behavior\ndiscriminant={}",
                value.discriminant()
            )
            .map_err(|e| e.to_string())?;
            match &value {
                SelectionBehavior::SingleSelect(value) => {
                    writeln!(out, "style={}", value.style.as_str()).map_err(|e| e.to_string())?;
                    string(&mut out, "defaultVariant", Some(&value.default_variant))
                        .map_err(|e| e.to_string())?;
                }
                SelectionBehavior::MultiSelect(value) => {
                    writeln!(out, "defaultVariants={}", value.default_variants.len())
                        .map_err(|e| e.to_string())?;
                    for (index, id) in value.default_variants.iter().take(8).enumerate() {
                        string(&mut out, &format!("defaultVariant{index}"), Some(id))
                            .map_err(|e| e.to_string())?;
                    }
                    writeln!(
                        out,
                        "defaultVariantsShown={}",
                        value.default_variants.len().min(8)
                    )
                    .map_err(|e| e.to_string())?;
                }
            }
        }
        value.to_value()
    } else if kind == "multi-selection" {
        let value = MultiSelectConfiguration::decode(&value)
            .map_err(|e| format!("multi-selection: {e:?}"))?;
        if !canonical {
            writeln!(
                out,
                "result=multi-selection\ndefaultVariants={}",
                value.default_variants.len()
            )
            .map_err(|e| e.to_string())?;
            for (index, id) in value.default_variants.iter().take(8).enumerate() {
                string(&mut out, &format!("defaultVariant{index}"), Some(id))
                    .map_err(|e| e.to_string())?;
            }
            writeln!(
                out,
                "defaultVariantsShown={}",
                value.default_variants.len().min(8)
            )
            .map_err(|e| e.to_string())?;
        }
        value.to_value()
    } else if kind == "single-selection" {
        let value = SingleSelectConfiguration::decode(&value)
            .map_err(|e| format!("single-selection: {e:?}"))?;
        if !canonical {
            writeln!(
                out,
                "result=single-selection\nstyle={}",
                value.style.as_str()
            )
            .map_err(|e| e.to_string())?;
            string(&mut out, "defaultVariant", Some(&value.default_variant))
                .map_err(|e| e.to_string())?;
        }
        value.to_value()
    } else if kind == "configuration" {
        let value = PreviewVariantsConfiguration::decode(&value)
            .map_err(|e| format!("configuration: {e:?}"))?;
        if !canonical {
            writeln!(out, "result=configuration").map_err(|e| e.to_string())?;
            string(&mut out, "title", Some(&value.title)).map_err(|e| e.to_string())?;
            writeln!(out, "sections={}", value.sections.len()).map_err(|e| e.to_string())?;
            for (index, section) in value.sections.iter().take(4).enumerate() {
                section_summary(&mut out, &format!("section{index}"), section)
                    .map_err(|e| e.to_string())?;
            }
            writeln!(out, "sectionsShown={}", value.sections.len().min(4))
                .map_err(|e| e.to_string())?;
        }
        value.to_value()
    } else if kind == "section" {
        let value = Section::decode(&value).map_err(|e| format!("section: {e:?}"))?;
        if !canonical {
            writeln!(out, "result=section").map_err(|e| e.to_string())?;
            section_summary(&mut out, "section", &value).map_err(|e| e.to_string())?;
        }
        value.to_value()
    } else if kind == "variant" {
        let value = PreviewVariant::decode(&value).map_err(|e| format!("variant: {e:?}"))?;
        if !canonical {
            writeln!(out, "result=variant").map_err(|e| e.to_string())?;
            string(&mut out, "id", Some(&value.id)).map_err(|e| e.to_string())?;
            string(&mut out, "displayName", Some(&value.display_name))
                .map_err(|e| e.to_string())?;
            writeln!(out, "renderEffects={}", value.render_effects.len())
                .map_err(|e| e.to_string())?;
            for (index, effect) in value.render_effects.iter().take(8).enumerate() {
                string(&mut out, &format!("effect{index}"), Some(&effect.id))
                    .map_err(|e| e.to_string())?;
            }
            writeln!(
                out,
                "renderEffectsShown={}",
                value.render_effects.len().min(8)
            )
            .map_err(|e| e.to_string())?;
            string(
                &mut out,
                "interfaceOrientationOverride",
                value.interface_orientation_override.map(|v| v.as_str()),
            )
            .map_err(|e| e.to_string())?;
        }
        value.to_value()
    } else {
        let value =
            ContentOverridePayload::decode(&value).map_err(|e| format!("override: {e:?}"))?;
        if !canonical {
            writeln!(out, "result=override").map_err(|e| e.to_string())?;
            string(
                &mut out,
                "contentOverride",
                value.content_override.as_deref(),
            )
            .map_err(|e| e.to_string())?;
        }
        value.to_value()
    };
    if canonical {
        let bytes =
            binary_plist_writer::encode(&normalized).map_err(|e| format!("encode: {e:?}"))?;
        out.write_all(&bytes).map_err(|e| format!("output: {e}"))?;
    }
    out.flush().map_err(|e| format!("output: {e}"))
}
fn main() {
    if let Err(error) = run() {
        eprintln!("{error}");
        std::process::exit(1)
    }
}
