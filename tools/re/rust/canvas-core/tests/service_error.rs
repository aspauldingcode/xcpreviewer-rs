use canvas_core::{service_error::{self, ServiceConnectionError as Failure}, settings_xpc::XpcValue as X, xpc_wire};
use std::collections::BTreeMap;
fn info() -> X { X::Dictionary(BTreeMap::from([
    ("BSErrorCodeDescription".into(), X::String("OperationFailed".into())),
    ("NSLocalizedFailureReason".into(), X::String("XPC error received on message reply handler".into())),
])) }
#[test]
fn reply_operation_error_is_distinct_from_connection_invalidation() {
    let failure=Failure::from_fields(service_error::DOMAIN,3,&info()).unwrap();
    assert_eq!(failure.to_user_info(),info());
    assert_eq!(service_error::code_description(2),"ConnectionInvalidated");
    assert_eq!(service_error::code_description(failure.code),"OperationFailed");
    assert!(Failure::from_fields(service_error::DOMAIN,2,&info()).is_err());
}
#[test]
fn wrong_domain_and_missing_or_mistyped_reserved_fields_reject() {
    assert!(Failure::from_fields("Other.Domain",3,&info()).is_err());
    assert!(Failure::from_fields(service_error::DOMAIN,3,&X::Null).is_err());
    let X::Dictionary(base)=info() else { unreachable!() };
    for key in ["BSErrorCodeDescription","NSLocalizedFailureReason"] {
        let mut d=base.clone();d.remove(key);
        assert!(Failure::from_fields(service_error::DOMAIN,3,&X::Dictionary(d.clone())).is_err());
        d.insert(key.into(),X::UInt64(3));
        assert!(Failure::from_fields(service_error::DOMAIN,3,&X::Dictionary(d)).is_err());
    }
}
#[test]
fn unknown_codes_preserve_identity_and_factory_reserved_keys_override_extras() {
    for code in [-1,5,i64::MIN,i64::MAX] {
        let e=Failure{code,failure_reason:"owned reason".into(),additional_info:BTreeMap::from([
            ("owned.extra".into(),X::Data(vec![0,1,255])),
            ("BSErrorCodeDescription".into(),X::String("spoofed".into())),
            ("NSLocalizedFailureReason".into(),X::Null),
        ])};
        let decoded=Failure::from_fields(service_error::DOMAIN,code,&e.to_user_info()).unwrap();
        assert_eq!(decoded.code,code);assert_eq!(decoded.failure_reason,"owned reason");
        assert_eq!(decoded.additional_info.len(),1);assert_eq!(service_error::code_description(code),"(unknown)");
    }
}
#[test]
fn actual_native_error_fields_when_supplied() {
    let Some(folder)=std::env::var_os("XCPREVIEW_NATIVE_SERVICE_ERROR_FIELDS") else { return };
    let folder=std::path::PathBuf::from(folder);
    let domain=std::fs::read_to_string(folder.join("domain.txt")).unwrap();
    let code=std::fs::read_to_string(folder.join("code.txt")).unwrap().parse::<i64>().unwrap();
    let body=std::fs::read(folder.join("user-info.body")).unwrap();
    // Authored fixture encodes actual SDK-observed userInfo fields. This is
    // explicitly not a captured native NSError wire representation.
    let table=std::fs::read_to_string(folder.join("code-table.txt")).unwrap();
    let names:Vec<_>=table.lines().collect();assert_eq!(names.len(),6);
    for (code,name) in names[..5].iter().enumerate() { assert_eq!(service_error::code_description(code as i64),*name); }
    assert_eq!(service_error::code_description(-1),names[5]);
    assert_eq!(service_error::code_description(5),names[5]);
    let value=xpc_wire::decode_body(&body).unwrap();let e=Failure::from_fields(&domain,code,&value).unwrap();
    assert_eq!(code,3);assert_eq!(e.failure_reason,"XPC error received on message reply handler");
    assert!(e.additional_info.is_empty());assert_eq!(e.to_user_info(),value);
    eprintln!("verified actual native error3 fields; authored field fixture, not native NSError wire");
}
