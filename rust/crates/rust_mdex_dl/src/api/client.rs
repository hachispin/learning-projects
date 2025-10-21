//! Contains [`ApiClient`] struct for interacting with MangaDex's API.

use std::sync::atomic::{AtomicBool, Ordering};
use std::time::Duration;

use crate::{api::endpoints::Endpoint, config};

use crate::errors::ApiError;
use log::{error, trace, warn};
use miette::{IntoDiagnostic, Result};
use reqwest::header::HeaderMap;
use reqwest::{self, StatusCode};
use serde_json;

// prevent threads spamming ratelimit logs
static RATELIMIT_LOGGED: AtomicBool = AtomicBool::new(false);

#[derive(Debug, Clone)]
/// A wrapper over [`reqwest::Client`] for MangaDex interactions.
pub struct ApiClient {
    client: reqwest::Client,
    base_url: reqwest::Url,
    max_retries: u32,
}

impl ApiClient {
    /// Creates a new [`ApiClient`] with [`reqwest::Client::builder()`]
    pub fn new(client_cfg: &config::Client) -> Result<Self> {
        let base_url = client_cfg.base_url.clone();
        let max_retries = client_cfg.max_retries;

        let client = reqwest::Client::builder()
            .user_agent(client_cfg.user_agent.clone())
            .build()
            .into_diagnostic()?;

        Ok(Self {
            client,
            base_url,
            max_retries,
        })
    }

    /// Sends a GET request to the `endpoint` prefixed with the
    /// [base url](Self::base_url) and returns the response.
    ///
    /// Use [`Self::get_ok_json()`] if this response is intended to parsed as JSON.
    pub async fn get(&self, endpoint: Endpoint) -> Result<reqwest::Response> {
        let uri = endpoint.as_string();
        let url = self.base_url.join(&uri).into_diagnostic()?;
        let mut r = None;

        trace!("Sending GET request, url={url}");

        // ratelimit handling... sorta
        for i in 1..=self.max_retries {
            r = Some(
                self.client
                    .get(self.base_url.join(&uri).into_diagnostic()?)
                    .send()
                    .await
                    .into_diagnostic()?,
            );

            let _r = r.as_ref().unwrap();
            let status = _r.status();
            let headers = _r.headers();

            if status != StatusCode::TOO_MANY_REQUESTS {
                break;
            }

            Self::handle_ratelimit(headers, i).await?;
        }

        Ok(r.unwrap())
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
        let r = self.get(endpoint.clone()).await?;
        let status_code = r.status();
        let success = r.status().is_success();
        let r_text = r.text().await.into_diagnostic()?;

        trace!("r_text={r_text:?}");

        let r_json: serde_json::Value = serde_json::from_str(&r_text).map_err(|e| {
            error!("Error parsing JSON: {e:#?}");
            error!("Raw response body as text: {r_text:#?}");
            ApiError::blank(endpoint.clone(), status_code)
        })?;

        let result = r_json
            .get("result")
            .and_then(|r| r.as_str())
            .unwrap_or("error");

        if result == "error" || !success {
            return Err(ApiError::new(endpoint, &r_json, status_code).into());
        }

        Ok(r_json)
    }

    /// Sleeps and logs ratelimit based off of provided `headers`.
    async fn handle_ratelimit(headers: &HeaderMap, retry_count: u32) -> Result<()> {
        let retry_after = Self::get_retry_after(headers)?;
        let sleep_duration = Duration::from_secs(retry_after as u64);

        if !RATELIMIT_LOGGED.swap(true, Ordering::SeqCst) {
            warn!("Ratelimited (received 429 Too Many Requests), attempt {retry_count}");
            warn!("Sleeping for {}s...", sleep_duration.as_secs());
        }

        tokio::time::sleep(sleep_duration).await;
        RATELIMIT_LOGGED.store(false, Ordering::SeqCst);

        Ok(())
    }

    /// Attempts to parse a response's headers for `Retry-After` headers or equivalent.
    fn get_retry_after(headers: &HeaderMap) -> Result<u32> {
        let retry_in = headers
            .get("retry-after")
            .or(headers.get("x-ratelimit-retry-in"))
            .ok_or(miette::miette!("couldn't find `retry-after` header"))?
            .to_str()
            .into_diagnostic()?;

        Ok(retry_in.parse::<u32>().into_diagnostic()?)
    }
}
