use canvas_core::agent_message_kind::AgentMessageKind as K;
#[test]
fn exact_native_domain_and_incremental_pairs() {
    let pairs = [
        ("previewInstances", "incrementalPreviewInstances"),
        ("render", "incrementalRender"),
        ("display", "incrementalDisplay"),
        ("layerHost", "incrementalLayerHost"),
        ("captureIOSurface", "incrementalCaptureIOSurface"),
    ];
    for (base, incremental) in pairs {
        let b=K::from_raw(base).unwrap(); let i=K::from_raw(incremental).unwrap();
        assert_eq!(b.as_str(),base); assert_eq!(i.as_str(),incremental);
        assert!(!b.is_incremental()); assert!(i.is_incremental());
        assert_eq!(b.incremental_variant(),i); assert_eq!(i.incremental_variant(),i);
    }
}
#[test]
fn unknown_and_near_match_commands_remain_unsupported() {
    for value in ["", "CaptureIOSurface", "captureIOSurface\0", "captureIOSurface ",
        "incremental", "incrementalCaptureIOSurface2", "rendér", "captureIOSurface/frame"] {
        assert_eq!(K::from_raw(value),None);
    }
}
