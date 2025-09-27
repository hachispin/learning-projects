//! Contains file locations and other file-related utilities.

use std::path::{Path, PathBuf};
use std::sync::LazyLock;

static PROJECT_ROOT: LazyLock<PathBuf> = LazyLock::new(|| {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .canonicalize()
        .expect("failed to canonicalise project root path")
});

static MANGA_SAVE: LazyLock<PathBuf> = LazyLock::new(|| PROJECT_ROOT.join("manga"));
static LOG_SAVE: LazyLock<PathBuf> = LazyLock::new(|| PROJECT_ROOT.join("log"));
static CONFIG: LazyLock<PathBuf> = LazyLock::new(|| PROJECT_ROOT.join("config.toml"));

/// NOTE: This currently uses the `"CARGO_MANIFEST_DIR"` environment variable.
///
/// This environment variable doesn't exist in release binaries.

pub fn manga_save_dir() -> &'static Path {
    &MANGA_SAVE
}
pub fn log_save_dir() -> &'static Path {
    &LOG_SAVE
}
pub fn config_toml() -> &'static Path {
    &CONFIG
}
