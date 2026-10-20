use canvas_core::{
    preference_handshake::*,
    scene_timing::{SceneTiming, SceneUpdateSeed as Seed},
};
#[test]
fn matching_resolution_consumes_once_and_preserves_other_requests() {
    let mut t = PreferenceHandshakeTracker::default();
    t.begin(Seed(-1)).unwrap();
    t.begin(Seed(7)).unwrap();
    assert_eq!(
        t.resolve(Seed(-1), SceneTiming::Fenced),
        Some(SceneTiming::Fenced)
    );
    assert_eq!(t.resolve(Seed(-1), SceneTiming::Async), None);
    assert!(t.contains(Seed(7)));
    assert_eq!(t.len(), 1);
    assert_eq!(
        t.resolve(Seed(7), SceneTiming::Async),
        Some(SceneTiming::Async)
    );
    assert!(t.is_empty());
}
#[test]
fn duplicate_begin_fails_and_clears_old_registration() {
    let mut t = PreferenceHandshakeTracker::default();
    t.begin(Seed(i64::MIN)).unwrap();
    t.begin(Seed(2)).unwrap();
    assert_eq!(
        t.begin(Seed(i64::MIN)),
        Err(DuplicatePreferenceSeed(Seed(i64::MIN)))
    );
    assert!(!t.contains(Seed(i64::MIN)));
    assert!(t.contains(Seed(2)));
    assert_eq!(t.resolve(Seed(i64::MIN), SceneTiming::Fenced), None);
}
#[test]
fn unknown_reply_is_not_cached_and_reused_seed_has_no_hidden_generation() {
    let mut t = PreferenceHandshakeTracker::default();
    assert_eq!(t.resolve(Seed(9), SceneTiming::Fenced), None);
    t.begin(Seed(9)).unwrap();
    assert!(t.contains(Seed(9)));
    assert_eq!(
        t.resolve(Seed(9), SceneTiming::Async),
        Some(SceneTiming::Async)
    );
    t.begin(Seed(9)).unwrap();
    // A late old reply has the same correlation key: no invented stale filter.
    assert_eq!(
        t.resolve(Seed(9), SceneTiming::Fenced),
        Some(SceneTiming::Fenced)
    );
    assert!(t.is_empty());
}
