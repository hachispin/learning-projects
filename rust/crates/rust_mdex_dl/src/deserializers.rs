//! Contains definitions for deserialize patterns with user-defined types.

use std::collections::HashMap;

use chrono::{DateTime, Utc};
use isolang::Language;
use log::LevelFilter;
use serde::Deserialize;
use uuid::Uuid;

/// Deserializer for [`LevelFilter`].
///
/// ## Errors
///
/// If initial deserilization as [`String`] fails, or
/// the isn't a valid logging level (e.g, "DEBUG").
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

/// Helper function to deserialize as [`Uuid`].
///
/// ## Errors
///
/// If initial deserilization as [`String`]
/// fails, or the string isn't a valid [`Uuid`].
pub fn deserialize_uuid<'de, D>(deserializer: D) -> Result<Uuid, D::Error>
where
    D: serde::Deserializer<'de>,
{
    let input_uuid = String::deserialize(deserializer)?;
    Uuid::parse_str(&input_uuid).map_err(serde::de::Error::custom)
}

/// Helper function to deserialize as [`DateTime<Utc>`]
///
/// The input is parsed as RFC 3339, in accordance with
/// [what MangaDex uses](https://api.mangadex.org/docs/01-concepts/timestamps/#timestamp-format).
///
/// ## Errors
///
/// If initial deserilization as [`String`] fails,
/// or the string isn't a valid RFC 3359 time.
pub fn deserialize_utc_datetime<'de, D>(deserializer: D) -> Result<DateTime<Utc>, D::Error>
where
    D: serde::Deserializer<'de>,
{
    let input_datetime = String::deserialize(deserializer)?;
    let parsed_datetime =
        DateTime::parse_from_rfc3339(&input_datetime).map_err(serde::de::Error::custom)?;

    Ok(parsed_datetime.to_utc())
}

/// shim for Manga-Dex's alpha-5 extensions used for titles.
///
/// ref: <https://api.mangadex.org/docs/3-enumerations/#language-codes--localization>
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

/// check <https://api.mangadex.org/manga/0c936660-cb06-491b-8b61-15dacad1bfb4> json for why
/// i just want to read my manga man
fn nullify_langcodes(langcode: &str) -> String {
    const UND_MAPPINGS: [&str; 4] = ["NULL", "Null", "null", ""];

    if UND_MAPPINGS.contains(&langcode) {
        return "UNKNOWN".to_string();
    }

    langcode.to_string()
}

/// Helper function to deserialize as [`Language`]
///
/// The input is parsed using the ISO 639-1 standard, in accordance with
/// [what MangaDex uses](https://api.mangadex.org/docs/3-enumerations/#language-codes--localization)
///
/// ## Errors
///
/// If initial deserilization as [`String`] fails, or
/// the string isn't a valid language code,
pub fn deserialize_langcode<'de, D>(deserializer: D) -> Result<Language, D::Error>
where
    D: serde::Deserializer<'de>,
{
    let input_langcode = nullify_langcodes(&narrow_langcodes(&String::deserialize(deserializer)?));

    if input_langcode == "UNKNOWN" {
        return Ok(Language::Und);
    }

    Language::from_639_1(input_langcode.as_str()).ok_or(serde::de::Error::custom(format!(
        "invalid iso 639-1 language code {input_langcode:?}"
    )))
}

/// Helper function to deserialize as [`HashMap<Language, String>`].
/// This pattern appears quite often, especially in places like descriptions.
///
/// The input is parsed using the ISO 639-1 standard, in accordance with
/// [what MangaDex uses](https://api.mangadex.org/docs/3-enumerations/#language-codes--localization)
///
/// ## Errors
///
/// If initial deserilization as [`HashMap<String, String>`]
///  fails, or the hashmap's keys aren't valid language codes.
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
            let k = nullify_langcodes(&narrow_langcodes(&k));

            if k == "UNKNOWN" {
                return Ok((Language::Und, v));
            }

            let lang = Language::from_639_1(&k).ok_or_else(|| {
                serde::de::Error::custom(format!("invalid iso 639-1 language code {k:?}"))
            })?;
            Ok((lang, v))
        })
        .collect()
}

/// Deserializes to [`Vec<HashMap<Language, String>>`].
///
/// ## Errors
///
/// If initial deserialization as [`Vec<Hashmap<String, String>>`] fails,
/// or any of the contained hashmaps; keys aren't valid language codes.
pub fn deserialize_langcode_map_vec<'de, D>(
    deserializer: D,
) -> Result<Vec<HashMap<Language, String>>, D::Error>
where
    D: serde::Deserializer<'de>,
{
    let input_map_vec: Vec<HashMap<String, String>> = Vec::deserialize(deserializer)?;
    let mut mappings: Vec<HashMap<Language, String>> = Vec::with_capacity(input_map_vec.len() + 1);

    for map in input_map_vec {
        let mut current = HashMap::with_capacity(map.len() + 1);

        for (k, v) in map {
            let k = nullify_langcodes(&narrow_langcodes(&k));
            if k == "UNKNOWN" {
                current.insert(Language::Und, v);
                continue;
            }

            let lang = Language::from_639_1(&k).ok_or_else(|| {
                serde::de::Error::custom(format!("invalid iso 639-1 language code {k:?}"))
            })?;

            current.insert(lang, v);
        }
        mappings.push(current);
    }
    Ok(mappings)
}
