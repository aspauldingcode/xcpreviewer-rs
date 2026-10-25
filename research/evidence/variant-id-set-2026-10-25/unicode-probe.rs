use unicode_normalization::{UnicodeNormalization,char::canonical_combining_class};
fn hex(s:&str)->String{s.chars().map(|c|format!("{:x}",c as u32)).collect::<Vec<_>>().join(",")}
fn main(){
 eprintln!("Unicode {:?}",unicode_normalization::UNICODE_VERSION);
 for i in 0..=0x10ffff {
  let Some(c)=char::from_u32(i) else {continue};let a=c.to_string();let b:String=a.nfd().collect();
  if a!=b {println!("decomposition\t{}\t{}",hex(&a),hex(&b));}
  let ccc=canonical_combining_class(c);
  if ccc>0 && ccc!=230 {println!("combining-order\t{}\t{}",hex(&format!("a{c}\u{300}")),hex(&format!("a\u{300}{c}")));}
 }
}
