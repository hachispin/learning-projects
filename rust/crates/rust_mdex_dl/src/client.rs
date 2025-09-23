use miette::{ErrReport, IntoDiagnostic, Result};
use reqwest;
use reqwest::Url;
use serde_json;

use crate::errors::ApiError;

#[derive(Debug)]
pub struct Client {
    client: reqwest::Client,
    base_url: reqwest::Url,
}

impl Client {
    pub fn new(base_url: &str, user_agent: Option<&str>) -> Result<Self> {
        let base_url: Url = base_url.parse().into_diagnostic()?;
        let user_agent = user_agent.unwrap_or("reqwest").to_string();

        let client = reqwest::Client::builder()
            .user_agent(user_agent)
            .build()
            .into_diagnostic()?;

        Ok(Self { client, base_url })
    }

    pub async fn get(&self, endpoint: &str) -> Result<reqwest::Response> {
        let url = self.base_url.join(endpoint).into_diagnostic()?;
        let r = self.client.get(url).send().await.into_diagnostic()?;

        Ok(r)
    }

    /// Fetches from the endpoint and parses the response as JSON.
    ///
    /// The `Ok()` value contains this JSON response.
    ///
    /// An `Err()` value is returned if it's either:
    ///
    /// * not parsable as JSON
    /// * bubbling up an Err() from [`Client::get()`]
    /// * invalid due to the `r_json["result"]` field
    ///     - expects `"result": "ok"` but may be `"result": "error"`
    ///
    /// This should be preferred over using [`Client::get()`]
    /// if the response is intended to be parsed as JSON.
    pub async fn get_ok_json(&self, endpoint: &str) -> Result<serde_json::Value> {
        let r = self.get(endpoint).await?;
        let status_code = r.status().as_u16();
        let success = r.status().is_success();

        let r_json: serde_json::Value = r.json().await.into_diagnostic()?;
        let result = r_json
            .get("result")
            .and_then(|r| r.as_str())
            .unwrap_or("error");

        if result == "error" || !success {
            return Err(ErrReport::from(ApiError::new(&r_json, status_code)));
        }

        Ok(r_json)
    }
}

#[derive(Debug)]
/// stores the JSON response of `GET at-home/server/:chapterId`
pub struct ChapterCdnInfo {
    base_url: String,
    hash: String,
    data: Vec<String>,
    data_saver: Vec<String>,
}

impl ChapterCdnInfo {
    /// This function is built upon the assumption that [`Client::get_ok_json()`] is used
    ///
    /// There should be no "errors" field and status is successful (200-299).
    pub fn new(cdn_info: &serde_json::Value) -> ChapterCdnInfo {
        let base_url = cdn_info["baseUrl"].as_str().unwrap().to_string();
        let chapter = cdn_info["chapter"].as_object().unwrap();
        let hash = chapter["hash"].as_str().unwrap().to_string();

        let data: Vec<String> = chapter["data"]
            .as_array()
            .unwrap()
            .iter()
            .map(|v| v.as_str().unwrap().to_string())
            .collect();

        let data_saver: Vec<String> = chapter["dataSaver"]
            .as_array()
            .unwrap()
            .iter()
            .map(|v| v.as_str().unwrap().to_string())
            .collect();

        ChapterCdnInfo {
            base_url,
            hash,
            data,
            data_saver,
        }
    }

    /// The page URLs are in the format:
    ///
    /// `$.baseUrl / $QUALITY / $.chapter.hash / $.chapter.$QUALITY[*]`
    pub fn construct_image_urls(&self, use_data_saver: bool) -> Result<Vec<Url>> {
        let quality = if use_data_saver { "data-saver" } else { "data" };
        let pages = if use_data_saver {
            &self.data_saver
        } else {
            &self.data
        };

        let mut urls: Vec<Url> = Vec::with_capacity(pages.len() + 1);
        let url_prefix_fmt = format!("{}/{}/{}/", self.base_url, quality, self.hash);
        let url_prefix = Url::parse(&url_prefix_fmt).into_diagnostic()?;

        for page in pages {
            let url = url_prefix.join(page).into_diagnostic()?;
            urls.push(url);
        }

        Ok(urls)
    }
}
