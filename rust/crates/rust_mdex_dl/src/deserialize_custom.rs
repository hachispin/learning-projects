//! Contains definitons for deserialize patterns with user-defined types

use chrono::{DateTime, Utc};
use isolang::Language;
use miette::ErrReport;
use reqwest::Url;
use serde::Deserialize;
use uuid::Uuid;

/// Helper function to deserialize as [`Url`]
pub fn deserialize_url<'de, D>(deserializer: D) -> Result<Url, D::Error>
where
    D: serde::Deserializer<'de>,
{
    let input_url = String::deserialize(deserializer)?
        .trim_matches('/')
        .to_string();

    Url::parse(&input_url).map_err(serde::de::Error::custom)
}

pub fn deserialize_url_maybe<'de, D>(deserializer: D) -> Result<Option<Url>, D::Error>
where
    D: serde::Deserializer<'de>,
{
    Ok(deserialize_url(deserializer).ok())
}

/// Generic helper function to deserialize enums.
///
/// The enum must have [`TryFrom<String>`] implemented.
pub fn deserialize_enum<'de, D, T>(deserializer: D) -> Result<T, D::Error>
where
    D: serde::Deserializer<'de>,
    T: TryFrom<String, Error = ErrReport>,
{
    let s = String::deserialize(deserializer)?;
    s.try_into().map_err(serde::de::Error::custom)
}

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
