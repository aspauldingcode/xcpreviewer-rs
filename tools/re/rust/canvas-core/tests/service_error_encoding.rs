use canvas_core::{binary_plist, payload_codec::Value, service_reply_error::{ServiceReplyError, split_dictionary_reply}};
use std::collections::BTreeMap;
fn info() -> BTreeMap<String, Value> {
    BTreeMap::from([
        ("bytes".into(), Value::Data((0..128).collect())),
        ("nested".into(), Value::Dictionary(BTreeMap::from([
            ("ok".into(), Value::Boolean(true)),
            ("name".into(), Value::String("owned/🪨".into())),
        ]))),
        ("items".into(), Value::Array(vec![Value::String("first".into()),Value::String("second".into())])),
    ])
}
#[test]
fn outbound_dictionary_matches_four_public_foundation_controls() {
    for (domain,code,user_info,bytes) in [
        ("",0,BTreeMap::new(),include_bytes!("fixtures/service-error-encoding/empty.bplist").as_slice()),
        ("owned/error/🪨",-17,info(),include_bytes!("fixtures/service-error-encoding/negative.bplist").as_slice()),
        ("owned/min",i64::MIN,info(),include_bytes!("fixtures/service-error-encoding/min.bplist").as_slice()),
        ("owned/max",i64::MAX,info(),include_bytes!("fixtures/service-error-encoding/max.bplist").as_slice()),
    ] {
        let error=ServiceReplyError {domain:domain.into(),code,user_info};
        let expected=binary_plist::decode(bytes).unwrap();
        assert_eq!(Value::Dictionary(error.to_dictionary()),expected);
        assert_eq!(split_dictionary_reply(error.to_dictionary()),(None,Some(error)));
    }
}
#[test]
fn encoded_values_own_all_nested_data_and_never_add_error_marker() {
    let error=ServiceReplyError {domain:"owned".into(),code:-17,user_info:info()};
    let mut fields=error.to_dictionary();
    assert_eq!(fields.keys().map(String::as_str).collect::<Vec<_>>(),vec!["code","domain","userInfo"]);
    let Value::Dictionary(ref mut copied)=fields.get_mut("userInfo").unwrap() else {panic!()};
    copied.clear();
    assert_eq!(error.user_info,info());
    assert_eq!(error.to_dictionary()["userInfo"],Value::Dictionary(info()));
}
