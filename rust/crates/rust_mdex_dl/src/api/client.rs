//! Contains [`ApiClient`] struct for interacting with MangaDex's API.

use crate::{api::endpoints::Endpoint, config};

use crate::errors::ApiError;
use log::trace;
use miette::{IntoDiagnostic, Result};
use reqwest;
use serde_json;

#[derive(Debug, Clone)]
/// A wrapper over [`reqwest::Client`] for MangaDex interactions.
pub struct ApiClient {
    client: reqwest::Client,
    base_url: reqwest::Url,
    _user_agent: String, // for `ApiClientBlocking::from_async()`
}

impl ApiClient {
    /// Creates a new [`ApiClient`] with [`reqwest::Client::builder()`]
    pub fn new(client_cfg: &config::Client) -> Result<Self> {
        let base_url = client_cfg.base_url.clone();
        let _user_agent = client_cfg.user_agent.clone();
        let client = reqwest::Client::builder()
            .user_agent(client_cfg.user_agent.clone())
            .build()
            .into_diagnostic()?;

        Ok(Self {
            client,
            base_url,
            _user_agent,
        })
    }

    /// Sends a GET request to the `endpoint` prefixed with the
    /// [base url](Self::base_url) and returns the response.
    ///
    /// Use [`Self::get_ok_json()`] if this response is intended to parsed as JSON.
    pub async fn get(&self, endpoint: Endpoint) -> Result<reqwest::Response> {
        let uri = endpoint.as_string();
        let url = self.base_url.join(&uri).into_diagnostic()?;

        trace!("Sending GET request, url={url}");

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

#[derive(Debug, Clone)]
/// A wrapper over [`reqwest::Client`] for MangaDex interactions.
///
/// This is the exact same as [`ApiClient`], just without async.
pub struct ApiClientBlocking {
    client: reqwest::blocking::Client,
    base_url: reqwest::Url,
}

impl ApiClientBlocking {
    fn _new(base_url: reqwest::Url, user_agent: String) -> Result<Self> {
        let client = reqwest::blocking::Client::builder()
            .user_agent(user_agent)
            .build()
            .into_diagnostic()?;

        Ok(Self { client, base_url })
    }

    pub fn new(client_cfg: &config::Client) -> Result<Self> {
        let base_url = client_cfg.base_url.clone();

        let client = reqwest::blocking::Client::builder()
            .user_agent(client_cfg.user_agent.clone())
            .build()
            .into_diagnostic()?;

        Ok(Self { client, base_url })
    }

    /// Creates a new [`ApiClientBlocking`] from [`ApiClient`].
    pub fn from_async(api: ApiClient) -> Result<Self> {
        Self::_new(api.base_url, api._user_agent)
    }

    pub fn get(&self, endpoint: Endpoint) -> Result<reqwest::blocking::Response> {
        let uri = endpoint.as_string();
        let url = self.base_url.join(&uri).into_diagnostic()?;

        trace!("Sending (blocking) GET request, url={url}");

        let r = self
            .client
            .get(self.base_url.join(&uri).into_diagnostic()?)
            .send()
            .into_diagnostic()?;

        Ok(r)
    }

    pub fn get_ok_json(&self, endpoint: Endpoint) -> Result<serde_json::Value> {
        let r = self.get(endpoint)?;
        let status_code = r.status().as_u16();
        let success = r.status().is_success();

        let r_json: serde_json::Value = r.json().into_diagnostic()?;
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
