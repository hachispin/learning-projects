//! Contains file locations and other file-related utilities.

#![allow(clippy::missing_errors_doc)]

use miette::{IntoDiagnostic, Result};
use std::path::PathBuf;

pub fn manga_save_dir() -> Result<PathBuf> {
    Ok(std::env::current_dir().into_diagnostic()?.join("manga"))
}

pub fn log_save_dir() -> Result<PathBuf> {
    Ok(std::env::current_dir().into_diagnostic()?.join("logs"))
}

pub fn config_toml() -> Result<PathBuf> {
    // maybe use ~/.config?
    Ok(std::env::current_dir()
        .into_diagnostic()?
        .join("config_rust_mdex_dl.toml"))
}
