//! Loads `./config.toml` in `/src` and validates options.

#![allow(unused)]

use crate::deserialize_custom::{deserialize_enum, deserialize_url};
use crate::paths::*;

use std::fs;
use std::path::{Path, PathBuf};

use miette::{self, ErrReport, IntoDiagnostic, Result};
use reqwest::Url;
use serde::Deserialize;
use toml::{self};

/* For config fields with set options       */
/* Consider attempting to apply DRY later   */

#[derive(Debug, Clone)]
pub enum SaveFormat {
    Raw,
    ComicBookZip,
}

#[derive(Debug, Clone)]
pub enum ImageQuality {
    High,
    Low,
}

impl TryFrom<String> for SaveFormat {
    type Error = ErrReport;

    fn try_from(s: String) -> Result<Self, Self::Error> {
        match s.to_ascii_lowercase().trim() {
            "raw" => Ok(SaveFormat::Raw),
            "cbz" => Ok(SaveFormat::ComicBookZip),
            _ => Err(miette::miette!(format!(
                "expected `save_format` config field to be either \"raw\" or \"cbz\", instead got {s:?}"
            ))),
        }
    }
}

impl TryFrom<String> for ImageQuality {
    type Error = ErrReport;

    fn try_from(s: String) -> Result<Self, Self::Error> {
        match s.to_ascii_lowercase().trim() {
            "high" => Ok(ImageQuality::High),
            "low" => Ok(ImageQuality::Low),
            _ => Err(miette::miette!(format!(
                "expected `quality` config field to be either \"high\" or \"low\", instead got {s:?}"
            ))),
        }
    }
}

#[derive(Deserialize, Debug, Clone)]
pub struct Client {
    #[serde(deserialize_with = "deserialize_url")]
    pub base_url: Url,
    pub user_agent: String,
}

#[derive(Deserialize, Debug, Clone)]
pub struct Concurrency {
    pub image_permits: usize,
    pub chapter_permits: usize,
}

#[derive(Deserialize, Debug, Clone)]
pub struct Config {
    pub client: Client,
    pub concurrency: Concurrency,
}

#[derive(Deserialize, Debug, Clone)]
pub struct Images {
    #[serde(deserialize_with = "deserialize_enum")]
    pub quality: ImageQuality,
    #[serde(deserialize_with = "deserialize_enum")]
    pub save_format: SaveFormat,
}

/// Loads the config stored in [`config_toml()`](`crate::paths::config_toml()`)
///
/// This also creates any dirs stored in [`crate::paths`] such as [`manga_save_dir()`](`crate::paths::manga_save_dir()`)
pub fn load_config() -> Result<Config> {
    let path = config_toml().canonicalize().into_diagnostic()?;
    let raw_config = fs::read_to_string(path).into_diagnostic()?;
    let config: Config = toml::de::from_str(&raw_config).into_diagnostic()?;

    for p in [manga_save_dir(), log_save_dir()] {
        fs::create_dir_all(p).into_diagnostic()?;
    }

    Ok(config)
}
