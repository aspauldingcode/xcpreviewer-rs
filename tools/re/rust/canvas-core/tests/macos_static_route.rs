use canvas_core::{
    agent_message_kind::AgentMessageKind as K,
    iosurface_payload::IOSurfacePayload,
    macos_static_route::{Error, MacOSStaticRenderingMethod as M},
    payload_codec::Value,
};
#[test]
fn static_request_and_reply_routes_are_paired() {
    assert_eq!(M::LayerHost.request_kind(), K::LayerHost);
    assert_eq!(M::IOSurface.request_kind(), K::CaptureIOSurface);
    assert!(!M::IOSurface.request_kind().is_incremental());
    let payload=IOSurfacePayload { surface_id:12345, scale_factor:2.0,
        width:1.5, height:1.0, selectable_regions:vec![] };
    let value=payload.to_value();
    assert_eq!(M::IOSurface.decode_surface_reply(&value),Ok(payload));
    assert_eq!(M::LayerHost.decode_surface_reply(&value),Err(Error::UnsupportedLayerHost));
}
#[test]
fn unsupported_layer_route_never_falls_back_and_surface_errors_propagate() {
    for invalid in [Value::Null,Value::String("layerHost".into()),Value::Integer(0)] {
        assert_eq!(M::LayerHost.decode_surface_reply(&invalid),Err(Error::UnsupportedLayerHost));
        assert!(matches!(M::IOSurface.decode_surface_reply(&invalid),Err(Error::Surface(_))));
    }
}

#[test]
fn macos_override_preserves_hosted_default() {
    for method in [M::LayerHost, M::IOSurface] {
        let messages=method.legacy_messages();
        assert_eq!(messages.hosted,K::Display);
        assert_eq!(messages.static_message,method.request_kind());
        assert!(!messages.hosted.is_incremental());
        assert!(!messages.static_message.is_incremental());
    }
}
#[test]
fn generic_defaults_keep_hosted_and_static_distinct() {
    let messages=canvas_core::agent_message_kind::LegacyAgentMessages::default();
    assert_eq!(messages.hosted,K::Display);
    assert_eq!(messages.static_message,K::Render);
    assert_ne!(messages.hosted,messages.static_message);
}
