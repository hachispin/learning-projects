use crate::api::{
    client::ApiClient,
    endpoints::Endpoint,
    models::{Chapter, ChapterData, ContentRating, Manga, MangaData},
};

use isolang::Language;
use log::{info, trace, warn};
use miette::{IntoDiagnostic, Result};
use serde::Deserialize;

#[derive(Deserialize, Debug, Clone)]
pub struct SearchResults {
    pub data: Vec<MangaData>,
    limit: u32,
    offset: u32,
    total: u32,
}

impl SearchResults {
    /// Prints every manga's titles stored in [`Self::data`] to stdout
    pub fn display(&self, language: Language) {
        for (i, md) in self.data.iter().enumerate() {
            let m = Manga::from_data(md.clone());
            println!("[{}] {}", i + 1, m.title(language));
        }
    }
}

#[derive(Deserialize, Debug, Clone)]
struct ChapterResults {
    data: Vec<ChapterData>,
    limit: u32,
    offset: u32,
    total: u32,
}

#[derive(Debug)]
pub struct SearchClient {
    api: ApiClient,
    language: Language,
    results_per_page: u32,
}

impl SearchClient {
    const MAX_MANGA_PAGINATION: u32 = 100;
    const MAX_CHAPTER_PAGINATION: u32 = 500;

    pub fn new(api: ApiClient, language: Language, results_per_page: u32) -> SearchClient {
        SearchClient {
            api,
            language,
            results_per_page,
        }
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

    pub async fn search(&self, query: &str, page: u32) -> Result<SearchResults> {
        // placeholder for now
        let mut params: Vec<(String, String)> = Vec::new();

        params.push(("title".into(), query.into()));

        // language filter
        params.push((
            "availableTranslatedLanguage[]".into(),
            self.language
                .to_639_1()
                .ok_or(miette::miette!(
                    "failed to convert `SearchClient::language` to iso 639-1",
                ))?
                .into(),
        ));

        // set pagination
        let offset = self.results_per_page * page;
        params.push(("limit".into(), self.results_per_page.to_string()));
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

    /// Fetches all chapters of the given [`Manga`].
    pub async fn fetch_all_chapters(&self, manga: Manga) -> Result<Vec<Chapter>> {
        let mut all_chapters: Vec<Chapter> = Vec::new();
        let mut offset = 0u32;
        let limit = Self::MAX_CHAPTER_PAGINATION;

        let mut params: Vec<(String, String)> = Vec::new();
        params.push(("offset".into(), offset.to_string()));
        params.push(("limit".into(), limit.to_string()));
        params.extend(Self::content_rating_param(&[
            ContentRating::Safe,
            ContentRating::Suggestive,
            ContentRating::Erotica,
            ContentRating::Pornographic,
        ]));

        info!(
            "Fetching chapters of the manga {:?}",
            manga.title(self.language)
        );

        // first fetch is outside the loop to find `total`
        let raw_results = self
            .api
            .get_ok_json(Endpoint::GetMangaChapters(manga.uuid(), params.clone()))
            .await?;

        let chapter_results: ChapterResults =
            serde_json::from_value(raw_results).into_diagnostic()?;

        let chapters: Vec<Chapter> = chapter_results
            .data
            .iter()
            .map(|cd| Chapter::from_data(cd.clone()))
            .collect();

        let total = chapter_results.total;
        offset += Self::MAX_CHAPTER_PAGINATION;
        all_chapters.extend(chapters);

        while offset < total {
            // ref: https://api.mangadex.org/docs/2-limitations/#collection-result-sizes
            if offset + limit > 10_000 {
                warn!(concat!(
                    "Fetching chapters halted; exceeded max collection",
                    " result size bound of (offset + limit > 10,000)"
                ))
            }

            // update params
            let mut params = params.clone();
            params[0].1 = offset.to_string();

            let chapters: Vec<Chapter> = serde_json::from_value::<ChapterResults>(
                self.api
                    .get_ok_json(Endpoint::GetMangaChapters(manga.uuid(), params))
                    .await?,
            )
            .into_diagnostic()?
            .data
            .iter()
            .map(|cd| Chapter::from_data(cd.clone()))
            .collect();

            all_chapters.extend(chapters);
            offset += Self::MAX_CHAPTER_PAGINATION;
        }

        Ok(all_chapters)
    }
}
