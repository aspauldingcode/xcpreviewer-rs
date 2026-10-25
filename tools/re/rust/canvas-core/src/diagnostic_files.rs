//! Deferred canonical file actions. The caller owns URL/path semantics and I/O.
//! Native archive cleanup, ZIP creation, log/command/copy actions are separate.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct FileEntry {
    pub name: String,
    pub folder: Option<String>,
    pub contents: String,
}
/// Destination resolution is delegated without treating names as portable paths.
/// A sink's successful write is not proof of remote/native resource settlement.
pub trait FileSink {
    type Destination: Clone;
    type Error;
    fn directory(&mut self, base: &Self::Destination, name: &str) -> Self::Destination;
    fn create_intermediate_directory(
        &mut self,
        directory: &Self::Destination,
    ) -> Result<(), Self::Error>;
    fn file(&mut self, base: &Self::Destination, name: &str) -> Self::Destination;
    fn write_utf8(
        &mut self,
        destination: &Self::Destination,
        bytes: &[u8],
        atomically: bool,
    ) -> Result<(), Self::Error>;
}
impl FileEntry {
    pub fn serialize_into<S: FileSink>(
        &self,
        base: &S::Destination,
        sink: &mut S,
    ) -> Result<(), S::Error> {
        let directory = if let Some(folder) = &self.folder {
            let d = sink.directory(base, folder);
            // Native action discards directory-creation failure and still writes.
            let _ = sink.create_intermediate_directory(&d);
            d
        } else {
            base.clone()
        };
        let file = sink.file(&directory, &self.name);
        sink.write_utf8(&file, self.contents.as_bytes(), true)
    }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Limits {
    pub entries: usize,
    pub utf8_bytes: usize,
}
impl Default for Limits {
    fn default() -> Self {
        Self {
            entries: 10_000,
            utf8_bytes: 64 * 1024 * 1024,
        }
    }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum LimitError {
    Entries,
    Bytes,
}
/// Original bounded file-action queue, not the native collector's lock/state.
/// Append preserves order/duplicates and performs no I/O. Limits count all
/// retained name/folder/content UTF-8 bytes and are not recovered native limits.
#[derive(Clone, Debug)]
pub struct FileQueue {
    entries: Vec<FileEntry>,
    bytes: usize,
    limits: Limits,
}
impl Default for FileQueue {
    fn default() -> Self {
        Self::new(Limits::default())
    }
}
impl FileQueue {
    pub fn new(limits: Limits) -> Self {
        Self {
            entries: Vec::new(),
            bytes: 0,
            limits,
        }
    }
    pub fn entries(&self) -> &[FileEntry] {
        &self.entries
    }
    pub fn append(
        &mut self,
        name: &str,
        folder: Option<&str>,
        contents: &str,
    ) -> Result<(), LimitError> {
        if self.entries.len() >= self.limits.entries {
            return Err(LimitError::Entries);
        }
        let size = name
            .len()
            .checked_add(folder.map_or(0, str::len))
            .and_then(|n| n.checked_add(contents.len()))
            .and_then(|n| n.checked_add(self.bytes))
            .filter(|&n| n <= self.limits.utf8_bytes)
            .ok_or(LimitError::Bytes)?;
        self.entries.push(FileEntry {
            name: name.into(),
            folder: folder.map(str::to_owned),
            contents: contents.into(),
        });
        self.bytes = size;
        Ok(())
    }
}
/// Original observability metadata associates a retained sink error with its
/// queue index. The native collector retains errors without this index field.
#[derive(Debug, PartialEq, Eq)]
pub struct EntryFailure<E> {
    pub index: usize,
    pub error: E,
}
#[derive(Debug, PartialEq, Eq)]
pub struct BatchReport<E> {
    pub attempted: usize,
    pub failures: Vec<EntryFailure<E>>,
}
impl FileQueue {
    /// Execute this retained file-action set sequentially, keeping each write
    /// failure in encounter order and continuing with later entries. No action
    /// is consumed or automatically retried. Use clone for an independent snapshot.
    /// This omits collector archive setup, generated actions, error-report output
    /// and ZIP creation; no filesystem/resource settlement is implied.
    pub fn serialize_all_into<S: FileSink>(
        &self,
        base: &S::Destination,
        sink: &mut S,
    ) -> BatchReport<S::Error> {
        let mut failures = Vec::new();
        for (index, entry) in self.entries.iter().enumerate() {
            if let Err(error) = entry.serialize_into(base, sink) {
                failures.push(EntryFailure { index, error });
            }
        }
        BatchReport {
            attempted: self.entries.len(),
            failures,
        }
    }
}
