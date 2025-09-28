//! Loads `./config.toml` in `/src` and validates options.

#![allow(unused)]

use crate::paths::*;

use std::fs;
use std::path::{Path, PathBuf};

use miette::{self, ErrReport, IntoDiagnostic, Result};
use reqwest::Url;
use serde::Deserialize;
use toml::{self};

/* For config fields with set options       */
/* Consider attempting to apply DRY later   */

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum SaveFormat {
    Raw,
    ComicBookZip,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum ImageQuality {
    High,
    Low,
}

#[derive(Deserialize, Debug, Clone)]
pub struct Client {
    pub base_url: Url,
    pub user_agent: String,
}

#[derive(Deserialize, Debug, Clone)]
pub struct Concurrency {
    pub image_permits: usize,
    pub chapter_permits: usize,
}

#[derive(Deserialize, Debug, Clone)]
pub struct Images {
    pub quality: ImageQuality,
    pub save_format: SaveFormat,
}

#[derive(Deserialize, Debug, Clone)]
pub struct Config {
    pub client: Client,
    pub concurrency: Concurrency,
    pub images: Images,
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
