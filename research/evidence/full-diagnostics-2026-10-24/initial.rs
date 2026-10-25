//! Source-guided diagnostic text for the canonical leaf/wrapper archive.
//! Native private getters, custom conformances and diagnostic collection are separate.
use crate::{
    error_archive::{ErrorArchive, Limits},
    error_presentation::Error,
};
const DIVIDER: &str = "\n\n==================================\n\n";
fn append(out: &mut String, text: &str, remaining: &mut usize) -> Result<(), Error> {
    *remaining = remaining.checked_sub(text.len()).ok_or(Error::ByteLimit)?;
    out.push_str(text);
    Ok(())
}
impl ErrorArchive {
    pub fn full_diagnostics(&self) -> Result<String, Error> {
        self.full_diagnostics_with_limits(Limits::default(), 64 * 1024 * 1024)
    }
    /// Original node/depth and cumulative appended UTF-8 work budgets, including
    /// intermediate reports and normalized copies. These are not native limits.
    pub fn full_diagnostics_with_limits(
        &self,
        limits: Limits,
        mut bytes: usize,
    ) -> Result<String, Error> {
        let mut nodes = limits.nodes;
        let mut tasks = vec![(self, 0usize, false)];
        let mut values: Vec<String> = Vec::new();
        while let Some((node, depth, join)) = tasks.pop() {
            if join {
                let cause = values.pop().expect("cause result");
                let main = values.pop().expect("main result");
                let mut out = String::new();
                append(&mut out, &main, &mut bytes)?;
                append(&mut out, DIVIDER, &mut bytes)?;
                for (i, line) in cause.split('\n').enumerate() {
                    if i != 0 {
                        append(&mut out, "\n", &mut bytes)?;
                    }
                    append(&mut out, "|  ", &mut bytes)?;
                    append(&mut out, line, &mut bytes)?;
                }
                values.push(out);
                continue;
            }
            if nodes == 0 || depth > limits.depth {
                return Err(Error::TreeLimit);
            }
            nodes -= 1;
            match node {
                Self::Wrapper { main, underlying } => {
                    tasks.push((node, depth, true));
                    tasks.push((underlying, depth + 1, false));
                    tasks.push((main, depth + 1, false));
                }
                Self::Leaf(leaf) => {
                    let mut out = String::new();
                    append(&mut out, &leaf.error_type_description, &mut bytes)?;
                    if let Some(title) = leaf
                        .high_value_title
                        .as_ref()
                        .or(leaf.low_value_title.as_ref())
                    {
                        append(&mut out, ": ", &mut bytes)?;
                        append(&mut out, title, &mut bytes)?;
                    }
                    for s in [&leaf.additional_info, &leaf.additional_diagnostics]
                        .into_iter()
                        .flatten()
                    {
                        append(&mut out, "\n\n", &mut bytes)?;
                        append(&mut out, s, &mut bytes)?;
                    }
                    // Foundation's fixed ASCII literal replacement is non-overlapping. Charge
                    // the complete normalized copy before allocation, preserving UTF-8 data.
                    let normalized_len = out.len() - out.match_indices("\\n").count();
                    bytes = bytes.checked_sub(normalized_len).ok_or(Error::ByteLimit)?;
                    values.push(out.replace("\\n", "\n"));
                }
            }
        }
        Ok(values.pop().expect("root result"))
    }
}
