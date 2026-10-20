use canvas_core::iosurface_snapshot::{copy_linear_snapshot, Error, LinearSurfaceLayout as L};
fn layout() -> L {
    L {
        width: 3,
        height: 2,
        bytes_per_row: 64,
        bytes_per_element: 4,
    }
}
#[test]
fn native_receiver_copy_preserves_all_padding_and_ignores_allocation_tail() {
    let expected = include_bytes!("fixtures/iosurface-snapshot/expected-snapshot.bin");
    let mut allocation = vec![0xa7; 4096];
    allocation[..128].copy_from_slice(expected);
    let image = copy_linear_snapshot(layout(), &allocation).unwrap();
    assert_eq!(&image.data, expected);
    assert_eq!(image.data.len(), 128);
    allocation.fill(0x19);
    assert_eq!(&image.data, expected);
    assert_eq!(image.bitmap_info, 0x2002);
    assert_eq!(image.bits_per_component, 8);
    assert_eq!(image.bits_per_pixel, 32);
    assert_eq!(image.color_space, "kCGColorSpaceSRGB");
    let mut output = vec![0xcd; 56];
    assert_eq!(
        image.write_premultiplied_rgba8(20, &mut output).unwrap(),
        40
    );
    assert_eq!(
        output.as_slice(),
        include_bytes!("fixtures/iosurface-snapshot/expected-output.rgba")
    );
}
#[test]
fn malformed_host_views_fail_without_source_changes() {
    let source = vec![0xa7; 128];
    let before = source.clone();
    assert_eq!(
        copy_linear_snapshot(layout(), &source[..127]),
        Err(Error::SourceLength)
    );
    for width in [-1, 0, 16385] {
        assert_eq!(
            copy_linear_snapshot(L { width, ..layout() }, &source),
            Err(Error::Dimensions)
        );
    }
    assert_eq!(
        copy_linear_snapshot(
            L {
                bytes_per_row: 11,
                ..layout()
            },
            &source
        ),
        Err(Error::Stride)
    );
    for bytes_per_element in [0, -1, i64::MAX] {
        assert_eq!(
            copy_linear_snapshot(
                L {
                    bytes_per_element,
                    ..layout()
                },
                &source
            ),
            Err(Error::ElementSize)
        );
    }
    assert_eq!(
        copy_linear_snapshot(
            L {
                bytes_per_row: i64::MAX,
                ..layout()
            },
            &source
        ),
        Err(Error::Extent)
    );
    assert_eq!(
        copy_linear_snapshot(
            L {
                bytes_per_row: 64 * 1024 * 1024,
                ..layout()
            },
            &source
        ),
        Err(Error::Extent)
    );
    assert_eq!(source, before);
}
#[test]
fn snapshot_metadata_is_separate_from_renderer_format_support() {
    let image = copy_linear_snapshot(
        L {
            width: 1,
            height: 1,
            bytes_per_row: 4,
            bytes_per_element: 3,
        },
        &[1, 2, 3, 9],
    )
    .unwrap();
    assert_eq!(image.bits_per_pixel, 24);
    assert_eq!(image.data, [1, 2, 3, 9]);
    let mut out = [0xcd; 4];
    assert!(image.write_premultiplied_rgba8(4, &mut out).is_err());
    assert_eq!(out, [0xcd; 4]);
}
