//! Bounded inspection of an individual variant or selected-override result.
use canvas_core::{
    binary_plist, binary_plist_writer,
    content_results::{ContentOverridePayload, PreviewVariant},
    payload_codec::Value,
    single_select_configuration::SingleSelectConfiguration,
    variants_configuration::{PreviewVariantsConfiguration, Section},
};
use std::io::{Read, Write};
const USAGE: &str = "usage: inspect-content-result [--canonical] variant|override|configuration|section|single-selection INPUT.bplist|-";
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
fn run() -> Result<(), String> {
    let mut args = std::env::args_os().skip(1);
    let first = args.next().ok_or(USAGE)?;
    if first == "--help" && args.next().is_none() {
        println!("{USAGE}\nValues only. Choose the expected kind explicitly; whole groups and full override-selection configuration are not supported.\n--canonical emits normalized bplist00 stdout. No effects or overrides are applied.");
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
    let normalized: Value = if kind == "single-selection" {
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
