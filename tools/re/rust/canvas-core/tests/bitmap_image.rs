use canvas_core::binary_plist::decode_render_payload_binary;
use canvas_core::bitmap_image::Error;
use canvas_core::payload_codec::BitmapDescription;
const FIRST_LE: &[u8] = include_bytes!("fixtures/bitmap-image/2002.bplist");
fn bitmap() -> BitmapDescription {
    decode_render_payload_binary(FIRST_LE)
        .unwrap()
        .bitmap_description
}
#[test]
fn decoded_payloads_match_every_native_and_independent_output_byte() {
    for (input, native) in [
        (
            &include_bytes!("fixtures/bitmap-image/2002.bplist")[..],
            &include_bytes!("fixtures/bitmap-image/2002.rgba")[..],
        ),
        (
            &include_bytes!("fixtures/bitmap-image/4002.bplist")[..],
            &include_bytes!("fixtures/bitmap-image/4002.rgba")[..],
        ),
        (
            &include_bytes!("fixtures/bitmap-image/2001.bplist")[..],
            &include_bytes!("fixtures/bitmap-image/2001.rgba")[..],
        ),
        (
            &include_bytes!("fixtures/bitmap-image/4001.bplist")[..],
            &include_bytes!("fixtures/bitmap-image/4001.rgba")[..],
        ),
    ] {
        let p = decode_render_payload_binary(input).unwrap();
        let original = p.bitmap_description.data.clone();
        let mut output = vec![0xcd; 56];
        assert_eq!(
            p.bitmap_description
                .write_premultiplied_rgba8(20, &mut output),
            Ok(40)
        );
        assert_eq!(output, native);
        assert_eq!(
            output,
            include_bytes!("fixtures/bitmap-image/expected-rgba.bin")
        );
        assert_eq!(p.bitmap_description.data, original);
    }
}
#[test]
fn unsupported_or_invalid_input_preserves_every_destination_byte() {
    let original = bitmap();
    let mut cases = Vec::new();
    let mut b = original.clone();
    b.width = -1;
    cases.push((b, 20, Error::Dimensions));
    let mut b = original.clone();
    b.height = 0;
    cases.push((b, 20, Error::Dimensions));
    let mut b = original.clone();
    b.width = 16385;
    cases.push((b, 20, Error::Dimensions));
    let mut b = original.clone();
    b.bytes_per_row = 11;
    cases.push((b, 20, Error::Stride));
    let mut b = original.clone();
    b.bytes_per_row = i64::MAX;
    cases.push((b, 20, Error::Limit));
    let mut b = original.clone();
    b.data.truncate(31);
    cases.push((b, 20, Error::Length));
    let mut b = original.clone();
    b.bits_per_component = 16;
    cases.push((b, 20, Error::UnsupportedFormat));
    let mut b = original.clone();
    b.bits_per_pixel = 64;
    cases.push((b, 20, Error::UnsupportedFormat));
    let mut b = original.clone();
    b.color_space = "kCGColorSpaceDisplayP3".into();
    cases.push((b, 20, Error::UnsupportedColorSpace));
    let mut b = original.clone();
    b.data[16 + 8] = 255;
    b.data[16 + 11] = 0;
    cases.push((b, 20, Error::InvalidPremultiplication));
    for flags in [0, 2, 0x2003, 0x4003, 0x2102, 0x6002, u32::MAX] {
        let mut b = original.clone();
        b.bitmap_info = flags;
        cases.push((b, 20, Error::UnsupportedFormat));
    }
    cases.push((original.clone(), 11, Error::Stride));
    cases.push((original.clone(), usize::MAX, Error::Limit));
    for (b, stride, error) in cases {
        let mut output = vec![0x6b; 56];
        assert_eq!(b.write_premultiplied_rgba8(stride, &mut output), Err(error));
        assert_eq!(output, vec![0x6b; 56]);
    }
    let mut short = vec![0x6b; 39];
    assert_eq!(
        original.write_premultiplied_rgba8(20, &mut short),
        Err(Error::Length)
    );
    assert_eq!(short, vec![0x6b; 39]);
}
#[test]
fn row_padding_does_not_become_pixels_and_tight_output_works() {
    let mut b = bitmap();
    let mut before = vec![0; 24];
    b.write_premultiplied_rgba8(12, &mut before).unwrap();
    for i in [12, 13, 14, 15, 28, 29, 30, 31, 32, 39] {
        b.data[i] ^= 0xff;
    }
    let mut after = vec![0; 24];
    b.write_premultiplied_rgba8(12, &mut after).unwrap();
    assert_eq!(before, after);
    let reference = include_bytes!("fixtures/bitmap-image/expected-rgba.bin");
    assert_eq!(after, [&reference[..12], &reference[20..32]].concat());
}
