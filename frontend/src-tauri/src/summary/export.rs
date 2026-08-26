//! Mirrors the generated meeting summary into the meeting folder so an exported
//! folder is self-contained (audio.mp4 + transcripts.json + metadata.json + summary.md).

use anyhow::{Context, Result};
use serde_json::Value;
use std::path::{Path, PathBuf};

use super::metadata::update_metadata_fields;

pub(crate) const SUMMARY_FILE: &str = "summary.md";
const SUMMARY_TEMP_FILE_PREFIX: &str = ".summary.md.";
const SUMMARY_FILE_FIELD: &str = "summary_file";

/// Writes the summary as a standalone Markdown document in `folder` and records
/// the file name in metadata.json.
///
/// The stored summary has its H1 stripped (the title lives in `meetings.title`),
/// so the title is prepended back when the markdown does not already carry one.
pub(crate) fn write_summary_markdown(
    folder: &Path,
    title: Option<&str>,
    markdown: &str,
) -> Result<()> {
    if !folder.exists() {
        std::fs::create_dir_all(folder)
            .with_context(|| format!("Failed to create {}", folder.display()))?;
    }

    let document = build_summary_document(title, markdown);
    let summary_path = folder.join(SUMMARY_FILE);
    let temp_path = summary_temp_path(folder);

    std::fs::write(&temp_path, &document)
        .with_context(|| format!("Failed to write {}", temp_path.display()))?;
    std::fs::rename(&temp_path, &summary_path).with_context(|| {
        format!(
            "Failed to replace {} with {}",
            summary_path.display(),
            temp_path.display()
        )
    })?;

    update_metadata_fields(
        folder,
        &[(
            SUMMARY_FILE_FIELD,
            Some(Value::String(SUMMARY_FILE.to_string())),
        )],
    )?;

    Ok(())
}

fn build_summary_document(title: Option<&str>, markdown: &str) -> String {
    let body = markdown.trim();
    let title = title.map(str::trim).filter(|t| !t.is_empty());

    match title {
        Some(title) if !body.starts_with("# ") => format!("# {}\n\n{}\n", title, body),
        _ => format!("{}\n", body),
    }
}

fn summary_temp_path(folder: &Path) -> PathBuf {
    folder.join(format!(
        "{}{}.tmp",
        SUMMARY_TEMP_FILE_PREFIX,
        uuid::Uuid::new_v4()
    ))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn prepends_title_when_markdown_has_no_heading() {
        let doc = build_summary_document(Some("Riunione ATEX"), "**Sintesi**\nTesto");
        assert_eq!(doc, "# Riunione ATEX\n\n**Sintesi**\nTesto\n");
    }

    #[test]
    fn keeps_existing_heading() {
        let doc = build_summary_document(Some("Ignored"), "# Riunione ATEX\n\nTesto");
        assert_eq!(doc, "# Riunione ATEX\n\nTesto\n");
    }

    #[test]
    fn writes_file_and_records_it_in_metadata() {
        let dir = tempfile::tempdir().unwrap();
        std::fs::write(dir.path().join("metadata.json"), r#"{"version":"1.0"}"#).unwrap();

        write_summary_markdown(dir.path(), Some("Titolo"), "Corpo").unwrap();

        let summary = std::fs::read_to_string(dir.path().join(SUMMARY_FILE)).unwrap();
        assert_eq!(summary, "# Titolo\n\nCorpo\n");

        let metadata: Value =
            serde_json::from_str(&std::fs::read_to_string(dir.path().join("metadata.json")).unwrap())
                .unwrap();
        assert_eq!(metadata[SUMMARY_FILE_FIELD], "summary.md");
        assert_eq!(metadata["version"], "1.0");
    }

    #[test]
    fn creates_metadata_when_folder_has_none() {
        let dir = tempfile::tempdir().unwrap();

        write_summary_markdown(dir.path(), None, "# Titolo\n\nCorpo").unwrap();

        assert_eq!(
            std::fs::read_to_string(dir.path().join(SUMMARY_FILE)).unwrap(),
            "# Titolo\n\nCorpo\n"
        );
        assert!(dir.path().join("metadata.json").exists());
    }
}
