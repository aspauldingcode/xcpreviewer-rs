use canvas_core::{
    binary_plist,
    error_archive::{ErrorArchive as A, Limits},
    error_presentation::Error,
    payload_codec::Value as V,
};
// Formatting fixtures are direct canonical values, not remote decoder inputs.
// The remote decoder separately normalizes errorTypeDescription with [Remote].
fn fixture(fields: &std::collections::BTreeMap<String, V>) -> A {
    if let (Some(V::Dictionary(main)), Some(V::Dictionary(cause))) =
        (fields.get("main"), fields.get("underlying"))
    {
        return A::Wrapper {
            main: Box::new(fixture(main)),
            underlying: Box::new(fixture(cause)),
        };
    }
    let mut leaf = canvas_core::remote_error::RemoteErrorLeaf::from_dictionary(fields).unwrap();
    let V::String(description) = &fields["errorTypeDescription"] else {
        panic!()
    };
    leaf.error_type_description = description.clone();
    A::Leaf(leaf)
}
fn leaf(text: &str) -> A {
    fixture(&std::collections::BTreeMap::from([
        ("errorType".into(), V::String("leaf".into())),
        ("errorTypeDescription".into(), V::String(text.into())),
    ]))
}
#[test]
fn complete_public_foundation_text_controls() {
    let V::Array(rows) =
        binary_plist::decode(include_bytes!("fixtures/full-diagnostics/native.bplist")).unwrap()
    else {
        panic!()
    };
    assert_eq!(rows.len(), 9);
    for row in rows {
        let V::Dictionary(row) = row else { panic!() };
        let V::Dictionary(archive) = &row["archive"] else {
            panic!()
        };
        let result = fixture(archive).full_diagnostics().unwrap();
        assert_eq!(V::String(result.clone()), row["result"]);
        assert_eq!(V::Data(result.into_bytes()), row["utf8"]);
    }
}
#[test]
fn exact_work_and_tree_budgets() {
    let a = leaf("x");
    assert_eq!(
        a.full_diagnostics_with_limits(Limits { nodes: 1, depth: 0 }, 2),
        Ok("x".into())
    );
    assert_eq!(
        a.full_diagnostics_with_limits(Limits { nodes: 1, depth: 0 }, 1),
        Err(Error::ByteLimit)
    );
    assert_eq!(
        a.full_diagnostics_with_limits(Limits { nodes: 0, depth: 0 }, 100),
        Err(Error::TreeLimit)
    );
    let w = A::Wrapper {
        main: Box::new(leaf("")),
        underlying: Box::new(leaf("")),
    };
    let s = w.full_diagnostics().unwrap();
    assert!(s.ends_with("\n\n|  "));
    assert_eq!(
        w.full_diagnostics_with_limits(Limits { nodes: 3, depth: 1 }, s.len()),
        Ok(s.clone())
    );
    assert_eq!(
        w.full_diagnostics_with_limits(Limits { nodes: 3, depth: 1 }, s.len() - 1),
        Err(Error::ByteLimit)
    );
    assert_eq!(
        w.full_diagnostics_with_limits(Limits { nodes: 3, depth: 0 }, 1000),
        Err(Error::TreeLimit)
    );
}
#[test]
fn wrapper_uses_child_reports_not_aggregate_presentation() {
    let a = A::Wrapper {
        main: Box::new(leaf("main")),
        underlying: Box::new(leaf("cause\n")),
    };
    let s = a.full_diagnostics().unwrap();
    assert!(s.starts_with("main\n\n===="));
    assert!(s.ends_with("|  cause\n|  "));
    assert!(!s.starts_with("main.cause"));
    let nested = A::Wrapper {
        main: Box::new(leaf("")),
        underlying: Box::new(a),
    };
    assert!(nested
        .full_diagnostics()
        .unwrap()
        .ends_with("|  |  cause\n|  |  "));
}

#[test]
fn measured_fixed_escape_scalar_boundaries() {
    let V::Dictionary(fields) = binary_plist::decode(include_bytes!(
        "fixtures/full-diagnostics/boundaries.bplist"
    ))
    .unwrap() else {
        panic!()
    };
    assert_eq!(fields["tested"], V::Integer(1112064));
    let V::Array(ranges) = &fields["rejected"] else {
        panic!()
    };
    assert_eq!(ranges.len(), 384);
    let ranges: Vec<(u32, u32)> = ranges
        .iter()
        .map(|r| {
            let V::Array(p) = r else { panic!() };
            let (V::Integer(a), V::Integer(b)) = (&p[0], &p[1]) else {
                panic!()
            };
            (*a as u32, *b as u32)
        })
        .collect();
    for &(a, b) in &ranges {
        for n in [a.saturating_sub(1), a, b, b + 1] {
            if let Some(c) = char::from_u32(n) {
                let suffix = format!("{c}x");
                let raw = format!("\\n{suffix}");
                let blocked = ranges.iter().any(|&(a, b)| a <= n && n <= b);
                let expected = if blocked {
                    raw.clone()
                } else {
                    format!("\n{suffix}")
                };
                assert_eq!(
                    leaf(&raw).full_diagnostics().unwrap(),
                    expected,
                    "scalar U+{n:04X}"
                );
            }
        }
    }
}
