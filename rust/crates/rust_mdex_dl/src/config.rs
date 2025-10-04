//! Loads the [config](`crate::paths::config_toml`) and validates
//! options using [`serde`] and [`toml`].
//!
//! Since this is done before logs are set up, logging is
//! sent to stdout, then cleared as soon as it's done.

use crate::{
    deserializers::{deserialize_langcode, deserialize_logging_filter},
    paths::*,
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
    #[serde(deserialize_with = "deserialize_langcode")]
    pub language: Language,
}

#[allow(unused)]
#[derive(Deserialize, Debug, Clone)]
pub struct Concurrency {
    pub image_permits: usize,
    pub chapter_permits: usize,
}

#[allow(unused)]
#[derive(Deserialize, Debug, Clone)]
pub struct Images {
    pub quality: ImageQuality,
    pub save_format: SaveFormat,
}

#[allow(unused)]
#[derive(Deserialize, Debug, Clone)]
pub struct Logging {
    pub enabled: bool,
    #[serde(deserialize_with = "deserialize_logging_filter")]
    pub filter: log::LevelFilter,
}

#[allow(unused)]
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
pub fn load_config() -> Result<Config> {
    let path = config_toml().canonicalize().into_diagnostic()?;
    let raw_config = fs::read_to_string(path).into_diagnostic()?;

    println!("Raw config before deserialization:");
    println!("\n{raw_config}");
    println!("Deserializing config...");

    let config: Config = toml::de::from_str(&raw_config).into_diagnostic()?;

    println!("{config:?}");
    println!("Config loaded successfully!\n");

    for p in [manga_save_dir(), log_save_dir()] {
        println!("Creating save dir {p:?}");
        fs::create_dir_all(p).into_diagnostic()?;
        println!("Path {p:?} created successfully.")
    }

    println!("\nAll paths have been created!");
    println!("Your terminal should be clearing about now...");

    // NOTE: this way of clearing may not be supported on some terminals
    println!("{esc}c", esc = 27 as char);
    Ok(config)
}
