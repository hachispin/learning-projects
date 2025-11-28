use crate::api::{
    client::ApiClient,
    endpoints::Endpoint,
    models::{Chapter, ChapterData, ContentRating, Manga, MangaData},
};

use isolang::Language;
use log::{debug, info, trace, warn};
use miette::{IntoDiagnostic, Result};
use serde::Deserialize;

#[derive(Deserialize, Debug, Clone)]
pub struct SearchResults {
    pub data: Vec<MangaData>,
    pub total: u32,
}

impl SearchResults {
    /// Returns every manga's title stored in [`Self::data`] enumerated.
    #[must_use] 
    pub fn display(&self, language: Language) -> Vec<String> {
        let mut titles = Vec::with_capacity(self.data.len() + 1);

        for (i, md) in self.data.iter().enumerate() {
            let m = Manga::from_data(md.clone());
            let option = format!("[{}] {}", i + 1, m.title(language));
            titles.push(option);
        }

        titles
    }

    /// Returns the [`MangaData`] as [`Manga`] of the specified `manga_index` at [`Self::data`].
    ///
    /// Note that `manga_index` is zero-indexed.
    #[must_use] 
    pub fn get(&self, manga_index: usize) -> Option<Manga> {
        self.data
            .get(manga_index)
            .map(|md| Manga::from_data(md.clone()))
    }
}

#[derive(Deserialize, Debug, Clone)]
struct ChapterResults {
    data: Vec<ChapterData>,
    total: u32,
}

#[derive(Debug)]
pub struct SearchClient {
    api: ApiClient,
    language: Language,
    manga_pagination: u32,
}

impl SearchClient {
    pub const MAX_MANGA_PAGINATION: u32 = 100;
    pub const MAX_CHAPTER_PAGINATION: u32 = 500;

    /// Creates a new [`SearchClient`].
    ///
    /// Clamps if `manga_pagination` > [`Self::MAX_MANGA_PAGINATION`]
    #[must_use] 
    pub fn new(api: ApiClient, language: Language) -> SearchClient {
        let manga_pagination = Self::MAX_MANGA_PAGINATION;

        SearchClient {
            api,
            language,
            manga_pagination,
        }
    }

    /// Helper for constructing language filters for manga or chapters.
    fn language_filter_param(
        allowed_languages: &[Language],
        is_chapter: bool,
    ) -> Result<Vec<(String, String)>> {
        let mut params: Vec<(String, String)> = Vec::new();

        let key = if is_chapter {
            "translatedLanguage[]"
        } else {
            "availableTranslatedLanguage[]"
        }
        .to_string();

        for language in allowed_languages {
            let key = key.clone();
            let value = language
                .to_639_1()
                .ok_or(miette::miette!("failed to convert language into iso 639-1"))?
                .to_string();

            params.push((key, value));
        }

        Ok(params)
    }

    /// Helper for constructing the content rating parameter.
    fn content_rating_param(allowed_ratings: &[ContentRating]) -> Vec<(String, String)> {
        let mut params: Vec<(String, String)> = Vec::new();
        let key = "contentRating[]".to_string();

        for rating in allowed_ratings {
            let key = key.clone();

            match rating {
                ContentRating::Safe => params.push((key, "safe".into())),
                ContentRating::Suggestive => params.push((key, "suggestive".into())),
                ContentRating::Erotica => params.push((key, "erotica".into())),
                ContentRating::Pornographic => params.push((key, "pornographic".into())),
            }
        }

        params
    }

    /// Searches for the given `query`.
    /// 
    /// ## Errors
    /// 
    /// If either the GET request fails, or the response is
    /// faulty and can't be parsed as [`SearchResults`].
    pub async fn search(&self, query: &str, page: u32) -> Result<SearchResults> {
        // placeholder for now
        let mut params: Vec<(String, String)> = Vec::new();

        params.push(("title".into(), query.into()));
        params.extend(Self::language_filter_param(&[self.language], false)?);

        // set pagination
        let offset = self.manga_pagination * page;
        params.push(("limit".into(), self.manga_pagination.to_string()));
        params.push(("offset".into(), offset.to_string()));

        // useful ux params
        params.push(("order[relevance]".into(), "desc".into()));
        params.extend(Self::content_rating_param(&[
            ContentRating::Safe,
            ContentRating::Suggestive,
            ContentRating::Erotica,
            ContentRating::Pornographic,
        ]));

        let endpoint = Endpoint::SearchManga(params);
        info!("Searching with URI {:?}", endpoint.as_string());

        let r = self.api.get_ok_json(endpoint).await?;
        let results = serde_json::from_value::<SearchResults>(r).into_diagnostic()?;

        trace!("Results: {results:?}");

        info!(
            "Fetched {} results out of the {} results available",
            results.data.len(),
            results.total
        );

        Ok(results)
    }

    /// Fetches all chapters of the given [`Manga`] with the specified [`Self::language`]
    /// 
    /// ## Errors
    /// 
    /// From [`ApiClient::get_ok_json`] or if the response
    /// can't be parsed as [`ChapterResults`].
    pub async fn fetch_all_chapters(&self, manga: &Manga) -> Result<Vec<Chapter>> {
        let mut all_chapters: Vec<Chapter> = Vec::new();
        let mut offset = 0u32;
        let limit = Self::MAX_CHAPTER_PAGINATION;

        let mut params: Vec<(String, String)> = Vec::new();
        params.push(("offset".into(), offset.to_string()));
        params.push(("limit".into(), limit.to_string()));
        params.extend(Self::language_filter_param(&[self.language], true)?);
        params.extend(Self::content_rating_param(&[
            ContentRating::Safe,
            ContentRating::Suggestive,
            ContentRating::Erotica,
            ContentRating::Pornographic,
        ]));

        let endpoint = Endpoint::GetMangaChapters(manga.uuid(), params.clone());

        info!(
            "Fetching chapters of the manga {:?}",
            manga.title(self.language)
        );

        // "initial" because pagination params are modified later on
        debug!("Fetching chapters using initial endpoint URI {params:?}");

        // first fetch is outside the loop to find `total`
        let raw_results = self.api.get_ok_json(endpoint).await?;

        let chapter_results: ChapterResults =
            serde_json::from_value(raw_results).into_diagnostic()?;

        let chapters: Vec<Chapter> = chapter_results
            .data
            .into_iter()
            .map(Chapter::from_data)
            .collect();

        let total = chapter_results.total;
        offset += Self::MAX_CHAPTER_PAGINATION;
        all_chapters.extend(chapters);

        while offset < total {
            debug!("Current offset: {offset}");

            // ref: https://api.mangadex.org/docs/2-limitations/#collection-result-sizes
            if offset + limit > 10_000 {
                warn!(concat!(
                    "Fetching chapters halted; exceeded max collection",
                    " result size bound of (offset + limit > 10,000)"
                ));
            }

            // update params
            let mut params = params.clone();
            params[0].1 = offset.to_string();

            // fetch chapters and turn them into `Vec<Chapter>`
            let chapters: Vec<Chapter> = serde_json::from_value::<ChapterResults>(
                self.api
                    .get_ok_json(Endpoint::GetMangaChapters(manga.uuid(), params))
                    .await?,
            )
            .into_diagnostic()?
            .data
            .into_iter()
            .map(Chapter::from_data)
            .collect();

            all_chapters.extend(chapters);
            offset += Self::MAX_CHAPTER_PAGINATION;
        }

        trace!("All fetched chapters: {all_chapters:?}");
        Ok(all_chapters)
    }
}
