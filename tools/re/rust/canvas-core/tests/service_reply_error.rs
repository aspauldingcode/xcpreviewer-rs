use canvas_core::{payload_codec::Value, service_reply_error::{ServiceReplyError, split_dictionary_reply}, transport_reply::{select_reply, acknowledge_reply, ReplyError}};
use std::collections::BTreeMap;
fn fields() -> BTreeMap<String, Value> {
    BTreeMap::from([
        ("domain".into(), Value::String("owned/error/🪨".into())),
        ("code".into(), Value::Integer(-17)),
        ("userInfo".into(), Value::Dictionary(BTreeMap::from([
            ("bytes".into(), Value::Data((0..128).collect())),
            ("reason".into(), Value::String("owned failure".into())),
        ]))),
    ])
}
#[test]
fn complete_error_fields_map_to_error_callback_and_keep_all_user_info() {
    let d = fields();
    let e = ServiceReplyError::recognize(&d).unwrap();
    assert_eq!(e.domain, "owned/error/🪨"); assert_eq!(e.code, -17);
    assert_eq!(Value::Dictionary(e.user_info.clone()), d["userInfo"]);
    let (p, error) = split_dictionary_reply(d);
    assert_eq!(select_reply(p, error), Err(ReplyError::Remote(e.clone())));
    let (p, error) = split_dictionary_reply(fields());
    assert_eq!(acknowledge_reply(p, error), Err(ReplyError::Remote(e)));
}
#[test]
fn missing_or_wrong_fields_remain_payload_instead_of_becoming_empty_reply() {
    for key in ["domain", "code", "userInfo"] {
        let mut d = fields(); d.remove(key);
        let (p, e) = split_dictionary_reply(d.clone());
        assert!(e.is_none()); assert_eq!(select_reply(p, e).unwrap().property_list(), Ok(d));
    }
    for (key, bad) in [("domain", Value::Integer(1)), ("code", Value::String("3".into())), ("userInfo", Value::Array(vec![]))] {
        let mut d = fields(); d.insert(key.into(), bad);
        assert!(ServiceReplyError::recognize(&d).is_none());
        let (p, e) = split_dictionary_reply(d.clone());
        assert_eq!(select_reply(p, e).unwrap().property_list(), Ok(d));
    }
}
#[test]
fn no_marker_required_and_extra_fields_do_not_hide_error_shape() {
    let mut d = fields(); d.insert("messageType".into(), Value::String("ordinary".into()));
    assert!(ServiceReplyError::recognize(&d).is_some());
    d.insert("domain".into(), Value::String(String::new())); d.insert("code".into(), Value::Integer(0));
    d.insert("userInfo".into(), Value::Dictionary(BTreeMap::new()));
    assert_eq!(ServiceReplyError::recognize(&d).unwrap().code, 0);
}
#[test]
fn measured_foundation_numeric_coercions_and_nonmatching_values() {
    for (value, expected) in [(Value::Boolean(true), Some(1)), (Value::Boolean(false), Some(0)), (Value::Real(3.0), Some(3)), (Value::Real(-0.0), Some(0)), (Value::Real(3.5), None), (Value::Real(f64::NAN), None), (Value::Real(f64::INFINITY), None), (Value::Real(9223372036854775808.0), Some(i64::MAX)), (Value::Real(-9223372036854775808.0), Some(i64::MIN))] {
        let mut d = fields();d.insert("code".into(), value);
        assert_eq!(ServiceReplyError::recognize(&d).map(|e|e.code), expected);
    }
    for n in [i64::MIN, i64::MAX] {
        let mut d = fields();d.insert("code".into(), Value::Integer(n));assert_eq!(ServiceReplyError::recognize(&d).unwrap().code,n);
    }
}
#[test]
fn classification_owns_user_info_and_preserves_ordinary_dictionary() {
    let d = fields();let mut e = ServiceReplyError::recognize(&d).unwrap();e.user_info.clear();
    assert_eq!(ServiceReplyError::recognize(&d).unwrap().user_info.len(),2);
    let ordinary = BTreeMap::from([("data".into(),Value::Data((0..128).collect()))]);
    let (p,e)=split_dictionary_reply(ordinary.clone());assert_eq!(select_reply(p,e).unwrap().property_list(),Ok(ordinary));
}

#[test]
fn all_representable_numeric_cases_match_independent_swift_fixture() {
    let high = 9223372036854775808.0f64;
    let low = -9223372036854775808.0f64;
    let cases = BTreeMap::from([
        ("above_real_max", Value::Real(high)), ("bool", Value::Boolean(true)),
        ("false", Value::Boolean(false)), ("fraction", Value::Real(3.5)),
        ("high_next_up", Value::Real(f64::from_bits(high.to_bits()+1))),
        ("huge_real", Value::Real(18446744073709551616.0)),
        ("infinity", Value::Real(f64::INFINITY)), ("integer", Value::Integer(-17)),
        ("integral_real", Value::Real(3.0)),
        ("low_next_down", Value::Real(f64::from_bits(low.to_bits()+1))),
        ("max_integer", Value::Integer(i64::MAX)), ("min_integer", Value::Integer(i64::MIN)),
        ("min_real", Value::Real(low)), ("nan", Value::Real(f64::NAN)),
        ("negative_zero", Value::Real(-0.0)), ("string", Value::String("3".into())),
    ]);
    let mut actual=String::new();
    for (name,value) in cases {
        let mut d=fields();d.insert("code".into(),value);
        let code=ServiceReplyError::recognize(&d).map_or("none".into(), |e|e.code.to_string());
        actual.push_str(&format!("{name}\t{code}\n"));
    }
    assert_eq!(actual,include_str!("fixtures/service-reply-error/coercions.tsv"));
}
