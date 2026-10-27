//! Inspect the recovered service-message subset without contacting a service.
use canvas_core::{
    binary_plist_writer,
    service_envelope::{ServiceContent, ServiceEnvelope},
    service_process::ProcessTarget,
};
use std::io::{Read, Write};

const INPUT_LIMIT: u64 = 64 * 1024 * 1024;
const USAGE: &str = "usage: inspect-service-message [--canonical|--prepare-update] INPUT.bplist|-";

// Bound human-readable strings independently of the binary input budget. Debug
// quoting escapes embedded newlines, NULs and other controls onto one line.
fn string(out: &mut impl Write, key: &str, value: Option<&str>) -> std::io::Result<()> {
    match value {
        None => writeln!(out, "{key}=absent"),
        Some(value) => {
            let preview: String = value.chars().take(256).collect();
            writeln!(out, "{key}={preview:?}")?;
            writeln!(out, "{key}Bytes={}", value.len())?;
            writeln!(out, "{key}Truncated={}", preview.len() < value.len())
        }
    }
}
fn process(out: &mut impl Write, target: &ProcessTarget) -> std::io::Result<()> {
    writeln!(out, "pid={}", target.pid())?;
    match target {
        ProcessTarget::Pid(_) => writeln!(out, "processRepresentation=pid"),
        ProcessTarget::AuditToken(words) => {
            writeln!(out, "processRepresentation=auditToken")?;
            writeln!(out, "auditToken={words:?}")
        }
    }
}
fn summary(out: &mut impl Write, envelope: &ServiceEnvelope) -> std::io::Result<()> {
    let kind = match &envelope.content {
        ServiceContent::Ping => "ping",
        ServiceContent::Variants(_) => "variants",
        ServiceContent::ContentOverride(_) => "contentOverride",
        ServiceContent::PrepareToRelaunch(_) => "prepareToRelaunch",
        ServiceContent::Capabilities(_) => "capabilities",
        ServiceContent::Connect(_) => "connect",
        ServiceContent::Stop(_) => "stop",
        ServiceContent::Kill(_) => "kill",
        ServiceContent::Forward(_) => "forward",
        ServiceContent::CancelUpdate(_) => "cancelUpdate",
        ServiceContent::Purge(_) => "purge",
    };
    writeln!(out, "messageType={kind}")?;
    string(out, "identifier", envelope.identifier.as_deref())?;
    match &envelope.content {
        ServiceContent::Ping => Ok(()),
        ServiceContent::Variants(value) => {
            string(out, "contentCategory", Some(&value.content_category))?;
            string(out, "contentOverride", value.content_override.as_deref())
        }
        ServiceContent::ContentOverride(value) => {
            string(out, "contentCategory", Some(&value.content_category))?;
            writeln!(
                out,
                "requestedOverrides={}",
                value.requested_overrides.len()
            )?;
            for (index, item) in value.requested_overrides.iter().take(8).enumerate() {
                string(out, &format!("requestedOverride{index}"), Some(item))?;
            }
            writeln!(
                out,
                "requestedOverridesShown={}",
                value.requested_overrides.len().min(8)
            )
        }
        ServiceContent::PrepareToRelaunch(value) => {
            string(
                out,
                "idAcrossRelaunches",
                Some(&value.agent_descriptor.id_across_relaunches),
            )?;
            string(
                out,
                "bundleID",
                Some(&value.agent_descriptor.bundle.bundle_id),
            )?;
            string(out, "path", value.agent_descriptor.bundle.path.as_deref())
        }
        ServiceContent::Capabilities(None) => writeln!(out, "capabilities=absent"),
        ServiceContent::Capabilities(Some(value)) => {
            writeln!(out, "isRunningInXTP={}", value.is_running_in_xtp)
        }
        ServiceContent::Connect(target)
        | ServiceContent::Stop(target)
        | ServiceContent::Kill(target) => process(out, target),
        ServiceContent::Purge(value) => {
            string(out, "workspaceID", Some(&value.workspace_id))?;
            writeln!(out, "killAgents={}", value.kill_agents)
        }
        ServiceContent::CancelUpdate(value) => {
            writeln!(out, "pid={}", value.pid)?;
            string(out, "contentIdentifier", Some(&value.content_identifier))?;
            writeln!(out, "updateSeed={}", value.update_seed)
        }
        ServiceContent::Forward(value) => {
            writeln!(out, "agentMessageType={}", value.message_type.as_str())?;
            writeln!(out, "pid={}", value.pid)?;
            string(out, "sceneIdentifier", value.scene_identifier.as_deref())?;
            string(
                out,
                "previewContextType",
                value.content_domain.map(|v| v.as_str()),
            )?;
            string(
                out,
                "previewInterfaceOrientation",
                value.preview_interface_orientation.map(|v| v.as_str()),
            )
        }
    }
}
fn run() -> Result<(), String> {
    let mut args = std::env::args_os().skip(1);
    let first = args.next().ok_or(USAGE)?;
    if first == "--help" && args.next().is_none() {
        println!("{USAGE}\nInspect values only. --canonical emits normalized bplist00 to stdout.\nUnknown fields are omitted; unsupported kinds reject. --prepare-update wraps a standalone shell value with a new process-local identifier. No service action runs.");
        return Ok(());
    }
    let prepare = first == "--prepare-update";
    let canonical = first == "--canonical" || prepare;
    let input = if canonical {
        args.next().ok_or(USAGE)?
    } else {
        first
    };
    if args.next().is_some() {
        return Err(USAGE.into());
    }
    let mut bytes = Vec::new();
    let reader: Box<dyn Read> = if input == "-" {
        Box::new(std::io::stdin())
    } else {
        Box::new(std::fs::File::open(input).map_err(|e| format!("input: {e}"))?)
    };
    reader
        .take(INPUT_LIMIT + 1)
        .read_to_end(&mut bytes)
        .map_err(|e| format!("input: {e}"))?;
    if bytes.len() as u64 > INPUT_LIMIT {
        return Err("input exceeds 64 MiB".into());
    }
    let value = canvas_core::binary_plist::decode(&bytes).map_err(|e| format!("decode: {e:?}"))?;
    if prepare {
        struct Preparation;
        impl canvas_core::shell_service::ShellServiceTransport for Preparation {
            type PendingReply = canvas_core::shell_service::ShellServiceEnvelope;
            fn send(&mut self, request: Self::PendingReply) -> Self::PendingReply { request }
        }
        let shell = canvas_core::shell_payload::ShellUpdatePayload::decode_single_entry_updates(&value)
            .map_err(|e| format!("shell: {e:?}"))?;
        let request = canvas_core::shell_service::dispatch_shell_update(&mut Preparation, shell);
        let bytes = request.to_binary_plist().map_err(|e| format!("encode: {e:?}"))?;
        let mut out = std::io::stdout().lock();
        out.write_all(&bytes).map_err(|e| format!("output: {e}"))?;
        return out.flush().map_err(|e| format!("output: {e}"));
    }
    if matches!(&value, canvas_core::payload_codec::Value::Dictionary(d)
        if matches!(d.get("messageType"), Some(canvas_core::payload_codec::Value::String(k)) if k == "update")) {
        let envelope = canvas_core::shell_service::ShellServiceEnvelope::decode_single_entry_updates(&value)
            .map_err(|e| format!("decode: {e:?}"))?;
        let mut out = std::io::stdout().lock();
        if canonical {
            out.write_all(&envelope.to_binary_plist().map_err(|e| format!("encode: {e:?}"))?)
                .map_err(|e| format!("output: {e}"))?;
        } else {
            writeln!(out, "messageType=update").map_err(|e| format!("output: {e}"))?;
            string(&mut out, "identifier", envelope.identifier.as_deref()).map_err(|e| format!("output: {e}"))?;
            writeln!(out, "staticProducts={}\nupdates={}", envelope.shell.static_products.len(), envelope.shell.setup_payload.updates.len())
                .map_err(|e| format!("output: {e}"))?;
        }
        return out.flush().map_err(|e| format!("output: {e}"));
    }
    let envelope = ServiceEnvelope::decode(&value).map_err(|e| format!("decode: {e:?}"))?;
    let mut out = std::io::stdout().lock();
    if canonical {
        let encoded = binary_plist_writer::encode(&envelope.to_value())
            .map_err(|e| format!("encode: {e:?}"))?;
        out.write_all(&encoded)
            .map_err(|e| format!("output: {e}"))?;
    } else {
        summary(&mut out, &envelope).map_err(|e| format!("output: {e}"))?;
    }
    out.flush().map_err(|e| format!("output: {e}"))
}
fn main() {
    if let Err(error) = run() {
        eprintln!("{error}");
        std::process::exit(1);
    }
}
