//! Loads the [config](`crate::paths::config_toml`) and validates
//! options using [`serde`] and [`toml`].

use crate::{
    deserializers::{deserialize_langcode, deserialize_logging_filter},
    paths::{config_toml, log_save_dir, manga_save_dir},
};

use std::fs;

use isolang::Language;
use miette::{self, IntoDiagnostic, Result};
use reqwest::Url;
use serde::Deserialize;
use toml;

/*    For config fields with set options    */
/*  Consider attempting to apply DRY later  */

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum SaveFormat {
    Raw,
    ComicBookZip,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum ImageQuality {
    Lossless,
    Lossy,
}

#[derive(Deserialize, Debug, Clone)]
pub struct Client {
    pub base_url: Url,
    pub user_agent: String,
    pub max_retries: u32,
    #[serde(deserialize_with = "deserialize_langcode")]
    pub language: Language,
}

#[derive(Deserialize, Debug, Clone)]
pub struct Concurrency {
    // semaphores take `usize`, so don't use `u32` here
    pub image_permits: usize,
    pub chapter_permits: usize,
}

#[derive(Deserialize, Debug, Clone)]
pub struct Images {
    pub quality: ImageQuality,
    pub save_format: SaveFormat,
}

#[derive(Deserialize, Debug, Clone)]
pub struct Logging {
    pub enabled: bool,
    #[serde(deserialize_with = "deserialize_logging_filter")]
    pub filter: log::LevelFilter,
}

#[derive(Deserialize, Debug, Clone)]
pub struct Config {
    pub client: Client,
    pub concurrency: Concurrency,
    pub images: Images,
    pub logging: Logging,
}

/// Loads the config stored in [`config_toml()`](`crate::paths::config_toml()`)
///
/// This also creates any dirs stored in [`crate::paths`] such as [`manga_save_dir()`](`crate::paths::manga_save_dir()`)
///
/// ## Errors
///
/// If some options fail extra validation,
/// such as `image_permits` being zero.
pub fn load_config() -> Result<Config> {
    let path = config_toml().canonicalize().into_diagnostic()?;
    let raw_cfg = fs::read_to_string(path).into_diagnostic()?;
    let cfg: Config = toml::de::from_str(&raw_cfg).into_diagnostic()?;

    let non_zero_options: [(&str, usize); 3] = [
        ("max_retries", cfg.client.max_retries as usize),
        ("image_permits", cfg.concurrency.image_permits),
        ("chapter_permits", cfg.concurrency.chapter_permits),
    ];
    for (option, value) in non_zero_options {
        if value == 0 {
            return Err(miette::miette!(
                "Expected option `{option}` to be non-zero, got {option}={value}"
            ));
        }
    }

    for p in [manga_save_dir(), log_save_dir()] {
        fs::create_dir_all(p).into_diagnostic()?;
    }

    Ok(cfg)
}
