use canvas_core::{
    binary_plist,
    diagnostic_files::{
        BatchReport, EntryFailure, FileSink, ReportLimitError, FAILURE_REPORT_NAME,
    },
    payload_codec::Value as V,
};
#[derive(Default)]
struct Sink {
    calls: Vec<String>,
    bytes: Vec<u8>,
    fail: bool,
}
impl FileSink for Sink {
    type Destination = String;
    type Error = ();
    fn directory(&mut self, _: &String, _: &str) -> String {
        panic!("report does not create folders")
    }
    fn create_intermediate_directory(&mut self, _: &String) -> Result<(), ()> {
        panic!()
    }
    fn file(&mut self, base: &String, name: &str) -> String {
        assert_eq!(base, "owned");
        assert_eq!(name, FAILURE_REPORT_NAME);
        self.calls.push("file".into());
        name.into()
    }
    fn write_utf8(&mut self, _: &String, bytes: &[u8], atomically: bool) -> Result<(), ()> {
        assert!(atomically);
        self.calls.push("write".into());
        self.bytes = bytes.into();
        if self.fail {
            Err(())
        } else {
            Ok(())
        }
    }
}

fn complete_foundation_failure_report_controls() {
    let V::Array(records) =
        binary_plist::decode(include_bytes!("native.bplist")).unwrap()
    else {
        panic!()
    };
    assert_eq!(records.len(), 5);
    for row in records {
        let V::Dictionary(row) = row else { panic!() };
        let V::Array(descriptions) = &row["descriptions"] else {
            panic!()
        };
        let report = BatchReport {
            attempted: descriptions.len(),
            failures: descriptions
                .iter()
                .enumerate()
                .map(|(index, v)| {
                    let V::String(error) = v else { panic!() };
                    EntryFailure {
                        index,
                        error: error.clone(),
                    }
                })
                .collect(),
        };
        let V::Boolean(fail) = row["failWrite"] else {
            panic!()
        };
        let mut sink = Sink {
            fail,
            ..Default::default()
        };
        let mut calls = 0;
        let attempted = report
            .write_failure_report_into(
                &"owned".into(),
                &mut sink,
                |error| {
                    calls += 1;
                    error.clone()
                },
                1024,
            )
            .unwrap();
        assert_eq!(V::Boolean(attempted), row["attempted"]);
        assert_eq!(V::Boolean(attempted && fail), row["ignoredWriteError"]);
        assert_eq!(calls, descriptions.len());
        assert_eq!(
            sink.calls,
            if attempted {
                vec!["file", "write"]
            } else {
                vec![]
            }
        );
        if attempted && !fail {
            assert_eq!(V::Data(sink.bytes), row["bytes"])
        }
        if !attempted {
            assert_eq!(row["bytes"], V::Data(b"sentinel".to_vec()))
        }
        assert_eq!(report.failures.len(), descriptions.len());
    }
}

fn joined_budget_checked_before_io_and_errors_remain_reusable() {
    let report = BatchReport {
        attempted: 3,
        failures: vec![
            EntryFailure {
                index: 0,
                error: "🙂",
            },
            EntryFailure {
                index: 2,
                error: "\\n",
            },
        ],
    };
    let mut sink = Sink::default();
    assert_eq!(
        report.write_failure_report_into(&"owned".into(), &mut sink, |s| s.to_string(), 7),
        Err(ReportLimitError)
    );
    assert!(sink.calls.is_empty());
    assert_eq!(
        report.write_failure_report_into(&"owned".into(), &mut sink, |s| s.to_string(), 8),
        Ok(true)
    );
    assert_eq!(sink.bytes, "🙂\n\n\n".as_bytes());
    assert_eq!(
        report.failures.iter().map(|e| e.index).collect::<Vec<_>>(),
        vec![0, 2]
    );
    let empty: BatchReport<()> = BatchReport {
        attempted: 2,
        failures: vec![],
    };
    assert_eq!(
        empty.write_failure_report_into(&"owned".into(), &mut sink, |_| panic!(), 0),
        Ok(false)
    );
    let one = BatchReport {
        attempted: 1,
        failures: vec![EntryFailure {
            index: 0,
            error: "",
        }],
    };
    assert_eq!(
        one.write_failure_report_into(&"owned".into(), &mut sink, |s| s.to_string(), 0),
        Ok(true)
    );
    assert!(sink.bytes.is_empty());
}

fn main(){complete_foundation_failure_report_controls();joined_budget_checked_before_io_and_errors_remain_reusable();println!("Five report controls and joined UTF-8 budget/retained errors passed in WASI");}
