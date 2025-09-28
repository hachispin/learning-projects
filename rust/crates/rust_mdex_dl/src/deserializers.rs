//! Contains definitons for deserialize patterns with user-defined types

use std::collections::HashMap;

use chrono::{DateTime, Utc};
use isolang::Language;
use serde::Deserialize;
use uuid::Uuid;

/// Helper function to deserialize as [`Uuid`]
pub fn deserialize_uuid<'de, D>(deserializer: D) -> Result<Uuid, D::Error>
where
    D: serde::Deserializer<'de>,
{
    let input_uuid = String::deserialize(deserializer)?
        .trim()
        .to_ascii_lowercase();

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

/// Helper function to deserialize as [`Language`]
///
/// The input is parsed using the ISO 639-1 standard, in accordance with
/// [what MangaDex uses](https://api.mangadex.org/docs/3-enumerations/#language-codes--localization)
pub fn deserialize_language_code<'de, D>(deserializer: D) -> Result<Language, D::Error>
where
    D: serde::Deserializer<'de>,
{
    let input_langcode = String::deserialize(deserializer)?;

    Language::from_639_1(&input_langcode.as_str()).ok_or(serde::de::Error::custom(format!(
        "invalid iso 639-1 language code {input_langcode:?}"
    )))
}

/// Helper function to deserialize as [`HashMap<Language, String>`].
/// This pattern appears quite often, especially in places like descriptions.
///
/// The input is parsed using the ISO 639-1 standard, in accordance with
/// [what MangaDex uses](https://api.mangadex.org/docs/3-enumerations/#language-codes--localization)
pub fn deserialize_language_code_map<'de, D>(
    deserializer: D,
) -> Result<HashMap<Language, String>, D::Error>
where
    D: serde::Deserializer<'de>,
{
    let input_map: HashMap<String, String> = HashMap::deserialize(deserializer)?;

    // `ok_or_else()` is used because `ok_or()`
    // requires turbofish hell with generic types
    input_map
        .into_iter()
        .map(|(k, v)| {
            let lang = Language::from_639_1(&k).ok_or_else(|| {
                serde::de::Error::custom(format!("invalid iso 639-1 language code {k:?}"))
            })?;
            Ok((lang, v))
        })
        .collect()
}
