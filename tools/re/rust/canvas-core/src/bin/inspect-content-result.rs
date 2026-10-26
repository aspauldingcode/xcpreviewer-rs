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
const USAGE: &str = "usage: inspect-content-result [--canonical] variant|override|configuration|section|single-selection|multi-selection|selection-behavior|overrides-configuration|group|variants-reply|default-selection|group-variants|render-effects|effective-overrides|align-settings|row-settings|update-multi-selection|update-single-selection|row-controls|override-cache-keys|control-state-keys|task-cache|grid-request-overrides|request-projections|configured-request-projections|plist-box|control-state-boxes|unbox-string|unbox-optional-string INPUT.bplist|-";
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
        && kind != "group-variants"
        && kind != "render-effects"
        && kind != "plist-box"
        && kind != "control-state-boxes"
        && kind != "control-state-keys"
        && kind != "unbox-string"
        && kind != "unbox-optional-string"
        && kind != "configured-request-projections"
        && kind != "request-projections"
        && kind != "grid-request-overrides"
        && kind != "effective-overrides"
        && kind != "align-settings"
        && kind != "row-settings"
        && kind != "update-multi-selection"
        && kind != "update-single-selection"
        && kind != "row-controls"
        && kind != "override-cache-keys"
        && kind != "task-cache"
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
    let normalized: Value = if kind == "task-cache" {
        use canvas_core::{
            content_requests::{ContentOverrideCacheKey, RequestContentOverridePayload},
            task_cache::{TaskAcquisition, TaskCache},
        };
        enum Op {
            Acquire(ContentOverrideCacheKey),
            Failure(usize),
            Invalidate(ContentOverrideCacheKey, bool),
        }
        let Value::Dictionary(f) = &value else {
            return Err("task-cache-input: dictionary required".into());
        };
        let clear = match f.get("clearOnFailure") {
            None => false,
            Some(Value::Boolean(v)) => *v,
            _ => return Err("task-cache-input: clearOnFailure Bool".into()),
        };
        let Some(Value::Array(values)) = f.get("operations") else {
            return Err("task-cache-input: operations array".into());
        };
        let mut available = Vec::new();
        let operations = values
            .iter()
            .map(|v| -> Result<Op, String> {
                let Value::Dictionary(f) = v else {
                    return Err("task-cache-input: operation dictionary".into());
                };
                let Some(Value::String(op)) = f.get("op") else {
                    return Err("task-cache-input: op String".into());
                };
                let key = || -> Result<ContentOverrideCacheKey, String> {
                    let Some(Value::Dictionary(request)) = f.get("request") else {
                        return Err("task-cache-input: request dictionary".into());
                    };
                    RequestContentOverridePayload::decode_dictionary(request)
                        .map(|v| v.cache_key())
                        .map_err(|e| format!("task-cache-input: request: {e:?}"))
                };
                match op.as_str() {
                    "acquire" => {
                        let key = key()?;
                        available.push(true);
                        Ok(Op::Acquire(key))
                    }
                    "failure" => {
                        let Some(Value::Integer(i)) = f.get("ticket") else {
                            return Err("task-cache-input: ticket nonnegative integer".into());
                        };
                        let i = usize::try_from(*i)
                            .map_err(|_| "task-cache-input: ticket nonnegative")?;
                        let Some(v) = available.get_mut(i) else {
                            return Err("task-cache-input: unknown ticket".into());
                        };
                        if !*v {
                            return Err("task-cache-input: consumed ticket".into());
                        }
                        *v = false;
                        Ok(Op::Failure(i))
                    }
                    "invalidate" => {
                        let cancel = match f.get("cancelingTask") {
                            None => true,
                            Some(Value::Boolean(v)) => *v,
                            _ => return Err("task-cache-input: cancelingTask Bool".into()),
                        };
                        Ok(Op::Invalidate(key()?, cancel))
                    }
                    _ => Err("task-cache-input: unknown operation".into()),
                }
            })
            .collect::<Result<Vec<_>, _>>()?;
        let mut cache = TaskCache::new(clear);
        let mut tickets: Vec<Option<TaskAcquisition<ContentOverrideCacheKey, i64>>> = Vec::new();
        let mut starts = 0i64;
        let mut cancel_requests = Vec::new();
        let mut events = Vec::new();
        for op in operations {
            let mut event = std::collections::BTreeMap::new();
            match op {
                Op::Acquire(key) => {
                    let lookup = cache.acquire(key, || {
                        starts += 1;
                        starts
                    });
                    event.insert("op".into(), Value::String("acquire".into()));
                    event.insert("task".into(), Value::Integer(*lookup.task()));
                    event.insert("created".into(), Value::Boolean(lookup.created()));
                    tickets.push(Some(lookup));
                }
                Op::Failure(i) => {
                    event.insert("op".into(), Value::String("failure".into()));
                    if let Some(task) = cache.observe_failure(
                        tickets[i]
                            .take()
                            .ok_or("task-cache-input: ticket invariant")?,
                    ) {
                        event.insert("removed".into(), Value::Integer(task));
                    }
                }
                Op::Invalidate(key, cancel) => {
                    event.insert("op".into(), Value::String("invalidate".into()));
                    if let Some(task) = cache.invalidate_with(&key, cancel, |task| {
                        cancel_requests.push(Value::Integer(*task))
                    }) {
                        event.insert("removed".into(), Value::Integer(task));
                        if cancel {
                            event.insert("cancelRequested".into(), Value::Integer(task));
                        }
                    }
                }
            }
            events.push(Value::Dictionary(event));
        }
        let mut retained: Vec<_> = cache.tasks().copied().collect();
        retained.sort();
        if !canonical {
            writeln!(out,"result=task-cache\noperations={}\ntasksStarted={}\nretainedTasks={}\ncancelRequests={}\neventsShown={}",events.len(),starts,retained.len(),cancel_requests.len(),events.len().min(8)).map_err(|e|e.to_string())?;
            for (i, event) in events.iter().take(8).enumerate() {
                if let Value::Dictionary(f) = event {
                    if let Some(Value::String(op)) = f.get("op") {
                        writeln!(out, "event{i}.op={op}").map_err(|e| e.to_string())?;
                    }
                }
            }
        }
        Value::Dictionary(
            [
                ("events".into(), Value::Array(events)),
                ("tasksStarted".into(), Value::Integer(starts)),
                (
                    "retainedTasks".into(),
                    Value::Array(retained.into_iter().map(Value::Integer).collect()),
                ),
                ("cancelRequests".into(), Value::Array(cancel_requests)),
            ]
            .into_iter()
            .collect(),
        )
    } else if kind == "control-state-keys" {
        use canvas_core::{hashable_plist_box::HashablePlistBox, plist_value_box::decode_boxes};
        let boxes = decode_boxes(&value).map_err(|e| format!("control-state-keys: {e:?}"))?;
        // Validate every snapshot before producing any output.
        let boxes = boxes
            .into_iter()
            .map(HashablePlistBox::new)
            .collect::<Result<Vec<_>, _>>()
            .map_err(|e| format!("control-state-keys: {e:?}"))?;
        let mut keys = std::collections::HashMap::new();
        let representatives: Vec<_> = boxes
            .iter()
            .enumerate()
            .map(|(i, b)| *keys.entry(b).or_insert(i))
            .collect();
        if !canonical {
            writeln!(
                out,
                "result=control-state-keys\nboxes={}\nuniqueKeys={}\nrepresentativesShown={}",
                boxes.len(),
                keys.len(),
                boxes.len().min(8)
            )
            .map_err(|e| e.to_string())?;
            for (i, representative) in representatives.iter().take(8).enumerate() {
                writeln!(out, "box{i}.representative={representative}")
                    .map_err(|e| e.to_string())?;
            }
        }
        Value::Dictionary(
            [
                (
                    "representatives".into(),
                    Value::Array(
                        representatives
                            .iter()
                            .map(|i| Value::Integer(*i as i64))
                            .collect(),
                    ),
                ),
                ("uniqueKeys".into(), Value::Integer(keys.len() as i64)),
            ]
            .into_iter()
            .collect(),
        )
    } else if kind == "override-cache-keys" {
        use canvas_core::content_requests::RequestContentOverridePayload;
        let Value::Array(requests) = &value else {
            return Err("override-cache-input: request array required".into());
        };
        let requests = requests
            .iter()
            .map(|value| {
                let Value::Dictionary(fields) = value else {
                    return Err("override-cache-input: request dictionary".into());
                };
                RequestContentOverridePayload::decode_dictionary(fields)
                    .map_err(|e| format!("override-cache-input: {e:?}"))
            })
            .collect::<Result<Vec<_>, String>>()?;
        let mut keys = std::collections::HashMap::new();
        let classes: Vec<usize> = requests
            .iter()
            .enumerate()
            .map(|(i, request)| *keys.entry(request.cache_key()).or_insert(i))
            .collect();
        if !canonical {
            writeln!(
                out,
                "result=override-cache-keys\nrequests={}\nuniqueKeys={}\nrepresentativesShown={}",
                classes.len(),
                keys.len(),
                classes.len().min(8)
            )
            .map_err(|e| e.to_string())?;
            for (i, representative) in classes.iter().take(8).enumerate() {
                writeln!(out, "request{i}.representative={representative}")
                    .map_err(|e| e.to_string())?;
            }
        }
        Value::Dictionary(
            [
                (
                    "representatives".into(),
                    Value::Array(classes.iter().map(|i| Value::Integer(*i as i64)).collect()),
                ),
                ("uniqueKeys".into(), Value::Integer(keys.len() as i64)),
            ]
            .into_iter()
            .collect(),
        )
    } else if kind == "row-controls" {
        use canvas_core::{
            effective_overrides::{OverrideSettings, VariantGroupSettings},
            variant_id_set::VariantIdSet,
        };
        let Value::Dictionary(f) = &value else {
            return Err("row-controls-input: expected dictionary".into());
        };
        let group = PreviewVariantGroup::decode(
            f.get("group").ok_or("row-controls-input: group required")?,
        )
        .map_err(|e| format!("row-controls-input: group: {e:?}"))?;
        let mut settings = OverrideSettings::new();
        if let Some(v) = f.get("settings") {
            let Value::Dictionary(v) = v else {
                return Err("row-controls-input: settings dictionary".into());
            };
            let (Some(Value::Boolean(enabled)), Some(Value::Array(ids))) =
                (v.get("isEnabled"), v.get("selection"))
            else {
                return Err(
                    "row-controls-input: settings Bool isEnabled and selection array".into(),
                );
            };
            let selection = ids
                .iter()
                .map(|v| {
                    if let Value::String(id) = v {
                        Ok(id.clone())
                    } else {
                        Err("row-controls-input: ID String")
                    }
                })
                .collect::<Result<VariantIdSet, _>>()?;
            settings.insert(
                group.id.clone(),
                VariantGroupSettings {
                    is_enabled: *enabled,
                    selection,
                },
            );
        }
        let requested = match f.get("requestedEnabled") {
            None => None,
            Some(Value::Boolean(v)) => Some(*v),
            _ => return Err("row-controls-input: requestedEnabled Bool".into()),
        };
        if let Some(enabled) = requested {
            settings.set_row_enabled(&group, enabled);
        }
        let state = settings.row_settings(&group);
        let read = group
            .overrides_configuration
            .as_ref()
            .and_then(|c| state.single_selection_candidates(c));
        if !canonical {
            writeln!(out,"result=row-controls\nisStored={}\nisEnabled={}\nenableWriteRequested={}\nselection={}\nsingleSelectionAvailable={}",settings.get(&group.id).is_some(),state.is_enabled,requested.is_some(),state.selection.len(),read.is_some()).map_err(|e|e.to_string())?;
            for (i, id) in state.selection.iter().take(8).enumerate() {
                string(&mut out, &format!("selected{i}"), Some(id)).map_err(|e| e.to_string())?;
            }
            writeln!(out, "selectionShown={}", state.selection.len().min(8))
                .map_err(|e| e.to_string())?;
            if let Some(read) = &read {
                writeln!(
                    out,
                    "usesDefaults={}\ncandidates={}\ncandidatesShown={}",
                    read.uses_defaults,
                    read.candidates.len(),
                    read.candidates.len().min(8)
                )
                .map_err(|e| e.to_string())?;
                string(&mut out, "portableValue", read.portable_value())
                    .map_err(|e| e.to_string())?;
                for (i, id) in read.candidates.iter().take(8).enumerate() {
                    string(&mut out, &format!("candidate{i}"), Some(id))
                        .map_err(|e| e.to_string())?;
                }
            }
        }
        let mut report = std::collections::BTreeMap::from([
            (
                "isStored".into(),
                Value::Boolean(settings.get(&group.id).is_some()),
            ),
            ("isEnabled".into(), Value::Boolean(state.is_enabled)),
            (
                "enableWriteRequested".into(),
                Value::Boolean(requested.is_some()),
            ),
            (
                "selection".into(),
                Value::Array(
                    state
                        .selection
                        .iter()
                        .map(|id| Value::String(id.into()))
                        .collect(),
                ),
            ),
            (
                "singleSelectionAvailable".into(),
                Value::Boolean(read.is_some()),
            ),
        ]);
        if let Some(read) = read {
            report.insert("usesDefaults".into(), Value::Boolean(read.uses_defaults));
            report.insert(
                "candidates".into(),
                Value::Array(
                    read.candidates
                        .iter()
                        .map(|id| Value::String(id.into()))
                        .collect(),
                ),
            );
            report.insert(
                "portableValue".into(),
                Value::String(
                    read.portable_value()
                        .ok_or("row-controls-input: empty read invariant")?
                        .into(),
                ),
            );
        }
        Value::Dictionary(report)
    } else if kind == "update-multi-selection" || kind == "update-single-selection" {
        use canvas_core::{
            effective_overrides::VariantGroupSettings, variant_id_set::VariantIdSet,
        };
        let Value::Dictionary(f) = &value else {
            return Err("selection-update-input: expected dictionary".into());
        };
        let configuration = PreviewOverridesConfiguration::decode(
            f.get("configuration")
                .ok_or("selection-update-input: configuration required")?,
        )
        .map_err(|e| format!("selection-update-input: configuration: {e:?}"))?;
        let Some(Value::Boolean(is_enabled)) = f.get("isEnabled") else {
            return Err("selection-update-input: isEnabled Bool required".into());
        };
        let ids = |key: &str| -> Result<VariantIdSet, String> {
            let Some(Value::Array(values)) = f.get(key) else {
                return Err(format!("selection-update-input: {key} array required"));
            };
            values
                .iter()
                .map(|v| match v {
                    Value::String(id) => Ok(id.clone()),
                    _ => Err(format!("selection-update-input: {key} ID String")),
                })
                .collect()
        };
        let mut state = VariantGroupSettings {
            is_enabled: *is_enabled,
            selection: ids("selection")?,
        };
        let (child_configurations, selection_changed) = if kind == "update-single-selection" {
            let Some(Value::String(requested)) = f.get("requestedVariant") else {
                return Err("selection-update-input: requestedVariant String required".into());
            };
            let update = state.update_single_selection(&configuration, requested.clone());
            (update.child_configurations, update.selection_changed)
        } else {
            let update = state.update_multi_selection(&configuration, ids("requestedSelection")?);
            (update.child_configurations, update.selection_changed)
        };
        if !canonical {
            writeln!(out,"result={}\nselectionChanged={}\nisEnabled={}\nselection={}\nchildConfigurations={}",kind.to_string_lossy(),selection_changed,state.is_enabled,state.selection.len(),child_configurations.len()).map_err(|e|e.to_string())?;
            for (i, id) in state.selection.iter().take(8).enumerate() {
                string(&mut out, &format!("selected{i}"), Some(id)).map_err(|e| e.to_string())?;
            }
            writeln!(
                out,
                "selectionShown={}\nchildConfigurationsShown={}",
                state.selection.len().min(8),
                child_configurations.len().min(4)
            )
            .map_err(|e| e.to_string())?;
            for (i, child) in child_configurations.iter().take(4).enumerate() {
                string(&mut out, &format!("child{i}.title"), Some(&child.title))
                    .map_err(|e| e.to_string())?;
            }
        }
        Value::Dictionary(
            [
                ("isEnabled".into(), Value::Boolean(state.is_enabled)),
                ("selectionChanged".into(), Value::Boolean(selection_changed)),
                (
                    "selection".into(),
                    Value::Array(
                        state
                            .selection
                            .iter()
                            .map(|id| Value::String(id.into()))
                            .collect(),
                    ),
                ),
                (
                    "childConfigurations".into(),
                    Value::Array(child_configurations.iter().map(|c| c.to_value()).collect()),
                ),
            ]
            .into_iter()
            .collect(),
        )
    } else if kind == "effective-overrides"
        || kind == "align-settings"
        || kind == "row-settings"
        || kind == "grid-request-overrides"
        || kind == "request-projections"
        || kind == "configured-request-projections"
    {
        use canvas_core::effective_overrides::{
            effective_groups_and_overrides, OverrideSettings, VariantGroupSettings,
        };
        let Value::Dictionary(f) = &value else {
            return Err("override-input: expected dictionary".into());
        };
        let Some(Value::Array(groups)) = f.get("groups") else {
            return Err("override-input: required groups array".into());
        };
        let groups = groups
            .iter()
            .map(PreviewVariantGroup::decode)
            .collect::<Result<Vec<_>, _>>()
            .map_err(|e| format!("override-input: group: {e:?}"))?;
        let Some(Value::Array(rows)) = f.get("settings") else {
            return Err("override-input: required settings array".into());
        };
        let mut settings = OverrideSettings::new();
        for row in rows {
            let Value::Dictionary(row) = row else {
                return Err("override-input: settings entry dictionary".into());
            };
            let (
                Some(Value::String(id)),
                Some(Value::Boolean(is_enabled)),
                Some(Value::Array(selection)),
            ) = (
                row.get("groupID"),
                row.get("isEnabled"),
                row.get("selection"),
            )
            else {
                return Err(
                    "override-input: required groupID String, isEnabled Bool and selection array"
                        .into(),
                );
            };
            let selection = selection
                .iter()
                .map(|v| match v {
                    Value::String(id) => Ok(id.clone()),
                    _ => Err("override-input: selection ID String"),
                })
                .collect::<Result<canvas_core::variant_id_set::VariantIdSet, _>>()?;
            settings.insert(
                id.clone(),
                VariantGroupSettings {
                    is_enabled: *is_enabled,
                    selection,
                },
            );
        }
        let grid = match f.get("gridGroupID").filter(|_| {
            kind != "grid-request-overrides"
                && kind != "request-projections"
                && kind != "plist-box"
                && kind != "control-state-boxes"
                && kind != "unbox-string"
                && kind != "unbox-optional-string"
                && kind != "configured-request-projections"
        }) {
            None => None,
            Some(Value::String(id)) => Some(id.as_str()),
            _ => return Err("override-input: gridGroupID String".into()),
        };
        if kind == "request-projections" || kind == "configured-request-projections" {
            use canvas_core::request_projection::{
                admitted_request_projections, CanvasMode, Capabilities, DisplayMode, HostLocation,
            };
            let Some(Value::Dictionary(mode)) = f.get("mode") else {
                return Err("request-projections: required mode dictionary".into());
            };
            let Some(Value::String(tag)) = mode.get("discriminant") else {
                return Err("request-projections: required mode discriminant String".into());
            };
            let grid = if tag == "grid" {
                Some(
                    PreviewVariantGroup::decode(
                        mode.get("group")
                            .ok_or("request-projections: required grid group")?,
                    )
                    .map_err(|e| format!("request-projections: grid group: {e:?}"))?,
                )
            } else {
                None
            };
            let mode = match tag.as_str() {
                "live" => match mode.get("hostLocation") {
                    Some(Value::String(s)) if s == "inCanvas" => {
                        CanvasMode::Live(HostLocation::InCanvas)
                    }
                    Some(Value::String(s)) if s == "external" => {
                        CanvasMode::Live(HostLocation::External)
                    }
                    _ => {
                        return Err(
                            "request-projections: live hostLocation inCanvas|external".into()
                        )
                    }
                },
                "grid" => CanvasMode::Grid(grid.as_ref().unwrap()),
                "static" => CanvasMode::Static,
                _ => return Err("request-projections: unknown canvas mode".into()),
            };
            let Some(Value::Dictionary(caps)) = f.get("capabilities") else {
                return Err("request-projections: required capabilities dictionary".into());
            };
            let (Some(Value::Boolean(continuous)), Some(Value::Boolean(static_previews))) = (
                caps.get("supportsContinuousLivePreview"),
                caps.get("supportsStaticPreviews"),
            ) else {
                return Err("request-projections: required capability Bools".into());
            };
            let capabilities = Capabilities {
                supports_continuous_live_preview: *continuous,
                supports_static_previews: *static_previews,
            };
            let requests: Vec<(_, Option<Vec<Value>>)> = if kind == "configured-request-projections"
            {
                use canvas_core::request_projection::{
                    configured_request_projections, PreviewSettings,
                };
                fn row(value: &Value) -> Result<PreviewSettings<Value>, String> {
                    let Value::Dictionary(row) = value else {
                        return Err("configured-request-projections: settings dictionary".into());
                    };
                    let (Some(Value::Boolean(enabled)), Some(Value::Array(states))) =
                        (row.get("isEnabled"), row.get("boxedCanvasControlStates"))
                    else {
                        return Err("configured-request-projections: required isEnabled Bool and boxedCanvasControlStates array".into());
                    };
                    Ok(PreviewSettings {
                        is_enabled: *enabled,
                        boxed_canvas_control_states: states.clone(),
                    })
                }
                let defaults = row(f
                    .get("defaultPreviewSettings")
                    .ok_or("configured-request-projections: required defaultPreviewSettings")?)?;
                let stored = f.get("previewSettings").map(row).transpose()?;
                configured_request_projections(
                    &groups,
                    &settings,
                    mode,
                    capabilities,
                    stored.as_ref(),
                    &defaults,
                )
                .into_iter()
                .map(|p| (p.request, Some(p.control_states)))
                .collect()
            } else {
                admitted_request_projections(&groups, &settings, mode, capabilities)
                    .into_iter()
                    .map(|p| (p, None))
                    .collect()
            };
            if !canonical {
                writeln!(
                    out,
                    "result={}\nrequests={}",
                    if kind == "configured-request-projections" {
                        "configured-request-projections"
                    } else {
                        "request-projections"
                    },
                    requests.len()
                )
                .map_err(|e| e.to_string())?;
                for (i, (request, states)) in requests.iter().take(8).enumerate() {
                    if let Some(states) = states {
                        writeln!(out, "request{i}.controlStates={}", states.len())
                            .map_err(|e| e.to_string())?;
                    }
                    writeln!(
                        out,
                        "request{i}.displayMode={}\nrequest{i}.overrides={}",
                        match request.display_mode {
                            DisplayMode::Interactive(true) => "interactive(true)",
                            DisplayMode::Interactive(false) => "interactive(false)",
                            DisplayMode::Static => "static",
                        },
                        request.overrides.len()
                    )
                    .map_err(|e| e.to_string())?;
                    string(
                        &mut out,
                        &format!("request{i}.variant"),
                        request.variant.as_ref().map(|v| v.id.as_str()),
                    )
                    .map_err(|e| e.to_string())?;
                }
                writeln!(out, "requestsShown={}", requests.len().min(8))
                    .map_err(|e| e.to_string())?;
            }
            Value::Array(
                requests
                    .iter()
                    .map(|(request, states)| {
                        let mut display = std::collections::BTreeMap::new();
                        match request.display_mode {
                            DisplayMode::Interactive(value) => {
                                display.insert(
                                    "discriminant".into(),
                                    Value::String("interactive".into()),
                                );
                                display.insert("value".into(), Value::Boolean(value));
                            }
                            DisplayMode::Static => {
                                display
                                    .insert("discriminant".into(), Value::String("static".into()));
                            }
                        }
                        let mut fields: std::collections::BTreeMap<String, Value> = [
                            ("displayMode".into(), Value::Dictionary(display)),
                            (
                                "overrides".into(),
                                Value::Array(
                                    request
                                        .overrides
                                        .iter()
                                        .map(PreviewVariant::to_value)
                                        .collect(),
                                ),
                            ),
                        ]
                        .into_iter()
                        .collect();
                        if let Some(variant) = &request.variant {
                            fields.insert("variant".into(), variant.to_value());
                        }
                        if let Some(states) = states {
                            fields.insert("controlState".into(), Value::Array(states.clone()));
                        }
                        Value::Dictionary(fields)
                    })
                    .collect(),
            )
        } else if kind == "grid-request-overrides" {
            let grid = PreviewVariantGroup::decode(
                f.get("gridGroup")
                    .ok_or("grid-request-overrides: required gridGroup")?,
            )
            .map_err(|e| format!("grid-request-overrides: gridGroup: {e:?}"))?;
            let variants =
                canvas_core::effective_overrides::grid_request_overrides(&groups, &settings, &grid);
            if !canonical {
                writeln!(
                    out,
                    "result=grid-request-overrides\noverrides={}",
                    variants.len()
                )
                .map_err(|e| e.to_string())?;
                for (i, variant) in variants.iter().take(8).enumerate() {
                    string(&mut out, &format!("override{i}"), Some(&variant.id))
                        .map_err(|e| e.to_string())?;
                }
                writeln!(out, "overridesShown={}", variants.len().min(8))
                    .map_err(|e| e.to_string())?;
            }
            Value::Array(variants.iter().map(PreviewVariant::to_value).collect())
        } else if kind == "row-settings" {
            let rows: Vec<_> = groups
                .iter()
                .map(|g| (g, settings.row_settings(g), settings.get(&g.id).is_some()))
                .collect();
            if !canonical {
                writeln!(out, "result=row-settings\nrows={}", rows.len())
                    .map_err(|e| e.to_string())?;
                for (i, (group, state, stored)) in rows.iter().take(4).enumerate() {
                    string(&mut out, &format!("row{i}.groupID"), Some(&group.id))
                        .map_err(|e| e.to_string())?;
                    writeln!(
                        out,
                        "row{i}.isStored={stored}\nrow{i}.isEnabled={}\nrow{i}.selection={}",
                        state.is_enabled,
                        state.selection.len()
                    )
                    .map_err(|e| e.to_string())?;
                    for (j, id) in state.selection.iter().take(8).enumerate() {
                        string(&mut out, &format!("row{i}.selected{j}"), Some(id))
                            .map_err(|e| e.to_string())?;
                    }
                    writeln!(
                        out,
                        "row{i}.selectionShown={}",
                        state.selection.len().min(8)
                    )
                    .map_err(|e| e.to_string())?;
                }
                writeln!(out, "rowsShown={}", rows.len().min(4)).map_err(|e| e.to_string())?;
            }
            Value::Array(
                rows.iter()
                    .map(|(group, state, stored)| {
                        Value::Dictionary(
                            [
                                ("groupID".into(), Value::String(group.id.clone())),
                                ("isStored".into(), Value::Boolean(*stored)),
                                ("isEnabled".into(), Value::Boolean(state.is_enabled)),
                                (
                                    "selection".into(),
                                    Value::Array(
                                        state
                                            .selection
                                            .iter()
                                            .map(|id| Value::String(id.into()))
                                            .collect(),
                                    ),
                                ),
                            ]
                            .into_iter()
                            .collect(),
                        )
                    })
                    .collect(),
            )
        } else if kind == "align-settings" {
            let report =
                canvas_core::effective_overrides::align_settings(&groups, &mut settings, grid);
            if !canonical {
                writeln!(out,"result=align-settings\nclearStoredCanvasMode={}\nremovedSettings={}\nsettings={}",report.clear_stored_canvas_mode,report.removed_settings,settings.iter().count()).map_err(|e|e.to_string())?;
                for (i, (id, state)) in settings.iter().take(4).enumerate() {
                    string(&mut out, &format!("setting{i}.groupID"), Some(id))
                        .map_err(|e| e.to_string())?;
                    writeln!(
                        out,
                        "setting{i}.isEnabled={}\nsetting{i}.selection={}",
                        state.is_enabled,
                        state.selection.len()
                    )
                    .map_err(|e| e.to_string())?;
                    for (j, id) in state.selection.iter().take(8).enumerate() {
                        string(&mut out, &format!("setting{i}.selected{j}"), Some(id))
                            .map_err(|e| e.to_string())?;
                    }
                    writeln!(
                        out,
                        "setting{i}.selectionShown={}",
                        state.selection.len().min(8)
                    )
                    .map_err(|e| e.to_string())?;
                }
                writeln!(out, "settingsShown={}", settings.iter().count().min(4))
                    .map_err(|e| e.to_string())?;
            }
            let states = settings
                .iter()
                .map(|(id, state)| {
                    Value::Dictionary(
                        [
                            ("groupID".into(), Value::String(id.into())),
                            ("isEnabled".into(), Value::Boolean(state.is_enabled)),
                            (
                                "selection".into(),
                                Value::Array(
                                    state
                                        .selection
                                        .iter()
                                        .map(|id| Value::String(id.into()))
                                        .collect(),
                                ),
                            ),
                        ]
                        .into_iter()
                        .collect(),
                    )
                })
                .collect();
            Value::Dictionary(
                [
                    (
                        "clearStoredCanvasMode".into(),
                        Value::Boolean(report.clear_stored_canvas_mode),
                    ),
                    (
                        "removedSettings".into(),
                        Value::Integer(report.removed_settings as i64),
                    ),
                    ("settings".into(), Value::Array(states)),
                ]
                .into_iter()
                .collect(),
            )
        } else {
            let effective = effective_groups_and_overrides(&groups, &settings, grid);
            if !canonical {
                writeln!(
                    out,
                    "result=effective-overrides\ngroups={}",
                    effective.len()
                )
                .map_err(|e| e.to_string())?;
                for (i, entry) in effective.iter().take(4).enumerate() {
                    string(&mut out, &format!("group{i}.id"), Some(&entry.group.id))
                        .map_err(|e| e.to_string())?;
                    writeln!(out, "group{i}.overrides={}", entry.overrides.len())
                        .map_err(|e| e.to_string())?;
                    for (j, v) in entry.overrides.iter().take(8).enumerate() {
                        string(&mut out, &format!("group{i}.override{j}"), Some(&v.id))
                            .map_err(|e| e.to_string())?;
                    }
                    writeln!(
                        out,
                        "group{i}.overridesShown={}",
                        entry.overrides.len().min(8)
                    )
                    .map_err(|e| e.to_string())?;
                }
                writeln!(out, "groupsShown={}", effective.len().min(4))
                    .map_err(|e| e.to_string())?;
            }
            Value::Array(
                effective
                    .iter()
                    .map(|e| {
                        Value::Dictionary(
                            [
                                ("group".into(), e.group.to_value()),
                                (
                                    "overrides".into(),
                                    Value::Array(
                                        e.overrides.iter().map(PreviewVariant::to_value).collect(),
                                    ),
                                ),
                            ]
                            .into_iter()
                            .collect(),
                        )
                    })
                    .collect(),
            )
        }
    } else if kind == "plist-box"
        || kind == "control-state-boxes"
        || kind == "unbox-string"
        || kind == "unbox-optional-string"
    {
        use canvas_core::plist_value_box::{decode_boxes, PlistValueBox};
        if kind == "control-state-boxes" {
            let boxes = decode_boxes(&value).map_err(|e| format!("control-state-boxes: {e:?}"))?;
            if !canonical {
                writeln!(out, "result=control-state-boxes\nboxes={}", boxes.len())
                    .map_err(|e| e.to_string())?;
                for (i, b) in boxes.iter().take(8).enumerate() {
                    writeln!(
                        out,
                        "box{i}.fields={}\nbox{i}.valuePresent={}",
                        b.field_count(),
                        b.value().is_some()
                    )
                    .map_err(|e| e.to_string())?;
                }
                writeln!(out, "boxesShown={}", boxes.len().min(8)).map_err(|e| e.to_string())?;
            }
            Value::Array(boxes.iter().map(PlistValueBox::to_value).collect())
        } else {
            let b = PlistValueBox::decode(&value).map_err(|e| format!("plist-box: {e:?}"))?;
            if kind == "plist-box" {
                if !canonical {
                    writeln!(
                        out,
                        "result=plist-box\nfields={}\nvaluePresent={}",
                        b.field_count(),
                        b.value().is_some()
                    )
                    .map_err(|e| e.to_string())?;
                }
                b.to_value()
            } else {
                let decode = |v: &Value| match v {
                    Value::String(s) => Ok(s.clone()),
                    _ => Err("expected String"),
                };
                let value = if kind == "unbox-string" {
                    Some(
                        b.required_with(decode)
                            .map_err(|e| format!("unbox-string: {e:?}"))?,
                    )
                } else {
                    b.optional_with(decode)
                        .map_err(|e| format!("unbox-optional-string: {e}"))?
                };
                if !canonical {
                    let label = if kind == "unbox-string" {
                        "unbox-string"
                    } else {
                        "unbox-optional-string"
                    };
                    writeln!(out, "result={label}\nisPresent={}", value.is_some())
                        .map_err(|e| e.to_string())?;
                    string(&mut out, "value", value.as_deref()).map_err(|e| e.to_string())?;
                }
                let mut fields = std::collections::BTreeMap::new();
                fields.insert("isPresent".into(), Value::Boolean(value.is_some()));
                if let Some(value) = value {
                    fields.insert("value".into(), Value::String(value));
                }
                Value::Dictionary(fields)
            }
        }
    } else if kind == "render-effects" {
        // Original inspector input shape, not a recovered native wire payload.
        let Value::Dictionary(fields) = &value else {
            return Err("render-effects: expected dictionary".into());
        };
        let Some(Value::Array(values)) = fields.get("overrides") else {
            return Err("render-effects: required overrides array".into());
        };
        let overrides = values
            .iter()
            .enumerate()
            .map(|(i, v)| {
                PreviewVariant::decode(v)
                    .map_err(|e| format!("render-effects: override {i}: {e:?}"))
            })
            .collect::<Result<Vec<_>, _>>()?;
        let variant = fields
            .get("variant")
            .map(PreviewVariant::decode)
            .transpose()
            .map_err(|e| format!("render-effects: variant: {e:?}"))?;
        let effects = canvas_core::render_effects::assemble(&overrides, variant.as_ref());
        if !canonical {
            writeln!(out, "result=render-effects\neffects={}", effects.len())
                .map_err(|e| e.to_string())?;
            for (i, effect) in effects.iter().take(8).enumerate() {
                string(&mut out, &format!("effect{i}"), Some(&effect.id))
                    .map_err(|e| e.to_string())?;
            }
            writeln!(out, "effectsShown={}", effects.len().min(8)).map_err(|e| e.to_string())?;
        }
        Value::Array(effects.iter().map(|e| e.to_value()).collect())
    } else if kind == "group-variants" {
        let group =
            PreviewVariantGroup::decode(&value).map_err(|e| format!("group-variants: {e:?}"))?;
        let lists = [
            ("overrides", group.overrides_variants().to_vec()),
            ("grid", group.grid_variants()),
            ("all", group.all_variants()),
        ];
        if !canonical {
            writeln!(out, "result=group-variants").map_err(|e| e.to_string())?;
            for (key, values) in &lists {
                writeln!(out, "{key}={}", values.len()).map_err(|e| e.to_string())?;
                for (index, v) in values.iter().take(8).enumerate() {
                    string(&mut out, &format!("{key}{index}.id"), Some(&v.id))
                        .map_err(|e| e.to_string())?;
                    string(
                        &mut out,
                        &format!("{key}{index}.displayName"),
                        Some(&v.display_name),
                    )
                    .map_err(|e| e.to_string())?;
                }
                writeln!(out, "{key}Shown={}", values.len().min(8)).map_err(|e| e.to_string())?;
            }
        }
        Value::Dictionary(
            lists
                .into_iter()
                .map(|(key, values)| {
                    (
                        key.into(),
                        Value::Array(values.iter().map(PreviewVariant::to_value).collect()),
                    )
                })
                .collect(),
        )
    } else if kind == "default-selection" {
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
