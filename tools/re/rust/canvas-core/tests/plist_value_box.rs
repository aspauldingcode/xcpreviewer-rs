use canvas_core::{
    binary_plist, binary_plist_writer,
    payload_codec::Value,
    plist_value_box::{self, ArrayError, Error, PlistValueBox, UnboxError},
};
use std::{
    cell::Cell,
    collections::BTreeMap,
    io::Write,
    process::{Command, Stdio},
};
fn rows() -> Vec<Value> {
    let Value::Array(rows) =
        binary_plist::decode(include_bytes!("fixtures/plist_value_box/native.bplist")).unwrap()
    else {
        panic!()
    };
    rows
}
fn string(v: &Value) -> Result<String, &'static str> {
    match v {
        Value::String(s) => Ok(s.clone()),
        _ => Err("String"),
    }
}
fn report(kind: &str, input: &Value) -> Result<Value, String> {
    if kind == "control-state-boxes" {
        return plist_value_box::decode_boxes(input)
            .map(|boxes| Value::Array(boxes.iter().map(PlistValueBox::to_value).collect()))
            .map_err(|e| format!("{e:?}"));
    }
    let b = PlistValueBox::decode(input).map_err(|e| format!("{e:?}"))?;
    if kind == "plist-box" {
        return Ok(b.to_value());
    }
    let value = if kind == "unbox-string" {
        Some(b.required_with(string).map_err(|e| format!("{e:?}"))?)
    } else {
        b.optional_with(string).map_err(str::to_owned)?
    };
    let mut fields = BTreeMap::new();
    fields.insert("isPresent".into(), Value::Boolean(value.is_some()));
    if let Some(value) = value {
        fields.insert("value".into(), Value::String(value));
    }
    Ok(Value::Dictionary(fields))
}
#[test]
fn complete_public_compositions() {
    let mut accepted = 0;
    for row in rows() {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let Value::String(kind) = &row["kind"] else {
            panic!()
        };
        let result = report(kind, &row["input"]);
        assert_eq!(
            result.is_ok(),
            row["accepted"] == Value::Boolean(true),
            "{:?}",
            row["name"]
        );
        if let Ok(result) = result {
            accepted += 1;
            assert_eq!(result, row["output"], "{:?}", row["name"]);
        }
    }
    assert_eq!(accepted, 18);
}
#[test]
fn delegation_presence_owned_values_and_portable_collision_boundary() {
    let empty = PlistValueBox::decode(&Value::Dictionary(BTreeMap::new())).unwrap();
    let calls = Cell::new(0);
    assert_eq!(
        empty.required_with(|_| {
            calls.set(calls.get() + 1);
            Ok::<_, u8>(false)
        }),
        Err(UnboxError::MissingValue)
    );
    assert_eq!(
        empty.optional_with(|_| {
            calls.set(calls.get() + 1);
            Ok::<_, u8>(false)
        }),
        Ok(None)
    );
    assert_eq!(calls.get(), 0);
    let b = PlistValueBox::from_value(Value::Boolean(false));
    assert_eq!(
        b.optional_with(|v| match v {
            Value::Boolean(b) => Ok::<_, u8>(*b),
            _ => Err(3),
        }),
        Ok(Some(false))
    );
    assert_eq!(
        b.required_with(|_| Err::<(), _>(27)),
        Err(UnboxError::Decode(27))
    );
    assert_eq!(b.optional_with(|_| Err::<(), _>(27)), Err(27));
    let mut encoded = b.to_value();
    let Value::Dictionary(ref mut fields) = encoded else {
        panic!()
    };
    fields.insert("value".into(), Value::String("changed".into()));
    assert_eq!(b.value(), Some(&Value::Boolean(false)));
    let collision = Value::Dictionary(
        [
            ("é".into(), Value::Integer(1)),
            ("e\u{301}".into(), Value::Integer(2)),
        ]
        .into_iter()
        .collect(),
    );
    assert_eq!(
        PlistValueBox::decode(&collision).unwrap_err(),
        Error::CanonicalKeyCollision
    );
    assert_eq!(
        plist_value_box::decode_boxes(&Value::Array(vec![b.to_value(), collision])).unwrap_err(),
        ArrayError::Element {
            index: 1,
            cause: Error::CanonicalKeyCollision
        }
    );
}
#[test]
fn cli_complete_values_and_bounded_summaries() {
    for row in rows() {
        let Value::Dictionary(row) = row else {
            panic!()
        };
        let Value::String(kind) = &row["kind"] else {
            panic!()
        };
        let bytes = binary_plist_writer::encode(&row["input"]).unwrap();
        for canonical in [false, true] {
            let mut command = Command::new(env!("CARGO_BIN_EXE_inspect-content-result"));
            if canonical {
                command.arg("--canonical");
            }
            let mut child = command
                .args([kind, "-"])
                .stdin(Stdio::piped())
                .stdout(Stdio::piped())
                .stderr(Stdio::piped())
                .spawn()
                .unwrap();
            child.stdin.take().unwrap().write_all(&bytes).unwrap();
            let output = child.wait_with_output().unwrap();
            assert_eq!(
                output.status.success(),
                row["accepted"] == Value::Boolean(true)
            );
            if output.status.success() {
                if canonical {
                    assert_eq!(binary_plist::decode(&output.stdout).unwrap(), row["output"]);
                } else {
                    let text = String::from_utf8(output.stdout).unwrap();
                    assert!(text.starts_with(&format!("result={kind}\n")));
                    assert!(text.len() < 4096);
                    if row["name"] == Value::String("many-boxes".into()) {
                        assert!(text.contains("boxesShown=8"));
                    }
                    if kind.starts_with("unbox-")
                        && row["name"] == Value::String(format!("{kind}-2"))
                    {
                        assert!(text.contains("valueTruncated=true"));
                    }
                }
            } else {
                assert!(output.stdout.is_empty());
            }
        }
    }
}
