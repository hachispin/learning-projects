//! Contains file locations and other file-related utilities.

use miette::{IntoDiagnostic, Result};
use std::path::PathBuf;

#[must_use]
pub fn manga_save_dir() -> Result<PathBuf> {
    Ok(std::env::current_dir().into_diagnostic()?.join("manga"))
}

#[must_use]
pub fn log_save_dir() -> Result<PathBuf> {
    Ok(std::env::current_dir().into_diagnostic()?.join("logs"))
}

#[must_use]
pub fn config_toml() -> Result<PathBuf> {
    // maybe use ~/.config?
    Ok(std::env::current_dir()
        .into_diagnostic()?
        .join("config_rust_mdex_dl.toml"))
}
