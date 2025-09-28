//! Contains the `Manga` and `Chapter` structs
//! which model the corresponding API responses.

#![allow(unused)]

use std::collections::HashMap;

use crate::{Endpoint, api::client::ApiClient, deserializers::*};

use chrono::{DateTime, Utc};
use isolang::Language;
use miette::{IntoDiagnostic, Result};
use reqwest::Url;
use serde::{self, Deserialize};
use uuid::Uuid;

#[derive(Deserialize, Debug, Clone)]
#[serde(rename_all = "camelCase")]
pub struct ChapterAttributes {
    pub volume: Option<String>,
    pub chapter: Option<String>,
    pub title: Option<String>,

    #[serde(deserialize_with = "deserialize_language_code")]
    pub translated_language: Language,

    #[serde(deserialize_with = "deserialize_url_maybe")]
    pub external_url: Option<Url>,

    pub is_unavailable: bool,

    #[serde(deserialize_with = "deserialize_utc_datetime")]
    pub publish_at: DateTime<Utc>,
    #[serde(deserialize_with = "deserialize_utc_datetime")]
    pub readable_at: DateTime<Utc>,
    #[serde(deserialize_with = "deserialize_utc_datetime")]
    pub created_at: DateTime<Utc>,

    pub pages: usize,
    pub version: usize,
}

#[derive(Deserialize, Debug, Clone)]
pub struct Relationship {
    #[serde(deserialize_with = "deserialize_uuid")]
    id: Uuid,

    #[serde(rename = "type")]
    pub type_: String,
}

#[derive(Deserialize, Debug, Clone)]
pub struct ChapterData {
    #[serde(deserialize_with = "deserialize_uuid")]
    id: Uuid,

    #[serde(rename = "type")]
    pub type_: String,

    pub attributes: ChapterAttributes,
    pub relationships: Vec<Relationship>,
}

/// Models the entire JSON response of [`Endpoint::GetChapter`] as a struct.
///
/// This also allows easy usage of [`serde::Deserialize`] for [`Self::new`].
#[derive(Deserialize, Debug, Clone)]
pub struct Chapter {
    pub data: ChapterData,
}

impl Chapter {
    /// Takes the given `chapter_uuid` and makes a GET request to [`Endpoint::GetChapter`],
    /// parsing the response as a [`Chapter`] using [`serde`] and returning it.
    pub async fn new(client: &ApiClient, chapter_uuid: Uuid) -> Result<Chapter> {
        let r_json = client
            .get_ok_json(Endpoint::GetChapter(chapter_uuid))
            .await?;

        serde_json::from_value::<Chapter>(r_json).into_diagnostic()
    }
}

#[derive(Deserialize, Debug, Clone)]
struct TagAttributes {
    #[serde(deserialize_with = "deserialize_language_code_map")]
    name: HashMap<Language, String>,
}

/// Omitted fields:
///
/// * attributes.description
/// * attributes.version
/// * relationships
///
/// These are omitted because they are nearly
/// always empty or store no useful information.
#[derive(Deserialize, Debug, Clone)]
struct Tag {
    #[serde(deserialize_with = "deserialize_uuid")]
    id: Uuid,

    #[serde(rename = "type")]
    type_: String,

    attributes: TagAttributes,
}

#[derive(Deserialize, Debug, Clone)]
#[serde(rename_all = "camelCase")]
struct MangaAttributes {
    #[serde(deserialize_with = "deserialize_language_code_map")]
    title: HashMap<Language, String>,

    #[serde(deserialize_with = "deserialize_language_code_map")]
    alt_titles: HashMap<Language, String>,

    #[serde(deserialize_with = "deserialize_language_code_map")]
    description: HashMap<Language, String>,

    is_locked: bool,

    // TODO: make this (or these?) an enum
    // https://api.mangadex.org/docs/3-enumerations/#manga-links-data
    links: HashMap<String, String>,
    official_links: Option<HashMap<String, String>>,

    #[serde(deserialize_with = "deserialize_language_code")]
    original_language: Language,

    last_volume: String,
    last_chapter: String,
    publication_demographic: Option<String>,
    status: String, // TODO: make enum
    year: usize,
    content_rating: String, // TODO: make enum
    tags: Vec<Tag>,
}
