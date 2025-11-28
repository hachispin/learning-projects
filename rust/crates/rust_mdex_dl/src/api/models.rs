//! Contains the [`Manga`] and [`Chapter`] structs
//! which model the corresponding API responses.

use std::collections::HashMap;

use crate::{
    api::{client::ApiClient, endpoints::Endpoint},
    deserializers::{
        // "don't use wildcard import" they said...
        deserialize_langcode,
        deserialize_langcode_map,
        deserialize_langcode_map_vec,
        deserialize_utc_datetime,
        deserialize_uuid,
    },
};

use chrono::{DateTime, Utc};
use isolang::Language;
use log::warn;
use miette::{IntoDiagnostic, Result};
use reqwest::Url;
use serde::{self, Deserialize};
use uuid::Uuid;

/// For storing `contentRating` field in [`MangaAttributes::content_rating`]
///
/// Reference: <https://api.mangadex.org/docs/3-enumerations/#manga-content-rating>

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
/// Reference: <https://api.mangadex.org/docs/3-enumerations/#manga-status>
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
/// Reference: <https://api.mangadex.org/docs/redoc.html#tag/Manga/operation/get-manga-id>
#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum State {
    Draft,
    Submitted,
    Published,
    Rejected,
}

/// For storing `publication_demographic` field in [`MangaAttributes::publication_demographic`]
///
/// Reference: <https://api.mangadex.org/docs/3-enumerations/#manga-publication-demographic>
#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum PublicationDemographic {
    Shounen,
    Shoujo,
    Josei,
    Seinen,
}

#[derive(Deserialize, Debug, Clone)]
pub struct Relationship {
    #[serde(deserialize_with = "deserialize_uuid")]
    id: Uuid,

    #[serde(rename = "type")]
    pub type_: String,
}

impl Relationship {
    #[must_use]
    pub fn uuid(&self) -> Uuid {
        self.id
    }
}

#[allow(unused)]
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
    pub version: u32,
}

#[allow(unused)]
#[derive(Deserialize, Debug, Clone)]
pub struct ChapterData {
    #[serde(deserialize_with = "deserialize_uuid")]
    pub id: Uuid,

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
    ///
    /// ## Panics
    ///
    /// If the JSON received does not have the data type "chapter".
    ///
    /// ## Errors
    ///
    /// If propagated from [`ApiClient::get_ok_json`].
    pub async fn new(client: &ApiClient, chapter_uuid: Uuid) -> Result<Self> {
        let r_json = client
            .get_ok_json(Endpoint::GetChapter(chapter_uuid))
            .await?;

        let chapter = serde_json::from_value::<Self>(r_json).into_diagnostic()?;
        assert!(chapter.data.type_ == "chapter");

        Ok(chapter)
    }

    /// Allows constructing of [`Chapter`] from [`ChapterData`].
    #[must_use] 
    pub fn from_data(data: ChapterData) -> Self {
        Self { data }
    }

    /// Returns a formatted chapter title such as:
    ///
    /// `[011] I broke through`
    ///
    /// Zero-padding is fixed to three characters because getting
    /// the highest chapter number is a little tricky from here.
    #[must_use] 
    pub fn formatted_title(&self) -> String {
        let title = self.data.attributes.title.clone().unwrap_or_default();

        let num = self
            .data
            .attributes
            .chapter
            .clone()
            .unwrap_or("---".to_string());

        // prevent naming conflicts
        let suffix = &self.data.id.to_string()[..8];

        if title.is_empty() {
            format!("[{num:0>3}] ({suffix})")
        } else {
            format!("[{num:0>3}] {title} ({suffix})")
        }
    }

    /// Iterates over [relationships](`ChapterData::relationships`) until the parent
    /// manga is found.
    ///
    /// ## Panics
    /// 
    /// This panics with [`Option::expect`] if the manga can't be found.
    #[must_use] 
    pub fn parent_uuid(&self) -> Uuid {
        // the "manga" field is usually in relationships[1] but this is more reliable
        self.data
            .relationships
            .iter()
            .find(|r| r.type_ == "manga")
            .expect("no parent manga found") // should be unreachable
            .uuid()
    }

    /// UUID getter
    #[must_use] 
    pub fn uuid(&self) -> Uuid {
        self.data.id
    }
}

#[allow(unused)]
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
#[allow(unused)]
#[derive(Deserialize, Debug, Clone)]
pub struct Tag {
    #[serde(deserialize_with = "deserialize_uuid")]
    id: Uuid,

    #[serde(rename = "type")]
    pub type_: String,

    pub attributes: TagAttributes,
}

#[allow(unused)]
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
    pub links: Option<HashMap<String, String>>,
    pub official_links: Option<HashMap<String, String>>,
    #[serde(deserialize_with = "deserialize_langcode")]
    pub original_language: Language,

    pub last_volume: Option<String>,
    pub last_chapter: Option<String>,
    pub publication_demographic: Option<PublicationDemographic>,
    pub status: Status,
    pub year: Option<u32>,
    pub content_rating: ContentRating,
    pub tags: Vec<Tag>,
    pub state: State,
    pub chapter_numbers_reset_on_new_volume: bool,

    #[serde(deserialize_with = "deserialize_utc_datetime")]
    pub created_at: DateTime<Utc>,

    #[serde(deserialize_with = "deserialize_utc_datetime")]
    pub updated_at: DateTime<Utc>,

    pub version: u32,
}

#[allow(unused)]
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
    /// Takes the given `manga_uuid` and makes a GET request to [`Endpoint::GetManga`],
    /// parsing the response as a [`Manga`] using [`serde`] and returning it.
    /// 
    /// ## Panics
    /// 
    /// If the data type received isn't of type "manga".
    /// 
    /// ## Errors
    /// 
    /// If the response can't be parsed as a [`Manga`].
    pub async fn new(client: &ApiClient, manga_uuid: Uuid) -> Result<Self> {
        let r_json = client.get_ok_json(Endpoint::GetManga(manga_uuid)).await?;
        let manga = serde_json::from_value::<Self>(r_json).into_diagnostic()?;
        assert!(manga.data.type_ == "manga");

        Ok(manga)
    }

    /// Allows constructing of [`Manga`] from [`MangaData`].
    #[must_use] 
    pub fn from_data(data: MangaData) -> Self {
        Self { data }
    }

    /// Helper for accessing title field given a language. This
    /// searches through the `title` and `alt_titles` fields.
    ///
    /// Defaults to the first title in [`MangaAttributes::title`]
    /// if the language provided wasn't available.
    /// 
    /// ## Panics
    /// 
    /// If no title whatsoever exists for this manga.
    #[must_use] 
    pub fn title(&self, language: Language) -> String {
        // check normal titles
        if let Some(v) = self.data.attributes.title.get(&language) {
            return v.clone();
        }

        // check alt titles
        for map in &self.data.attributes.alt_titles {
            for (k, v) in map {
                if *k == language {
                    return v.clone();
                }
            }
        }

        warn!(
            concat!(
                "Could not find a title in both `title` and `alt_titles`",
                " for language {:?}, falling back to any available title"
            ),
            language.to_name()
        );

        // fallback to first normal title
        self.data
            .attributes
            .title
            .values()
            .next()
            .cloned()
            .expect("fallback title failed; no title found")
    }

    /// UUID getter
    #[must_use] 
    pub fn uuid(&self) -> Uuid {
        self.data.id
    }
}
