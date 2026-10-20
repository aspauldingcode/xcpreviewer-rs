use canvas_core::{nserror_archive::{NSErrorDetails, Error}, service_error, workspace_action::WorkspaceActionCompletion};
use std::collections::BTreeMap;
#[test]
fn native_string_details_match_expected_fields() {
    let Ok(root) = std::env::var("XCPREVIEW_NATIVE_ERROR_DETAILS") else { return };
    let cases = [("single", "Owned.Info",17, vec![("NSLocalizedFailureReason","owned.reason")]), ("diagnostic","BSServiceConnectionErrorDomain",3,vec![("BSErrorCodeDescription","OperationFailed"),("NSLocalizedFailureReason","XPC error received on message reply handler")]), ("unicode","Owned.☃",-129,vec![("clé.☃","value.😀"),("second","other")]), ("empty","Owned.Empty",0,vec![]), ("holdout","Owned.Holdout.😀",256,vec![("detail","a different holdout value"),("status","ready")])];
    let mut total = 0;
    for (name,domain,code,info) in cases {
        let bytes = std::fs::read(std::path::Path::new(&root).join(format!("{name}.archive"))).unwrap();
        let expected: BTreeMap<_,_> = info.into_iter().map(|(k,v)|(k.to_owned(),v.to_owned())).collect();
        let decoded = NSErrorDetails::decode(&bytes).unwrap();
        assert_eq!(decoded.error.domain, domain); assert_eq!(decoded.error.code,code); assert_eq!(decoded.user_info,expected);
        let completion = WorkspaceActionCompletion { error_archive: Some(bytes.clone()) };
        assert_eq!(completion.decoded_error_details().unwrap(), Some(decoded));
        assert_eq!(completion.error_archive.as_ref(),Some(&bytes)); total += bytes.len();
    }
    assert_eq!(total,1260);
}
#[test]
fn native_diagnostic_archive_projects_to_service_error() {
    let Ok(root) = std::env::var("XCPREVIEW_NATIVE_ERROR_DETAILS") else { return };
    for name in ["diagnostic.archive", "actual-diagnostic.archive"] {
    let bytes = std::fs::read(std::path::Path::new(&root).join(name)).unwrap();
    let value = service_error::ServiceConnectionError::from_archive(&bytes).unwrap();
    assert_eq!(value.code,3); assert_eq!(value.failure_reason,"XPC error received on message reply handler"); assert!(value.additional_info.is_empty());
    }
}
#[test]
fn valid_native_numeric_value_is_explicitly_unsupported() {
    let Ok(root) = std::env::var("XCPREVIEW_NATIVE_ERROR_DETAILS") else { return };
    let bytes = std::fs::read(std::path::Path::new(&root).join("numeric.archive")).unwrap();
    assert_eq!(NSErrorDetails::decode(&bytes),Err(Error::UnsupportedUserInfo));
}
#[test]
fn native_truncations_and_unknown_reference_reject() {
    let Ok(root) = std::env::var("XCPREVIEW_NATIVE_ERROR_DETAILS") else { return };
    let bytes = std::fs::read(std::path::Path::new(&root).join("single.archive")).unwrap();
    for end in 0..bytes.len() { assert!(NSErrorDetails::decode(&bytes[..end]).is_err()); }
    let mut invalid = bytes.clone(); let at=invalid.windows(2).position(|v|v==[0x81,0x1f]).unwrap();invalid[at+1]=0xff;
    assert_eq!(NSErrorDetails::decode(&invalid),Err(Error::Profile));
    // Original hostile fixture: shared long string references amplify decoded
    // output far beyond input size. It is not presented as a native capture.
    let stress = std::fs::read(std::path::Path::new(&root).join("synthetic-reference-budget.archive")).unwrap();
    assert!(stress.len() < 1024*1024);
    assert_eq!(NSErrorDetails::decode(&stress), Err(Error::Limit));
}
