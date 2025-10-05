use crate::{Endpoint, api::{client::ApiClient, models::{Manga, ContentRating}}};


use reqwest::{self, Url};
use serde::Deserialize

#[derive(Deserialize, Debug, Clone)]
struct SearchResults {
    data: Vec<Manga>,
    limit: u32,
    offset: u32,
    total: u32,
}

#[derive(Debug)]
struct SearchClient {
    client: ApiClient,
    page_size: usize,
}

impl SearchClient {

    // pub fn search(&self, query: &str, page: u32) -> Result<SearchResults> {
    //     let query = [("title", query)];
    //     let offset = page * self.page_size as u32;

    //     miette::miette!("wtf")
    // }
}
