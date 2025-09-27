//! Contains the `Manga` and `Chapter` structs
//! which model the corresponding API responses.

#![allow(unused)]

use crate::{
    Endpoint,
    api::client::ApiClient,
    deserialize_custom::{
        deserialize_language_code, deserialize_url, deserialize_url_maybe,
        deserialize_utc_datetime, deserialize_uuid,
    },
};

use chrono::{DateTime, Utc};
use isolang::Language;
use miette::{IntoDiagnostic, Result};
use reqwest::Url;
use serde::{self, Deserialize};
use uuid::Uuid;

/*
{
  "data": {
    "id": "c0c57b41-4d7d-4dd3-b3e2-90aeab080db2",
    "type": "chapter",
    "relationships": [
      {
        "id": "ee472231-6e83-402c-a8eb-2ec015fb1e68",
        "type": "scanlation_group"
      },
      {
        "id": "46748d60-9b15-4647-8250-de0926b20268",
        "type": "manga"
      },
      {
        "id": "5b4c4597-96ba-48df-ac4e-4c074b607dbd",
        "type": "user"
      }
    ]
  }
}
*/

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

#[derive(Deserialize, Debug, Clone)]
pub struct Chapter {
    pub data: ChapterData,
}

impl Chapter {
    pub async fn new(client: &ApiClient, chapter_uuid: Uuid) -> Result<Chapter> {
        let r_json = client
            .get_ok_json(Endpoint::GetChapter(chapter_uuid))
            .await?;

        serde_json::from_value::<Chapter>(r_json).into_diagnostic()
    }
}
