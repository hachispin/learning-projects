//! Contains the [`Endpoint`] enum.

use serde_urlencoded;
use uuid::Uuid;

/// "Endpoints" in this context are urls that aren't
/// valid until prefixed with a proper base url.
/// 
/// You can find the URIs in the [`Endpoint::as_string`] method.
#[derive(Debug, Clone)]
pub enum Endpoint {
    /// Takes a chapter's UUID and returns its info.
    ///
    /// ## References
    ///
    /// - [Redoc](https://api.mangadex.org/docs/redoc.html#tag/Chapter/operation/get-chapter-id)
    /// - [Swagger](https://api.mangadex.org/docs/swagger.html#/Chapter/get-chapter-id)
    GetChapter(Uuid),
    /// Takes a chapter's UUID and returns its download (CDN) info.
    ///
    /// ## References
    ///
    /// - [Redoc](https://api.mangadex.org/docs/redoc.html#tag/AtHome/operation/get-at-home-server-chapterId)
    /// - [Swagger](https://api.mangadex.org/docs/swagger.html#/AtHome/get-at-home-server-chapterId)
    GetChapterCdn(Uuid),
    /// Takes a manga's UUID and returns its info.
    ///
    /// ## References
    ///
    /// - [Redoc](https://api.mangadex.org/docs/redoc.html#tag/Manga/operation/get-manga-id)
    /// - [Swagger](https://api.mangadex.org/docs/swagger.html#/Manga/get-manga-id)
    GetManga(Uuid),
    /// Takes a manga's UUID and returns its chapters.
    /// 
    /// - [Redoc](https://api.mangadex.org/docs/redoc.html#tag/Manga/operation/get-manga-id-feed)
    /// - [Swagger](https://api.mangadex.org/docs/swagger.html#/Manga/get-manga-id-feed)
    GetMangaChapters(Uuid, Vec<(String, String)>),
    /// Takes search parameters (with query string) and returns a list of manga.
    ///
    /// ## References
    ///
    /// - [Redoc](https://api.mangadex.org/docs/redoc.html#tag/Manga/operation/get-search-manga)
    /// - [Swagger](https://api.mangadex.org/docs/swagger.html#/Manga/get-search-manga)
    SearchManga(Vec<(String, String)>),
}

impl Endpoint {
    /// Converts the endpoint into a relative URI.
    ///
    /// ## Panics
    ///
    /// If the query string for an endpoint fails to be made.
    #[must_use]
    pub fn as_string(&self) -> String {
        match self {
            Self::GetChapter(uuid) => format!("/chapter/{uuid}"),
            Self::GetChapterCdn(uuid) => format!("/at-home/server/{uuid}"),
            Self::GetManga(uuid) => format!("/manga/{uuid}"),

            Self::GetMangaChapters(uuid, params) => format!(
                "/manga/{uuid}/feed?{}",
                serde_urlencoded::to_string(params)
                    .expect("failed to build `GetMangaChapters` query string")
            ),

            Self::SearchManga(params) => {
                format!(
                    "/manga?{}",
                    serde_urlencoded::to_string(params)
                        .expect("failed to build `SearchManga` query string")
                )
            }
        }
    }
}
