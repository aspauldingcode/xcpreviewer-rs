// Owned public SwiftUI captures, accepted by the actual private RenderPayload codec.
use canvas_core::{
    binary_plist::{decode, decode_render_payload_binary},
    binary_plist_writer::encode,
    browser_frame::frame_packet,
    payload_codec::Value,
};
fn verify_capture(name: &str) {
    let source = match name {
        "asymmetric" => {
            include_bytes!("../tests/fixtures/swiftui_capture/asymmetric.bplist").as_slice()
        }
        "transparent" => {
            include_bytes!("../tests/fixtures/swiftui_capture/transparent.bplist").as_slice()
        }
        _ => panic!("fixture"),
    };
    let native = decode(include_bytes!(
        "../tests/fixtures/swiftui_capture/native.bplist"
    ))
    .unwrap();
    let Value::Array(rows) = native else {
        panic!("native rows")
    };
    let row = rows
        .iter()
        .find_map(|r| {
            let Value::Dictionary(r) = r else {
                panic!("row")
            };
            (r["case"] == Value::String(name.into())).then_some(r)
        })
        .unwrap();
    assert_eq!(row["accepted"], Value::Boolean(true));
    let canonical = encode(&row["canonical"]).unwrap();
    assert_eq!(
        decode_render_payload_binary(source).unwrap(),
        decode_render_payload_binary(&canonical).unwrap()
    );
    let frame = frame_packet(source).unwrap();
    assert_eq!(frame, frame_packet(&canonical).unwrap());
    assert_eq!(&frame[..8], b"XCPV\x01\0\0\0");
    let u32_at = |i| u32::from_le_bytes(frame[i..i + 4].try_into().unwrap());
    assert_eq!(u32_at(20), 0);
    if name == "asymmetric" {
        assert_eq!((u32_at(8), u32_at(12)), (64, 48));
        assert_eq!(f64::from_le_bytes(frame[24..32].try_into().unwrap()), 1.0);
        for (i, p) in frame[40..].chunks_exact(4).enumerate() {
            assert_eq!(
                p,
                if i < 64 * 24 {
                    &[255, 56, 60, 255][..]
                } else {
                    &[0, 136, 255, 255][..]
                }
            );
        }
    } else {
        assert_eq!((u32_at(8), u32_at(12)), (32, 32));
        assert_eq!(f64::from_le_bytes(frame[24..32].try_into().unwrap()), 2.0);
        for p in frame[40..].chunks_exact(4) {
            assert_eq!(p, [96, 32, 64, 128]);
        }
    }
    println!(
        "{}: native codec, geometry and all captured pixels agree",
        name
    );
}
fn main() {
    verify_capture("asymmetric");
    verify_capture("transparent");
}
