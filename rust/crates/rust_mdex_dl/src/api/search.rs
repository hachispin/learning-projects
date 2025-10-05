use std::collections::HashMap;

use crate::api::{
    client::ApiClient,
    endpoints::Endpoint,
    models::{ContentRating, Manga},
};

use miette::Result;
use reqwest::{self, Url};
use serde::Deserialize;

#[derive(Deserialize, Debug, Clone)]
struct SearchResults {
    data: Vec<Manga>,
    limit: u32,
    offset: u32,
    total: u32,
}

#[derive(Debug)]
pub struct SearchClient {
    client: ApiClient,
    page_size: usize,
}

impl SearchClient {
    /// Expands a key with multiple values into multiple tuples.
    ///
    /// Example usage:
    /// ```
    /// # use rust_mdex_dl::SearchClient;
    /// let key = "allowed_genres";
    /// let values = vec!["Romance".to_string(), "Fantasy".to_string()];
    /// let param = SearchClient::expand_param(key, values);
    ///
    /// assert_eq!(param, vec![
    ///     ("allowed_genres", "Romance".to_string()),
    ///     ("allowed_genres", "Fantasy".to_string())
    /// ])
    /// ```
    pub fn expand_param<'k>(key: &'k str, values: Vec<String>) -> Vec<(&'k str, String)> {
        let mut pairs = Vec::with_capacity(values.len() + 1);

        for v in values {
            pairs.push((key, v));
        }

        pairs
    }
}
