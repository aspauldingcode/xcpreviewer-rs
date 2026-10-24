use canvas_core::{payload_codec::Value, service_reply_error::ServiceReplyError, service_reply_failure::{self as reply, ObservedXpcError as Event, ServiceReplyInput as Input, ServiceReplyFailure as Failure, XpcFailure as X}, transport_reply::{acknowledge_reply, select_reply, ReplyError}};
use std::collections::BTreeMap;
#[test]
fn rejected_dictionary_and_other_types_preserve_full_description_in_error_callback() {
    let description="owned description 🪨\nsecond line";
    for input in [Input::RejectedDictionary {description:description.into()},Input::OtherType {description:description.into()}] {
        let (payload,error)=reply::classify_service_reply(input);
        assert_eq!(select_reply(payload,error),Err(ReplyError::Remote(Failure::Xpc(X::InvalidType(description.into())))));
    }
}
#[test]
fn interrupted_termination_invalidated_and_unknown_stay_distinct() {
    for (event,expected) in [
        (Event::ConnectionInterrupted,X::ConnectionInterrupted),
        (Event::TerminationImminent,X::TerminationImminent),
        (Event::ConnectionInvalidated {reason:Some("owned reason".into())},X::ConnectionInvalidated("owned reason".into())),
        (Event::Other {description:Some("owned event".into())},X::Unknown("owned event".into())),
    ] {
        let (p,e)=reply::classify_service_reply(Input::Error(event));
        assert_eq!(acknowledge_reply(p,e),Err(ReplyError::Remote(Failure::Xpc(expected))));
    }
}
#[test]
fn absent_descriptions_use_literal_while_empty_and_unicode_values_survive() {
    for (value,expected) in [(None,"<no description>"),(Some(""),""),(Some("owned 🪨"),"owned 🪨")] {
        assert_eq!(Event::ConnectionInvalidated {reason:value.map(str::to_owned)}.classify(),X::ConnectionInvalidated(expected.into()));
        assert_eq!(Event::Other {description:value.map(str::to_owned)}.classify(),X::Unknown(expected.into()));
    }
}
#[test]
fn decoded_dictionaries_compose_with_remote_schema_and_ordinary_payload() {
    let ordinary=BTreeMap::from([("bytes".into(),Value::Data((0..128).collect()))]);
    let (p,e)=reply::classify_service_reply(Input::DecodedDictionary(ordinary.clone()));
    assert_eq!(select_reply(p,e).unwrap().property_list(),Ok(ordinary));
    let remote=ServiceReplyError {domain:"owned".into(),code:i64::MIN,user_info:BTreeMap::new()};
    let (p,e)=reply::classify_service_reply(Input::DecodedDictionary(remote.to_dictionary()));
    assert_eq!(select_reply(p,e),Err(ReplyError::Remote(Failure::Remote(remote))));
}
#[test]
fn public_xpc_control_categories_feed_the_projected_classifier() {
    let fixture=include_str!("fixtures/service-reply-failure/categories.tsv");
    let mut seen=Vec::new();
    for row in fixture.lines() {
        let f:Vec<_>=row.split('\t').collect();assert_eq!(f.len(),4);assert_eq!(f[3],"1");seen.push(f[0]);
        let (input,expected)=match (f[1],f[2]) {
            ("error","connectionInterrupted") => (Input::Error(Event::ConnectionInterrupted),Some(X::ConnectionInterrupted)),
            ("error","connectionInvalidated") => (Input::Error(Event::ConnectionInvalidated {reason:None}),Some(X::ConnectionInvalidated("<no description>".into()))),
            ("error","terminationImminent") => (Input::Error(Event::TerminationImminent),Some(X::TerminationImminent)),
            ("other","none") => (Input::OtherType {description:"projected owned description".into()},Some(X::InvalidType("projected owned description".into()))),
            ("dictionary","none") => (Input::DecodedDictionary(BTreeMap::new()),None),
            _ => panic!("Unexpected native category")
        };
        let (p,e)=reply::classify_service_reply(input);
        if let Some(expected)=expected {assert!(p.is_none());assert_eq!(e,Some(Failure::Xpc(expected)));}
        else {assert!(p.is_some());assert!(e.is_none());}
    }
    assert_eq!(seen,vec!["interrupted","invalidated","termination","integer","string","boolean","null","array","dictionary"]);
}
