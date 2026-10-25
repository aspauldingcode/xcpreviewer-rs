//! Pure supported-archive presentation values from recovered wrapper algebra.
//! This does not invoke native getters or reproduce fullDiagnosticsOutput.
use crate::{
    error_archive::{ErrorArchive, Limits},
    remote_error::Severity,
};
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Presentation {
    pub error_type_description: String,
    pub high_value_title: Option<String>,
    pub low_value_title: Option<String>,
    pub additional_info: Option<String>,
    pub additional_diagnostics: Option<String>,
    pub options: Option<i64>,
    pub severity: Option<Severity>,
    pub is_potential_crash: bool,
    pub is_native: bool,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Error {
    TreeLimit,
    ByteLimit,
}
fn append(out: &mut String, text: &str, bytes: &mut usize) -> Result<(), Error> {
    *bytes = bytes.checked_sub(text.len()).ok_or(Error::ByteLimit)?;
    out.push_str(text);
    Ok(())
}
fn copy(text: &str, bytes: &mut usize) -> Result<String, Error> {
    let mut out = String::new();
    append(&mut out, text, bytes)?;
    Ok(out)
}
impl ErrorArchive {
    pub fn presentation(&self) -> Result<Presentation, Error> {
        self.presentation_with_limits(Limits::default(), 64 * 1024 * 1024)
    }
    /// Pure value aggregation, not native getter evaluation/callback order.
    /// Traverse main before cause; first-present optionals preserve Some("")
    /// and Some(0). Type names join all leaves with '.', present infos with ': '.
    /// Root wrappers have no additionalDiagnostics; standalone leaves retain it.
    /// Budgets cover archive nodes/depth and total returned UTF-8 string bytes.
    /// They are original policies, not native diagnostic/serialization limits.
    pub fn presentation_with_limits(
        &self,
        limits: Limits,
        mut bytes: usize,
    ) -> Result<Presentation, Error> {
        let mut report = Presentation {
            error_type_description: String::new(),
            high_value_title: None,
            low_value_title: None,
            additional_info: None,
            additional_diagnostics: None,
            options: None,
            severity: None,
            is_potential_crash: false,
            is_native: false,
        };
        let leaf_root = matches!(self, Self::Leaf(_));
        let mut nodes = limits.nodes;
        let mut first = true;
        let mut pending = vec![(self, 0usize)];
        while let Some((node, depth)) = pending.pop() {
            if nodes == 0 || depth > limits.depth {
                return Err(Error::TreeLimit);
            }
            nodes -= 1;
            match node {
                Self::Wrapper { main, underlying } => {
                    pending.push((underlying, depth + 1));
                    pending.push((main, depth + 1));
                }
                Self::Leaf(leaf) => {
                    if !first {
                        append(&mut report.error_type_description, ".", &mut bytes)?;
                    }
                    append(
                        &mut report.error_type_description,
                        &leaf.error_type_description,
                        &mut bytes,
                    )?;
                    if report.high_value_title.is_none() {
                        if let Some(text) = &leaf.high_value_title {
                            report.high_value_title = Some(copy(text, &mut bytes)?);
                        }
                    }
                    if report.low_value_title.is_none() {
                        if let Some(text) = &leaf.low_value_title {
                            report.low_value_title = Some(copy(text, &mut bytes)?);
                        }
                    }
                    if let Some(text) = &leaf.additional_info {
                        if let Some(info) = &mut report.additional_info {
                            append(info, ": ", &mut bytes)?;
                            append(info, text, &mut bytes)?;
                        } else {
                            report.additional_info = Some(copy(text, &mut bytes)?);
                        }
                    }
                    if leaf_root {
                        if let Some(text) = &leaf.additional_diagnostics {
                            report.additional_diagnostics = Some(copy(text, &mut bytes)?);
                        }
                    }
                    report.options = report.options.or(leaf.options);
                    report.severity = report.severity.or(leaf.severity);
                    if first {
                        report.is_native = leaf.is_native;
                    }
                    report.is_potential_crash = leaf.is_potential_crash;
                    first = false;
                }
            }
        }
        Ok(report)
    }
}
