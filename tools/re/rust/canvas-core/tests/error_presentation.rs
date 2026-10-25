use canvas_core::{
    binary_plist,
    error_archive::{ErrorArchive as A, Limits},
    error_presentation::Error,
    payload_codec::Value as V,
    remote_error::{RemoteErrorLeaf as L, Severity},
};
fn leaf(name: &str) -> L {
    L {
        error_type_description: name.into(),
        high_value_title: None,
        low_value_title: None,
        additional_info: None,
        additional_diagnostics: None,
        options: None,
        severity: None,
        is_potential_crash: false,
        is_native: false,
    }
}
fn wrap(a: L, b: L) -> A {
    A::Wrapper {
        main: Box::new(A::Leaf(a)),
        underlying: Box::new(A::Leaf(b)),
    }
}
#[test]
fn main_present_empty_zero_and_info_beat_cause_values() {
    let mut a = leaf("a");
    a.high_value_title = Some("".into());
    a.options = Some(0);
    a.severity = Some(Severity::Info);
    let mut b = leaf("b");
    b.high_value_title = Some("cause".into());
    b.low_value_title = Some("low".into());
    b.options = Some(-1);
    b.severity = Some(Severity::Error);
    let p = wrap(a, b).presentation().unwrap();
    assert_eq!(p.high_value_title, Some("".into()));
    assert_eq!(p.low_value_title, Some("low".into()));
    assert_eq!(p.options, Some(0));
    assert_eq!(p.severity, Some(Severity::Info));
}
#[test]
fn foundation_format_fixture_preserves_optional_presence_and_utf8() {
    let V::Array(rows) =
        binary_plist::decode(include_bytes!("fixtures/wrapper-properties/format.bplist")).unwrap()
    else {
        panic!()
    };
    for row in rows {
        let V::Dictionary(f) = row else { panic!() };
        let string = |key: &str| {
            let V::String(s) = &f[key] else { panic!() };
            s.clone()
        };
        let boolean = |key: &str| {
            let V::Boolean(v) = f[key] else { panic!() };
            v
        };
        let mut a = leaf("a");
        let mut b = leaf("b");
        a.additional_info = boolean("mainPresent").then(|| string("main"));
        b.additional_info = boolean("causePresent").then(|| string("cause"));
        let p = wrap(a, b).presentation().unwrap();
        assert_eq!(
            p.additional_info,
            boolean("present").then(|| string("result"))
        );
        let V::Data(bytes) = &f["utf8"] else { panic!() };
        assert_eq!(p.additional_info.as_deref().unwrap_or("").as_bytes(), bytes);
    }
}
#[test]
fn descriptions_join_with_period_and_wrapper_diagnostics_stay_absent() {
    let mut a = leaf("first\0🪨");
    a.additional_diagnostics = Some("main diag".into());
    let mut b = leaf("second");
    b.additional_diagnostics = Some("cause diag".into());
    assert_eq!(
        A::Leaf(a.clone())
            .presentation()
            .unwrap()
            .additional_diagnostics,
        Some("main diag".into())
    );
    let p = wrap(a, b).presentation().unwrap();
    assert_eq!(p.error_type_description, "first\0🪨.second");
    assert_eq!(p.additional_diagnostics, None);
}
#[test]
fn presentation_budgets_cover_tree_and_total_returned_utf8() {
    let mut a = leaf("abc");
    a.high_value_title = Some("de".into());
    let a = A::Leaf(a);
    assert_eq!(
        a.presentation_with_limits(Limits { nodes: 1, depth: 0 }, 4),
        Err(Error::ByteLimit)
    );
    assert_eq!(
        a.presentation_with_limits(Limits { nodes: 1, depth: 0 }, 5)
            .unwrap()
            .high_value_title,
        Some("de".into())
    );
    let tree = A::Wrapper {
        main: Box::new(a.clone()),
        underlying: Box::new(a),
    };
    for limits in [Limits { nodes: 2, depth: 1 }, Limits { nodes: 3, depth: 0 }] {
        assert_eq!(
            tree.presentation_with_limits(limits, 100),
            Err(Error::TreeLimit)
        );
    }
}
#[test]
fn nested_algebra_preserves_main_subtree_precedence_and_flag_routes() {
    let mut a = leaf("a");
    a.additional_info = None;
    let mut b = leaf("b");
    b.high_value_title = Some("".into());
    b.additional_info = Some("".into());
    b.options = Some(0);
    b.severity = Some(Severity::Info);
    let mut c = leaf("c");
    c.high_value_title = Some("outer cause".into());
    c.additional_info = Some("c".into());
    c.options = Some(9);
    c.severity = Some(Severity::Error);
    c.is_native = true;
    c.is_potential_crash = true;
    let tree = A::Wrapper {
        main: Box::new(wrap(a, b)),
        underlying: Box::new(A::Leaf(c)),
    };
    let p = tree.presentation().unwrap();
    assert_eq!(p.error_type_description, "a.b.c");
    assert_eq!(p.additional_info, Some(": c".into()));
    assert_eq!(p.high_value_title, Some("".into()));
    assert_eq!(p.options, Some(0));
    assert_eq!(p.severity, Some(Severity::Info));
    assert_eq!(p.is_native, tree.is_native());
    assert_eq!(p.is_potential_crash, tree.is_potential_crash());
}
