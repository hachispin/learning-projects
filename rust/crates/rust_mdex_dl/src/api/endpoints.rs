//! Contains the [`Endpoint`] enum.

#![allow(unused)]

use miette::{IntoDiagnostic, Result};
use reqwest::Url;
use uuid::Uuid;

/// ## Info about endpoints
///
/// "Endpoints" in this context are urls that aren't
/// valid until prefixed with a proper base url.
///
/// [`Endpoint::GetChapter`] takes a chapter uuid and returns relevant info
///
/// [`Endpoint::GetChapterCdn`] takes a chapter uuid and returns info needed for downloading
///
/// [`Endpoint::SearchManga`] takes* a query and parameters and returns a list of manga
///
/// \* the enum itself doesn't take these arguments
///
/// ## Relevant documentation
///
/// https://api.mangadex.org/docs/redoc.html#tag/Chapter/operation/get-chapter-id
///
/// https://api.mangadex.org/docs/redoc.html#tag/AtHome/operation/get-at-home-server-chapterId
///
/// https://api.mangadex.org/docs/redoc.html#tag/Manga/operation/get-search-manga

#[derive(Debug, Clone)]
pub enum Endpoint {
    GetChapter(Uuid),
    GetChapterCdn(Uuid),
    SearchManga,
}

impl Endpoint {
    pub fn as_string(&self) -> String {
        match self {
            Self::GetChapter(uuid) => format!("/chapter/{uuid}"),
            Self::GetChapterCdn(uuid) => format!("/at-home/server/{uuid}"),
            Self::SearchManga => "/manga".to_string(),
        }
    }
}
