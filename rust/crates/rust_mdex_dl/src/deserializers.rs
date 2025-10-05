//! Contains definitions for deserialize patterns with user-defined types.

use std::collections::HashMap;

use chrono::{DateTime, Utc};
use isolang::Language;
use log::LevelFilter;
use serde::Deserialize;
use uuid::Uuid;

pub fn deserialize_logging_filter<'de, D>(deserializer: D) -> Result<LevelFilter, D::Error>
where
    D: serde::Deserializer<'de>,
{
    let input_level = String::deserialize(deserializer)?;

    match input_level.as_str() {
        "TRACE" => Ok(LevelFilter::Trace),
        "DEBUG" => Ok(LevelFilter::Debug),
        "INFO" => Ok(LevelFilter::Info),
        "WARN" => Ok(LevelFilter::Warn),
        "ERROR" => Ok(LevelFilter::Error),
        _ => Err(serde::de::Error::custom(format!(
            "invalid logging level {input_level:?}"
        ))),
    }
}

/// Helper function to deserialize as [`Uuid`]
pub fn deserialize_uuid<'de, D>(deserializer: D) -> Result<Uuid, D::Error>
where
    D: serde::Deserializer<'de>,
{
    let input_uuid = String::deserialize(deserializer)?;
    Uuid::parse_str(&input_uuid).map_err(|e| serde::de::Error::custom(e))
}

/// Helper function to deserialize as [`DateTime<Utc>`]
///
/// The input is parsed as RFC 3339, in accordance with
/// [what MangaDex uses](https://api.mangadex.org/docs/01-concepts/timestamps/#timestamp-format).
pub fn deserialize_utc_datetime<'de, D>(deserializer: D) -> Result<DateTime<Utc>, D::Error>
where
    D: serde::Deserializer<'de>,
{
    let input_datetime = String::deserialize(deserializer)?;
    let parsed_datetime =
        DateTime::parse_from_rfc3339(&input_datetime).map_err(|e| serde::de::Error::custom(e))?;

    Ok(parsed_datetime.to_utc())
}

/// shim for MangaDex's alpha-5 extensions used for titles.
///
/// ref: https://api.mangadex.org/docs/3-enumerations/#language-codes--localization
///
/// TODO: find a better way of doing this
fn narrow_langcodes(langcode: &str) -> String {
    match langcode {
        "zh-ro" | "ja-ro" | "ko-ro" => "en", // language-romanized => eng
        "zh-hk" => "zh",                     // remove simplified/traditional distinction
        "pt-br" => "pt",                     // brazilian portugese => portugese
        "es-la" => "es",                     // latam spanish => spanish
        _ => langcode,
    }
    .to_string()
}

/// Helper function to deserialize as [`Language`]
///
/// The input is parsed using the ISO 639-1 standard, in accordance with
/// [what MangaDex uses](https://api.mangadex.org/docs/3-enumerations/#language-codes--localization)
pub fn deserialize_langcode<'de, D>(deserializer: D) -> Result<Language, D::Error>
where
    D: serde::Deserializer<'de>,
{
    let input_langcode = narrow_langcodes(&String::deserialize(deserializer)?);

    Language::from_639_1(input_langcode.as_str()).ok_or(serde::de::Error::custom(format!(
        "invalid iso 639-1 language code {input_langcode:?}"
    )))
}

/// Helper function to deserialize as [`HashMap<Language, String>`].
/// This pattern appears quite often, especially in places like descriptions.
///
/// The input is parsed using the ISO 639-1 standard, in accordance with
/// [what MangaDex uses](https://api.mangadex.org/docs/3-enumerations/#language-codes--localization)
pub fn deserialize_langcode_map<'de, D>(
    deserializer: D,
) -> Result<HashMap<Language, String>, D::Error>
where
    D: serde::Deserializer<'de>,
{
    let input_map: HashMap<String, String> = HashMap::deserialize(deserializer)?;

    input_map
        .into_iter()
        .map(|(k, v)| {
            let k = narrow_langcodes(&k);
            let lang = Language::from_639_1(&k).ok_or_else(|| {
                serde::de::Error::custom(format!("invalid iso 639-1 language code {k:?}"))
            })?;
            Ok((lang, v))
        })
        .collect()
}

/// Deserializes to [`Vec<HashMap<Language, String>>`]
pub fn deserialize_langcode_map_vec<'de, D>(
    deserializer: D,
) -> Result<Vec<HashMap<Language, String>>, D::Error>
where
    D: serde::Deserializer<'de>,
{
    let mut mappings: Vec<HashMap<Language, String>> = Vec::new();
    let input_map_vec: Vec<HashMap<String, String>> = Vec::deserialize(deserializer)?;

    for map in input_map_vec {
        let mut current = HashMap::new();

        for (k, v) in map {
            let k = narrow_langcodes(&k);
            let lang = Language::from_639_1(&k).ok_or_else(|| {
                serde::de::Error::custom(format!("invalid iso 639-1 language code {k:?}"))
            })?;

            current.insert(lang, v);
        }
        mappings.push(current);
    }
    Ok(mappings)
}
