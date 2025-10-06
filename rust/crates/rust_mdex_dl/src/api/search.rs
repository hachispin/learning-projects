use crate::api::{client::ApiClient, endpoints::Endpoint, models::MangaData};

use log::info;
use miette::{IntoDiagnostic, Result};
use reqwest::{self, Url};
use serde::Deserialize;

#[derive(Deserialize, Debug, Clone)]
pub struct SearchResults {
    data: Vec<MangaData>,
    limit: u32,
    offset: u32,
    total: u32,
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
        let mut pairs = Vec::with_capacity(values.len() + 1);

        for v in values {
            pairs.push((key.to_string(), v.to_string()));
        }

        pairs
    }

    pub async fn search(&self, query: &str, page: u32) -> Result<SearchResults> {
        // placeholder for now
        let mut params = Vec::new();

        params.push(("title".to_string(), query.to_string()));
        params.push(("order[relevance]".to_string(), "desc".to_string()));

        params.extend(SearchClient::expand_param(
            "contentRating[]",
            vec!["safe", "suggestive", "erotica", "pornographic"],
        ));

        let endpoint = Endpoint::SearchManga(params);
        info!("Searching with URI {:?}", endpoint.as_string());

        serde_json::from_value::<SearchResults>(self.api.get_ok_json(endpoint).await?)
            .into_diagnostic()
    }
}
