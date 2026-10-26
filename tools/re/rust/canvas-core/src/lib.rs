//! Owned portable frame store.
#![forbid(unsafe_code)]
pub mod contract;
pub mod render_payload;
pub mod payload_codec;
pub mod binary_plist;
pub mod bitmap_image;
pub mod preview_geometry;
pub mod remote_crash;
pub mod crash_report;
pub mod crash_listener;
pub mod iosurface_snapshot;
pub mod iosurface_payload;
pub mod scene_timing;
pub use contract::*;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Snapshot {
    pub revision: u64,
    pub spec: FrameSpec,
    pub frame: Box<[u8]>,
}
#[derive(Default)]
pub struct FrameStore {
    active: Option<Snapshot>,
}
impl FrameStore {
    pub fn snapshot(&self) -> Option<Snapshot> {
        self.active.clone()
    }
    pub fn publish(
        &mut self,
        spec: FrameSpec,
        abi: FrameAbi,
        actual: &[u8],
        expected: &[u8],
    ) -> Result<Snapshot, Error> {
        validate(spec, abi, actual, expected)?;
        let revision = self
            .active
            .as_ref()
            .map_or(Some(1), |s| s.revision.checked_add(1))
            .ok_or(Error::Revision)?;
        let candidate = Snapshot {
            revision,
            spec,
            frame: actual.into(),
        };
        self.active = Some(candidate.clone());
        Ok(candidate)
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    fn valid() -> (FrameSpec, FrameAbi, Vec<u8>) {
        (
            FrameSpec {
                width: 13,
                height: 7,
                stride: 64,
            },
            FrameAbi {
                memory: MEMORY,
                pointer: MEMORY - ALLOCATION as u64,
                capacity: ALLOCATION as u64,
                rendered: 448,
            },
            vec![0xc3; ALLOCATION],
        )
    }
    #[test]
    fn failures_preserve_every_prior_byte() {
        let (spec, abi, bytes) = valid();
        let mut store = FrameStore::default();
        let good = store.publish(spec, abi, &bytes, &bytes).unwrap();
        for offset in [0, 52, ALLOCATION - 1] {
            let mut bad = bytes.clone();
            bad[offset] ^= 1;
            assert_eq!(
                store.publish(spec, abi, &bad, &bytes),
                Err(Error::Mismatch(offset))
            );
            assert_eq!(store.snapshot(), Some(good.clone()));
        }
        let next = store.publish(spec, abi, &bytes, &bytes).unwrap();
        assert_eq!(next.revision, 2);
    }
    #[test]
    fn snapshot_owns_allocation() {
        let (spec, abi, mut bytes) = valid();
        let mut store = FrameStore::default();
        let mut snapshot = store.publish(spec, abi, &bytes, &bytes).unwrap();
        bytes[0] = 0;
        snapshot.frame[1] = 0;
        assert_eq!(
            store.snapshot().unwrap().frame.as_ref(),
            vec![0xc3; ALLOCATION]
        );
    }
    #[test]
    fn rejects_overflow_and_retains_last_valid_frame() {
        let (spec, abi, bytes) = valid();
        let mut store = FrameStore::default();
        let good = store.publish(spec, abi, &bytes, &bytes).unwrap();
        for pointer in [MEMORY - ALLOCATION as u64 + 1, u64::MAX] {
            assert_eq!(
                store.publish(spec, FrameAbi { pointer, ..abi }, &bytes, &bytes),
                Err(Error::Span)
            );
            assert_eq!(store.snapshot(), Some(good.clone()));
        }
    }
    #[test]
    fn rejects_extent_and_receipt_boundaries() {
        let (spec, abi, bytes) = valid();
        for width in [0, 65, u32::MAX] {
            assert_eq!(
                validate(FrameSpec { width, ..spec }, abi, &bytes, &bytes),
                Err(Error::Dimensions)
            );
        }
        for stride in [0, 51, 257, u32::MAX] {
            assert_eq!(
                validate(FrameSpec { stride, ..spec }, abi, &bytes, &bytes),
                Err(Error::Stride)
            );
        }
        assert_eq!(
            validate(
                spec,
                FrameAbi {
                    rendered: 447,
                    ..abi
                },
                &bytes,
                &bytes
            ),
            Err(Error::Rendered)
        );
        assert_eq!(
            validate(
                spec,
                FrameAbi {
                    memory: MEMORY + 1,
                    ..abi
                },
                &bytes,
                &bytes
            ),
            Err(Error::Memory)
        );
        assert_eq!(
            validate(
                spec,
                FrameAbi {
                    capacity: 16383,
                    ..abi
                },
                &bytes,
                &bytes
            ),
            Err(Error::Capacity)
        );
        assert_eq!(
            validate(spec, abi, &bytes[..16383], &bytes),
            Err(Error::Length)
        );
    }
    #[test]
    fn revision_overflow_never_publishes() {
        let (spec, abi, bytes) = valid();
        let mut store = FrameStore::default();
        store.publish(spec, abi, &bytes, &bytes).unwrap();
        store.active.as_mut().unwrap().revision = u64::MAX;
        let old = store.snapshot();
        assert_eq!(
            store.publish(spec, abi, &bytes, &bytes),
            Err(Error::Revision)
        );
        assert_eq!(store.snapshot(), old);
    }
    #[test]
    fn invalid_render_keeps_every_input_byte() {
        let (spec, _, mut bytes) = valid();
        let old = bytes.clone();
        assert_eq!(
            render_primary(spec, [9, 4, 4], false, &mut bytes),
            Err(Error::Alpha)
        );
        assert_eq!(bytes, old);
        assert_eq!(
            render_primary(
                FrameSpec { stride: 51, ..spec },
                [4, 4, 4],
                false,
                &mut bytes
            ),
            Err(Error::Stride)
        );
        assert_eq!(bytes, old);
        let mut short = vec![17; ALLOCATION - 1];
        let old = short.clone();
        assert_eq!(
            render_primary(spec, [4, 4, 4], false, &mut short),
            Err(Error::Length)
        );
        assert_eq!(short, old);
    }
    #[test]
    fn transparent_and_opaque_controls_overwrite_full_allocation() {
        let (spec, _, mut bytes) = valid();
        bytes.fill(0x11);
        assert_eq!(render_primary(spec, [0, 0, 0], false, &mut bytes), Ok(448));
        assert_eq!(&bytes[..4], &[0, 0, 0, 0]);
        assert!(bytes[52..64].iter().all(|b| *b == 0xa5));
        assert!(bytes[448..].iter().all(|b| *b == 0xc3));
        render_primary(spec, [8, 8, 8], false, &mut bytes).unwrap();
        assert_eq!(&bytes[..4], &[0, 255, 0, 255]);
        render_primary(spec, [8, 8, 8], true, &mut bytes).unwrap();
        assert_eq!(&bytes[..4], &[0, 0, 255, 255]);
    }
}
pub mod preference_handshake;
pub mod scene_action;
pub mod action_reply;

pub mod scene_reply;

pub mod delivery_signal;

pub mod settings_xpc;

pub mod action_xpc;

pub mod xpc_wire;

pub mod scene_identity;

pub mod workspace_action;

pub mod service_error;

pub mod nserror_archive;

pub mod agent_message_kind;

pub mod macos_static_route;

pub mod forward_payload;

pub mod service_envelope;

pub mod transport_reply;

pub mod service_identifier;

pub mod service_reply_error;

pub mod service_reply_failure;

pub mod service_property_list;

pub mod service_reply_dispatch;

pub mod service_connection_event;

pub mod service_receiver;

pub mod service_response;

pub mod binary_plist_writer;

pub mod human_readable_error;

pub mod remote_error;

mod remote_prefix;

pub mod error_archive;

pub mod error_presentation;

pub mod preview_error;
pub mod full_diagnostics;
mod diagnostic_escape;
pub mod diagnostic_files;
pub mod service_process;
pub mod cancel_update;
pub mod purge;

pub mod agent_descriptor;
pub mod prepare_relaunch;

pub mod content_requests;

pub mod content_results;

pub mod variants_configuration;

pub mod single_select_configuration;

pub mod variant_id_set;
pub mod multi_select_configuration;

pub mod selection_behavior;

pub mod overrides_configuration;

pub mod variants_reply;

pub mod render_effects;

pub mod effective_overrides;

pub mod task_cache;

pub mod request_projection;

pub mod plist_value_box;

pub mod hashable_plist_box;

pub mod canvas_control_state;

pub mod runnable_configuration_id;
