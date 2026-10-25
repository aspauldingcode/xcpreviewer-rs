//! Projected counterpart of the measured NSError UVObjCAdditions factory.
//! Native object identity, subclass overrides and Swift boxing are not modeled.
use crate::{
    error_archive::{Error, ErrorArchive, Limits},
    human_readable_error::ARCHIVE_KEY,
    payload_codec::Value,
    service_reply_error::ServiceReplyError,
};
use std::collections::BTreeMap;
pub const DOMAIN: &str = "com.apple.Previews";
pub const CODE: i64 = -1;
pub const DEFAULT_DESCRIPTION: &str = "Unexpected preview error";
/// Exact value fields from NSError.uv_errorWithUserInfo: on NSError itself.
/// No key is synthesized or removed and no localization is performed.
pub fn with_user_info(user_info: BTreeMap<String, Value>) -> ServiceReplyError {
    ServiceReplyError {
        domain: DOMAIN.into(),
        code: CODE,
        user_info,
    }
}
fn first_title(archive: &ErrorArchive, high: bool, limits: Limits) -> Result<Option<&str>, Error> {
    let mut nodes = limits.nodes;
    let mut pending = vec![(archive, 0usize)];
    while let Some((node, depth)) = pending.pop() {
        if nodes == 0 || depth > limits.depth {
            return Err(Error::Limit);
        }
        nodes -= 1;
        match node {
            ErrorArchive::Wrapper { main, underlying } => {
                pending.push((underlying, depth + 1));
                pending.push((main, depth + 1));
            }
            ErrorArchive::Leaf(leaf) => {
                let value = if high {
                    &leaf.high_value_title
                } else {
                    &leaf.low_value_title
                };
                if let Some(text) = value {
                    return Ok(Some(text));
                }
            }
        }
    }
    Ok(None)
}
/// Build the source-guided supported serializableNSError value: high title,
/// else low title, else the fixed fallback, plus the complete encoded archive.
/// Empty titles remain present. Metadata contains exactly the two native keys.
/// It does not run the native Swift getter or implement NSError localization.
pub fn from_archive(archive: &ErrorArchive) -> Result<ServiceReplyError, Error> {
    from_archive_with_limits(archive, Limits::default())
}
/// Original tree budgets apply independently to title lookup and archive encode.
/// Total string/serialized-byte budgets remain the separate writer's policy.
pub fn from_archive_with_limits(
    archive: &ErrorArchive,
    limits: Limits,
) -> Result<ServiceReplyError, Error> {
    let title = match first_title(archive, true, limits)? {
        Some(text) => text,
        None => first_title(archive, false, limits)?.unwrap_or(DEFAULT_DESCRIPTION),
    };
    let fields = archive.to_dictionary_with_limits(limits)?;
    Ok(with_user_info(BTreeMap::from([
        ("NSLocalizedDescription".into(), Value::String(title.into())),
        (ARCHIVE_KEY.into(), Value::Dictionary(fields)),
    ])))
}
