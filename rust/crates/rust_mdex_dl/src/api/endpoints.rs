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
/// * [`Endpoint::GetChapter`] returns chapter info given a uuid
/// * [`Endpoint::GetChapterCdn`] returns download info
/// * [`Endpoint::GetManga`] takes a manga's uuid and returns its info
/// * [`Endpoint::SearchManga`] takes** a query and parameters and returns a list of manga
///
/// ** the [SearchManga](`Endpoint::SearchManga`) enum doesn't take search parameters itself.
///
/// The caller is expected to append them using [`reqwest::RequestBuilder::query`].
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
    GetManga(Uuid),
    SearchManga,
}

impl Endpoint {
    pub fn as_string(&self) -> String {
        match self {
            Self::GetChapter(uuid) => format!("/chapter/{uuid}"),
            Self::GetChapterCdn(uuid) => format!("/at-home/server/{uuid}"),
            Self::GetManga(uuid) => format!("/manga/{uuid}"),
            Self::SearchManga => "/manga".to_string(),
        }
    }
}
