use canvas_core::{
    binary_plist,
    diagnostic_files::{FileEntry, FileQueue, FileSink, LimitError, Limits},
    payload_codec::Value as V,
};
#[derive(Default)]
struct Sink {
    operations: Vec<String>,
    bytes: Vec<u8>,
    fail_create: bool,
    fail_write: bool,
}
impl FileSink for Sink {
    type Destination = String;
    type Error = &'static str;
    fn directory(&mut self, base: &String, name: &str) -> String {
        self.operations.push("directory".into());
        format!("{base}/{name}")
    }
    fn create_intermediate_directory(&mut self, _: &String) -> Result<(), Self::Error> {
        self.operations.push("create".into());
        if self.fail_create {
            Err("create")
        } else {
            Ok(())
        }
    }
    fn file(&mut self, base: &String, name: &str) -> String {
        self.operations.push("file".into());
        format!("{base}/{name}")
    }
    fn write_utf8(&mut self, _: &String, bytes: &[u8], atomic: bool) -> Result<(), Self::Error> {
        assert!(atomic);
        self.operations.push("write".into());
        if self.fail_write {
            return Err("write");
        };
        self.bytes = bytes.into();
        Ok(())
    }
}
#[test]
fn complete_owned_foundation_file_controls() {
    let V::Array(rows) =
        binary_plist::decode(include_bytes!("fixtures/diagnostic-files/native.bplist")).unwrap()
    else {
        panic!()
    };
    assert_eq!(rows.len(), 5);
    for row in rows {
        let V::Dictionary(row) = row else { panic!() };
        let V::String(name) = &row["name"] else {
            panic!()
        };
        let V::String(contents) = &row["contents"] else {
            panic!()
        };
        let folder = match row.get("folder") {
            Some(V::String(s)) => Some(s.as_str()),
            None => None,
            _ => panic!(),
        };
        let mut q = FileQueue::default();
        q.append(name, folder, contents).unwrap();
        let V::String(error) = &row["error_domain"] else {
            panic!()
        };
        let mut sink = Sink {
            fail_create: !error.is_empty(),
            fail_write: !error.is_empty(),
            ..Sink::default()
        };
        let result = q.entries()[0].serialize_into(&"owned".into(), &mut sink);
        assert_eq!(result.is_err(), !error.is_empty());
        assert_eq!(
            V::Array(sink.operations.into_iter().map(V::String).collect()),
            row["operations"]
        );
        assert_eq!(V::Data(sink.bytes), row["bytes"]);
        assert_eq!(V::Boolean(folder.is_some()), row["folder_present"]);
    }
}
#[test]
fn append_is_deferred_ordered_and_transactional() {
    let mut q = FileQueue::new(Limits {
        entries: 2,
        utf8_bytes: 6,
    });
    q.append("a", None, "x").unwrap();
    q.append("a", Some(""), "🪨").unwrap_err();
    assert_eq!(q.entries().len(), 1);
    q.append("a", Some(""), "x").unwrap();
    assert_eq!(q.entries()[0].folder, None);
    assert_eq!(q.entries()[1].folder, Some("".into()));
    assert_eq!(q.append("b", None, ""), Err(LimitError::Entries));
    let snapshot = q.clone();
    assert_eq!(snapshot.entries(), q.entries());
    let mut z = FileQueue::new(Limits {
        entries: 1,
        utf8_bytes: 0,
    });
    z.append("", None, "").unwrap();
}
#[test]
fn exact_bytes_and_write_error_propagate_without_retry() {
    let mut q = FileQueue::new(Limits {
        entries: 1,
        utf8_bytes: 6,
    });
    q.append("a", Some("b"), "🪨").unwrap();
    let mut sink = Sink {
        fail_write: true,
        ..Sink::default()
    };
    assert_eq!(
        q.entries()[0].serialize_into(&"owned".into(), &mut sink),
        Err("write")
    );
    assert_eq!(sink.operations, ["directory", "create", "file", "write"]);
    assert_eq!(q.entries().len(), 1);
    let mut sink = Sink::default();
    q.entries()[0]
        .serialize_into(&"owned".into(), &mut sink)
        .unwrap();
    assert_eq!(sink.bytes, "🪨".as_bytes());
    let mut short = FileQueue::new(Limits {
        entries: 1,
        utf8_bytes: 5,
    });
    assert_eq!(short.append("a", Some("b"), "🪨"), Err(LimitError::Bytes));
    assert!(short.entries().is_empty());
    let direct = FileEntry {
        name: "other".into(),
        folder: None,
        contents: "\0\\n".into(),
    };
    let mut sink = Sink::default();
    direct.serialize_into(&"owned".into(), &mut sink).unwrap();
    assert_eq!(sink.operations, ["file", "write"]);
    assert_eq!(sink.bytes, b"\0\\n");
}

#[test]
fn creation_error_is_discarded_before_write_result() {
    let entry = FileEntry {
        name: "file".into(),
        folder: Some("folder".into()),
        contents: "retained".into(),
    };
    let mut sink = Sink {
        fail_create: true,
        ..Sink::default()
    };
    assert_eq!(entry.serialize_into(&"owned".into(), &mut sink), Ok(()));
    assert_eq!(sink.operations, ["directory", "create", "file", "write"]);
    assert_eq!(sink.bytes, b"retained");
}
