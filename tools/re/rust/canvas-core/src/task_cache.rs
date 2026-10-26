//! Source-guided serialized task-handle storage. Hosts own scheduling, awaiting,
//! results, cancellation cooperation and handle lifetime; this is not an executor.
use std::{
    collections::{hash_map::Entry, HashMap},
    hash::Hash,
};
#[derive(Debug)]
pub struct TaskAcquisition<K, T> {
    key: K,
    task: T,
    created: bool,
}
impl<K, T> TaskAcquisition<K, T> {
    pub fn task(&self) -> &T {
        &self.task
    }
    pub fn created(&self) -> bool {
        self.created
    }
}
#[derive(Debug)]
pub struct TaskCache<K, T> {
    clear_on_failure: bool,
    storage: HashMap<K, T>,
}
impl<K: Eq + Hash + Clone, T: Clone> Default for TaskCache<K, T> {
    fn default() -> Self {
        Self::new(false)
    }
}
impl<K: Eq + Hash + Clone, T: Clone> TaskCache<K, T> {
    pub fn new(clear_on_failure: bool) -> Self {
        Self {
            clear_on_failure,
            storage: HashMap::new(),
        }
    }
    pub fn clear_on_failure(&self) -> bool {
        self.clear_on_failure
    }
    pub fn len(&self) -> usize {
        self.storage.len()
    }
    pub fn is_empty(&self) -> bool {
        self.storage.is_empty()
    }
    pub fn tasks(&self) -> impl Iterator<Item = &T> {
        self.storage.values()
    }
    /// Invoke the host's task factory once on a miss, and store before returning.
    /// A stored handle is reused regardless of pending/success/failure state.
    pub fn acquire(&mut self, key: K, make_task: impl FnOnce() -> T) -> TaskAcquisition<K, T> {
        let (task, created) = match self.storage.entry(key.clone()) {
            Entry::Occupied(entry) => (entry.get().clone(), false),
            Entry::Vacant(entry) => {
                let task = make_task();
                entry.insert(task.clone());
                (task, true)
            }
        };
        TaskAcquisition { key, task, created }
    }
    /// Call when this lookup observes a task error. Only its creating lookup
    /// clears the key, and only with clear_on_failure. No task-identity guard:
    /// a late creator failure can remove a replacement under the same key.
    /// The consumed ticket cannot apply its cleanup twice. Success needs no call.
    pub fn observe_failure(&mut self, lookup: TaskAcquisition<K, T>) -> Option<T> {
        if self.clear_on_failure && lookup.created {
            self.storage.remove(&lookup.key)
        } else {
            None
        }
    }
    /// Match native default cancelingTask=true. Cancellation is requested before
    /// the entry is removed; it does not imply task completion or waiter release.
    pub fn invalidate(&mut self, key: &K, cancel: impl FnOnce(&T)) -> Option<T> {
        self.invalidate_with(key, true, cancel)
    }
    pub fn invalidate_with(
        &mut self,
        key: &K,
        canceling_task: bool,
        cancel: impl FnOnce(&T),
    ) -> Option<T> {
        if canceling_task {
            if let Some(task) = self.storage.get(key) {
                cancel(task);
            }
        }
        self.storage.remove(key)
    }
}
