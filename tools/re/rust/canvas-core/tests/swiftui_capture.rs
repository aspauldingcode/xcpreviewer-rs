include!("../examples/swiftui_capture.rs");
#[test]
fn native_swiftui_opaque_capture_keeps_orientation() {
    verify_capture("asymmetric");
}
#[test]
fn native_swiftui_transparent_capture_keeps_premultiplication_and_scale() {
    verify_capture("transparent");
}
