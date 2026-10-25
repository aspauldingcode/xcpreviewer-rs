//! Canonical Unicode equality for opaque variant IDs, with retained wire spellings.
//!
//! Unicode 16 matches the qualified native runtime. Deterministic iteration sorts
//! decomposed keys; it does not reproduce randomized native Set iteration.
use std::collections::{btree_map::Entry, BTreeMap};
use unicode_normalization::UnicodeNormalization;
#[derive(Clone, Debug, Default)]
pub struct VariantIdSet {
    values: BTreeMap<String, String>,
}
impl VariantIdSet {
    pub fn new() -> Self {
        Self::default()
    }
    /// Retains the first spelling of a canonically equivalent ID.
    pub fn insert(&mut self, value: String) -> bool {
        match self.values.entry(value.nfd().collect()) {
            Entry::Vacant(entry) => {
                entry.insert(value);
                true
            }
            Entry::Occupied(_) => false,
        }
    }
    pub fn contains(&self, value: &str) -> bool {
        self.values.contains_key(&value.nfd().collect::<String>())
    }
    pub fn len(&self) -> usize {
        self.values.len()
    }
    pub fn is_empty(&self) -> bool {
        self.values.is_empty()
    }
    /// Original spellings in deterministic decomposed-key order.
    pub fn iter(&self) -> impl Iterator<Item = &str> {
        self.values.values().map(String::as_str)
    }
}
impl FromIterator<String> for VariantIdSet {
    fn from_iter<T: IntoIterator<Item = String>>(values: T) -> Self {
        let mut result = Self::new();
        for value in values {
            result.insert(value);
        }
        result
    }
}
impl PartialEq for VariantIdSet {
    fn eq(&self, other: &Self) -> bool {
        self.values.keys().eq(other.values.keys())
    }
}
impl Eq for VariantIdSet {}
