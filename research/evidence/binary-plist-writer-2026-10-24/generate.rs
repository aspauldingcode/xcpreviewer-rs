use canvas_core::{binary_plist,binary_plist_writer::encode,payload_codec::Value as V};
use std::{collections::BTreeMap,path::Path};
fn main() {
    let dir=std::env::args().nth(1).unwrap();let dir=Path::new(&dir);std::fs::create_dir_all(dir).unwrap();
    let text=format!("{}按钮🪨\0\n","a".repeat(20));
    let mut cases=vec![
        ("bool",V::Array(vec![V::Boolean(false),V::Boolean(true)])),
        ("integers",V::Array([i64::MIN,-1,0,1,127,128,255,256,65535,65536,4294967296,i64::MAX].map(V::Integer).to_vec())),
        ("real",V::Array([0.0,-0.0,3.5,f64::from_bits(1),f64::MAX].map(V::Real).to_vec())),
        ("dates",V::Array([-1.0,0.0,17.5,12345.5].map(V::Date).to_vec())),
        ("text",V::String(text)),
        ("data",V::Data((0..512).map(|i|(i%256) as u8).collect())),
        ("empty",V::Dictionary(BTreeMap::new())),
        ("wide-refs",V::Array((0..300).map(V::Integer).collect())),
        ("wide-offset",V::Array(vec![V::Data(vec![17;70000]),V::String("after wide offset".into())])),
    ];
    for n in [14,15,255,256] {cases.push((Box::leak(format!("length-{n}").into_boxed_str()),V::Array(vec![V::String("x".repeat(n)),V::Data(vec![17;n])])));}
    for (name,path) in [("native-nested","tools/re/rust/canvas-core/tests/fixtures/service-property-list/nested.wire-data"),("native-error","tools/re/rust/canvas-core/tests/fixtures/service-wire-reply/remote-error.wire-data")] {
        cases.push((name,binary_plist::decode(&std::fs::read(path).unwrap()).unwrap()));
    }
    for (name,value) in cases {let bytes=encode(&value).unwrap();assert_eq!(binary_plist::decode(&bytes).unwrap(),value);std::fs::write(dir.join(format!("{name}.bplist")),bytes).unwrap();}
}
