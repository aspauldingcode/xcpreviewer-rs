use canvas_core::{binary_plist, payload_codec::Value, service_reply_error::{ServiceReplyError, split_dictionary_reply}};
use std::collections::BTreeMap;
fn original(domain:&str,code:i64) -> ServiceReplyError {
    ServiceReplyError {domain:domain.into(),code,user_info:BTreeMap::from([
        ("owned.extra".into(),Value::Data((0..128).collect())),
        ("NSLocalizedDescription".into(),Value::String("old description".into())),
        ("NSDebugDescription".into(),Value::String("old debug".into())),
    ])}
}
#[test]
fn empty_encoding_retry_matches_public_foundation_projections() {
    for (domain,code,bytes) in [
        ("owned/fallback/🪨",-17,include_bytes!("fixtures/service-error-fallback/negative.bplist").as_slice()),
        ("owned/min",i64::MIN,include_bytes!("fixtures/service-error-fallback/min.bplist").as_slice()),
        ("owned/max",i64::MAX,include_bytes!("fixtures/service-error-fallback/max.bplist").as_slice()),
    ] {
        let e=original(domain,code);
        let retry=e.retry_dictionary_if_empty(0,"owned failure 🪨").unwrap();
        assert_eq!(Value::Dictionary(retry.clone()),binary_plist::decode(bytes).unwrap());
        let (payload,error)=split_dictionary_reply(retry);
        assert!(payload.is_none());let received=error.unwrap();
        assert_eq!(received.domain,e.domain);assert_eq!(received.code,e.code);
        assert_eq!(received.user_info.len(),2);assert!(!received.user_info.contains_key("owned.extra"));
        assert_eq!(e.user_info["owned.extra"],Value::Data((0..128).collect()));
    }
}
#[test]
fn any_nonempty_encoded_destination_skips_retry_even_if_partial() {
    let e=original("owned",3);
    for count in [1,2,3,usize::MAX] {
        assert_eq!(e.retry_dictionary_if_empty(count,"ignored"),None);
    }
}
#[test]
fn retry_uses_supplied_description_and_does_not_merge_or_mutate_original_info() {
    let e=original("",0);let saved=e.clone();
    let mut retry=e.retry_dictionary_if_empty(0,"").unwrap();
    let Value::Dictionary(ref mut info)=retry.get_mut("userInfo").unwrap() else {panic!()};
    assert_eq!(info["NSLocalizedDescription"],Value::String("".into()));
    assert_eq!(info["NSDebugDescription"],Value::String("Failed to encode full userInfo due to incompatible types".into()));
    assert_eq!(info.len(),2);info.clear();assert_eq!(e,saved);
    assert_eq!(retry["domain"],Value::String("".into()));assert_eq!(retry["code"],Value::Integer(0));
}
