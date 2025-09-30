use crate::{api::endpoints::Endpoint, config};

use crate::errors::ApiError;
use isolang::Language;
use miette::{IntoDiagnostic, Result};
use reqwest;
use serde_json;

#[derive(Debug)]
/// A wrapper over [`reqwest::Client`] for MangaDex interactions.
pub struct ApiClient {
    client: reqwest::Client,
    base_url: reqwest::Url,
    language: Language,
}

impl ApiClient {
    /// Creates a new [`ApiClient`] with [`reqwest::Client::builder()`]
    pub fn new(client_cfg: &config::Client) -> Result<Self> {
        let base_url = client_cfg.base_url.clone();
        let language = client_cfg.language;

        let client = reqwest::Client::builder()
            .user_agent(client_cfg.user_agent.clone())
            .build()
            .into_diagnostic()?;

        Ok(Self {
            client,
            base_url,
            language,
        })
    }

    /// Sends a GET request to the `endpoint` prefixed with the
    /// [base url](Self::base_url) and returns the response.
    ///
    /// Use [`Self::get_ok_json()`] if this response is intended to parsed as JSON.
    pub async fn get(&self, endpoint: Endpoint) -> Result<reqwest::Response> {
        let uri = endpoint.as_string();

        let r = self
            .client
            .get(self.base_url.join(&uri).into_diagnostic()?)
            .send()
            .await
            .into_diagnostic()?;

        Ok(r)
    }

    /// Fetches from the `endpoint` and parses the response as JSON.
    ///
    /// The `Ok()` value contains this JSON response.
    ///
    /// An `Err()` value is returned if it's either:
    ///
    /// * not parsable as JSON
    /// * bubbling up an Err() from [`Self::get()`]
    /// * invalid due to the `r_json["result"]` field
    ///     - expects `"result": "ok"` but may be `"result": "error"`
    ///
    /// This should be preferred over using [`Self::get()`]
    /// if the response is intended to be parsed as JSON.
    pub async fn get_ok_json(&self, endpoint: Endpoint) -> Result<serde_json::Value> {
        let r = self.get(endpoint).await?;
        let status_code = r.status().as_u16();
        let success = r.status().is_success();

        let r_json: serde_json::Value = r.json().await.into_diagnostic()?;
        let result = r_json
            .get("result")
            .and_then(|r| r.as_str())
            .unwrap_or("error");

        if result == "error" || !success {
            return Err(ApiError::new(&r_json, status_code).into());
        }

        Ok(r_json)
    }
}
