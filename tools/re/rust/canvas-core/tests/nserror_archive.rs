use canvas_core::{nserror_archive::{ArchivedNSError, Error}, workspace_action::WorkspaceActionCompletion};
#[test]
fn native_archives_match_independent_fields_and_all_bytes() {
    let Ok(root) = std::env::var("XCPREVIEW_NATIVE_ERROR_ARCHIVES") else { return };
    let cases = [("primary", "Owned.Reply", 17), ("unicode", "Owned.Reply.☃", 29), ("negative", "Owned.Negative", -129), ("zero", "", 0), ("wide16", "Owned.Wide", 256), ("wide32", "Owned.Wide", 65536), ("max", "Owned.Maximum.Domain.Long", i64::MAX), ("min", "Owned.Minimum.😀", i64::MIN), ("len15", "123456789012345", 255), ("holdout", "Holdout.é🦀", 65535)];
    let mut total = 0;
    for (name, domain, code) in cases {
        let bytes = std::fs::read(std::path::Path::new(&root).join(format!("{name}.archive"))).unwrap();
        let expected = ArchivedNSError { domain: domain.into(), code };
        assert_eq!(ArchivedNSError::decode(&bytes).unwrap(), expected);
        assert_eq!(expected.encode().unwrap(), bytes);
        let completion = WorkspaceActionCompletion { error_archive: Some(bytes.clone()) };
        assert_eq!(completion.decoded_error().unwrap(), Some(expected)); total += bytes.len();
    }
    assert_eq!(total, 1102);
}
#[test]
fn absent_and_unsupported_archives_remain_distinct() {
    assert_eq!(WorkspaceActionCompletion::default().decoded_error().unwrap(), None);
    let bad = WorkspaceActionCompletion { error_archive: Some(b"bplist00".to_vec()) };
    assert_eq!(bad.decoded_error(), Err(Error::Profile));
    assert_eq!(bad.error_archive.as_deref(), Some(&b"bplist00"[..]));
    if let Ok(root) = std::env::var("XCPREVIEW_NATIVE_ERROR_ARCHIVES") {
        let bytes = std::fs::read(std::path::Path::new(&root).join("with_info.archive")).unwrap();
        assert_eq!(ArchivedNSError::decode(&bytes), Err(Error::UnsupportedUserInfo));
    }
}
#[test]
fn truncation_bad_offsets_and_non_nil_userinfo_reject() {
    let valid = ArchivedNSError { domain: "Owned.Reply".into(), code: 17 }.encode().unwrap();
    for end in 0..valid.len() { assert!(ArchivedNSError::decode(&valid[..end]).is_err()); }
    for offset in [9, 23] { let mut b = valid.clone(); b[offset] ^= 1; assert_eq!(ArchivedNSError::decode(&b), Err(Error::Profile)); }
    let mut b = valid.clone(); *b.last_mut().unwrap() = 0; assert_eq!(ArchivedNSError::decode(&b), Err(Error::UnsupportedUserInfo));
}
#[test]
fn hostile_lengths_and_invalid_utf16_reject() {
    let mut b = ArchivedNSError { domain: "x".into(), code: 17 }.encode().unwrap();
    let at = b.windows(10).position(|v| v == b"\x79NSDomain\0").unwrap() + 11;
    b[at] = 0; b[at+1] = 0xd8; assert_eq!(ArchivedNSError::decode(&b), Err(Error::Utf16));
    assert_eq!(ArchivedNSError { domain: "x".repeat(65537), code: 0 }.encode(), Err(Error::Limit));
    assert_eq!(ArchivedNSError::decode(&vec![0; 1024*1024+1]), Err(Error::Limit));
}
