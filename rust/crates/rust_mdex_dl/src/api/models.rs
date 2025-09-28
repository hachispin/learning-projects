//! Contains the `Manga` and `Chapter` structs
//! which model the corresponding API responses.

#![allow(unused)]

use std::{collections::HashMap, fs};

use crate::{Endpoint, api::client::ApiClient, deserializers::*};

use chrono::{DateTime, Utc};
use isolang::Language;
use miette::{ErrReport, IntoDiagnostic, Result};
use reqwest::Url;
use serde::{self, Deserialize};
use serde_json::Deserializer;
use toml::value::Date;
use uuid::Uuid;

/// For storing `contentRating` field in [`MangaAttributes::content_rating`]
///
/// Reference: https://api.mangadex.org/docs/3-enumerations/#manga-content-rating
#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum ContentRating {
    Safe,
    Suggestive,
    Erotica,
    Pornographic,
}

/// For storing `status` field in [`MangaAttributes::status`]
///
/// Reference: https://api.mangadex.org/docs/3-enumerations/#manga-status
#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Status {
    Ongoing,
    Completed,
    Hiatus,
    Cancelled,
}

/// For storing `state` field in [`MangaAttributes::state`]
///
/// Reference: https://api.mangadex.org/docs/redoc.html#tag/Manga/operation/get-manga-id
#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum State {
    Draft,
    Submitted,
    Published,
    Rejected,
}

#[derive(Deserialize, Debug, Clone)]
pub struct Relationship {
    #[serde(deserialize_with = "deserialize_uuid")]
    id: Uuid,

    #[serde(rename = "type")]
    pub type_: String,
}

#[derive(Deserialize, Debug, Clone)]
#[serde(rename_all = "camelCase")]
pub struct ChapterAttributes {
    pub volume: Option<String>,
    pub chapter: Option<String>,
    pub title: Option<String>,

    #[serde(deserialize_with = "deserialize_langcode")]
    pub translated_language: Language,

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
    pub async fn new(client: &ApiClient, chapter_uuid: Uuid) -> Result<Self> {
        let r_json = client
            .get_ok_json(Endpoint::GetChapter(chapter_uuid))
            .await?;

        serde_json::from_value::<Self>(r_json).into_diagnostic()
    }

    /// Returns the UUID.
    pub fn uuid(&self) -> Uuid {
        self.data.id
    }
}

#[derive(Deserialize, Debug, Clone)]
pub struct TagAttributes {
    #[serde(deserialize_with = "deserialize_langcode_map")]
    pub name: HashMap<Language, String>,
}

/// Omitted fields:
///
/// * attributes.description
/// * attributes.version
/// * relationships
///
/// These are omitted because they are either
/// always empty or store no useful information.
#[derive(Deserialize, Debug, Clone)]
pub struct Tag {
    #[serde(deserialize_with = "deserialize_uuid")]
    id: Uuid,

    #[serde(rename = "type")]
    pub type_: String,

    pub attributes: TagAttributes,
}

#[derive(Deserialize, Debug, Clone)]
#[serde(rename_all = "camelCase")]
pub struct MangaAttributes {
    #[serde(deserialize_with = "deserialize_langcode_map")]
    pub title: HashMap<Language, String>,

    #[serde(deserialize_with = "deserialize_langcode_map_vec")]
    pub alt_titles: Vec<HashMap<Language, String>>,

    #[serde(deserialize_with = "deserialize_langcode_map")]
    pub description: HashMap<Language, String>,

    pub is_locked: bool,
    // TODO: make this (or these?) an enum
    // https://api.mangadex.org/docs/3-enumerations/#manga-links-data
    pub links: HashMap<String, String>,
    pub official_links: Option<HashMap<String, String>>,
    #[serde(deserialize_with = "deserialize_langcode")]
    pub original_language: Language,

    pub last_volume: Option<String>,
    pub last_chapter: Option<String>,
    pub publication_demographic: Option<String>,
    pub status: Status,
    pub year: Option<usize>,
    pub content_rating: ContentRating,
    pub tags: Vec<Tag>,
    pub state: State,
    pub chapter_numbers_reset_on_new_volume: bool,

    #[serde(deserialize_with = "deserialize_utc_datetime")]
    pub created_at: DateTime<Utc>,

    #[serde(deserialize_with = "deserialize_utc_datetime")]
    pub updated_at: DateTime<Utc>,

    pub version: usize,
}

#[derive(Deserialize, Debug, Clone)]
pub struct MangaData {
    #[serde(deserialize_with = "deserialize_uuid")]
    id: Uuid,

    #[serde(rename = "type")]
    pub type_: String,

    pub attributes: MangaAttributes,
    pub relationships: Vec<Relationship>,
}

#[derive(Deserialize, Debug, Clone)]
pub struct Manga {
    pub data: MangaData,
}

impl Manga {
    /// Takes the given `manga_uuid` and makes a GET request to [`Endpoint::GetChapter`],
    /// parsing the response as a [`Chapter`] using [`serde`] and returning it.
    pub async fn new(client: &ApiClient, manga_uuid: Uuid) -> Result<Self> {
        let r_json = client.get_ok_json(Endpoint::GetManga(manga_uuid)).await?;
        serde_json::from_value::<Self>(r_json).into_diagnostic()
    }
}
