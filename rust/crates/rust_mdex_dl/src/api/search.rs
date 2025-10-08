use crate::api::{
    client::ApiClient,
    endpoints::Endpoint,
    models::{Manga, MangaData},
};

use isolang::Language;
use log::{info, trace};
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

#[derive(Debug)]
pub struct SearchClient {
    api: ApiClient,
    results_per_page: u32,
}

impl SearchClient {
    pub fn new(api: ApiClient, results_per_page: u32) -> SearchClient {
        SearchClient {
            api,
            results_per_page,
        }
    }

    /// Expands a key with multiple values into multiple tuples.
    fn expand_param(key: &str, values: Vec<&str>) -> Vec<(String, String)> {
        let mut pairs: Vec<(String, String)> = Vec::with_capacity(values.len() + 1);

        for v in values {
            pairs.push((key.into(), v.into()));
        }

        pairs
    }

    pub async fn search(&self, query: &str, page: u32) -> Result<SearchResults> {
        // placeholder for now
        let mut params: Vec<(String, String)> = Vec::new();

        params.push(("title".into(), query.into()));

        // set pagination
        let offset = self.results_per_page * page;
        params.push(("limit".into(), self.results_per_page.to_string()));
        params.push(("offset".into(), offset.to_string()));

        // useful ux params
        params.push(("order[relevance]".into(), "desc".into()));
        params.extend(SearchClient::expand_param(
            "contentRating[]",
            vec!["safe", "suggestive", "erotica", "pornographic"],
        ));

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
}
