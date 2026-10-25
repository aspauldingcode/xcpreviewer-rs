//! Encoded human-readable error extraction from projected NSError userInfo.
//! The archive decoder remains explicit: remote/underlying schema, native Error
//! conformances and NSError boxing are not reproduced by this value adapter.
use crate::payload_codec::Value;
use std::collections::BTreeMap;

pub const ARCHIVE_KEY: &str = "UVHumanReadableError";

/// Look up the exact native archive key and require a string-key dictionary.
/// Missing/wrong-type values skip unarchive. An empty dictionary still reaches
/// it. Unarchive failure is suppressed so the caller can use its generic error
/// fallback. The original map is borrowed unchanged, including unknown fields.
///
/// Value already projects string-key dictionaries. Foundation's broader Any
/// bridging/coercions and native diagnostic logging remain outside this API.
/// No fallback error is synthesized; None is only absence of a decoded archive.
pub fn extract_encoded_with<T, E>(
    user_info: &BTreeMap<String, Value>,
    unarchive: impl FnOnce(&BTreeMap<String, Value>) -> Result<T, E>,
) -> Option<T> {
    let Value::Dictionary(fields) = user_info.get(ARCHIVE_KEY)? else {
        return None;
    };
    unarchive(fields).ok()
}
