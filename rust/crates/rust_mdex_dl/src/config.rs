//! Loads the [config](`crate::paths::config_toml`) and validates
//! options using [`serde`] and [`toml`].

use crate::{
    deserializers::{deserialize_langcode, deserialize_logging_filter},
    paths::{config_toml, log_save_dir, manga_save_dir},
};

use std::fs;

use isolang::Language;
use miette::{IntoDiagnostic, Result, bail, miette};
use reqwest::Url;
use serde::Deserialize;
use toml;

const CONFIG_DEFAULT: &str = "\
# ==> For rust_mdex_dl
# Find defaults at: https://github.com/hachispin/learning-projects/blob/main/rust/crates/rust_mdex_dl/config.toml

# Client info used for:

# * `reqwest::ClientBuilder::new()`
# * `crate::Client` (which is just a reqwest::Client wrapper)

[client]
base_url = \"https://api.mangadex.org\"
user_agent = \"hachispin/learning-projects\"
max_retries = 3  # how many times to retry upon being ratelimited
language = \"en\"     # * must be an ISO 639-1 code, which are two letters long
                    #   https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes

# This how many of these can be processed (or \"permitted\") at the same time.
#
# e.g. `image_permits` means how many images can be
# downloaded and saved at any one point in time.
#
# To go more in depth, these are the number of permits set on the \"semaphores\".
# https://en.wikipedia.org/wiki/Semaphore_(programming)
#
# Setting these higher may result in faster downloads at the cost
# of possible being throttled or ratelimited by MangaDex.
[concurrency]
image_permits = 10      # * undocumented ratelimit but hard to hit unless done intentionally
                        #   https://api.mangadex.org/docs/2-limitations/#non-api-rate-limits
chapter_permits = 3     # * max is 40 reqs per minute for this endpoint
                        #   scale this against your download speed accordingly
                        #   https://api.mangadex.org/docs/2-limitations/#endpoint-specific-rate-limits

[images]
quality = \"lossless\"    # options: \"lossless\", \"lossy\"
save_format = \"raw\"     # not implemented yet, does nothing for now

[logging]
enabled = true
filter = \"DEBUG\"  # options: \"TRACE\", \"DEBUG\", \"INFO\", \"WARN\", \"ERROR\"
";

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
    let path = config_toml()?;

    if !path.try_exists().into_diagnostic()? {
        fs::write(&path, CONFIG_DEFAULT).map_err(|e| {
            miette!(
                "failed to write (default config) to {}: {e}",
                path.display()
            )
        })?;
    }

    let raw_cfg = fs::read_to_string(path).into_diagnostic()?;
    let cfg: Config = toml::de::from_str(&raw_cfg).into_diagnostic()?;

    let non_zero_options: [(&str, usize); 3] = [
        ("max_retries", cfg.client.max_retries as usize),
        ("image_permits", cfg.concurrency.image_permits),
        ("chapter_permits", cfg.concurrency.chapter_permits),
    ];

    for (option, value) in non_zero_options {
        if value == 0 {
            bail!("Expected option `{option}` to be non-zero, got {option}={value}");
        }
    }

    for p in [manga_save_dir(), log_save_dir()] {
        fs::create_dir_all(p?).into_diagnostic()?;
    }

    Ok(cfg)
}
