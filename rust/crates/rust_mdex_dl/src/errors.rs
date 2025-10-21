//! Contains user-defined errors.

use log::error;
use miette::Diagnostic;
use reqwest::StatusCode;
use thiserror::Error;

use crate::api::endpoints::Endpoint;

#[derive(Error, Debug, Diagnostic)]
#[error("{error}")]
#[diagnostic(help("{help}"))]
pub struct ApiError {
    error: String,
    help: String,
}

impl ApiError {
    /// Helper for [`ApiError::new()`] in constructing [`ApiError::help`]
    fn get_status_code_help(status: StatusCode) -> String {
        match status.as_u16() {
            400 | 404 => "check if this link is actually valid",
            401 => "authentication needed. (you shouldn't be seeing this!)",
            403 => "you lack permission to access this. try something else",
            429 => "you've been ratelimited. i swear i'll implement ratelimit handling later",
            500 => "something went wrong with mangadex, consider retrying",
            503 => "try again in a few minutes",
            _ => status
                .canonical_reason()
                .unwrap_or("no reason found, sorry :("),
        }
        .to_string()
    }

    /// Helper for [`ApiError::new()`] if "errors" field in `r_json` doesn't exist
    pub fn blank(endpoint: Endpoint, status: StatusCode) -> Self {
        let status_code = status.as_u16();

        Self {
            error: format!(
                "api error\n\n\
                endpoint: {endpoint:?}\n\
                status code: {status_code}\n\
                (missing 'errors' field, couldn't gather more info)\n"
            )
            .to_string(),
            help: Self::get_status_code_help(status),
        }
    }

    /// Helper for [`ApiError::new()`] in constructing [`ApiError::error`]
    fn format_error_text(
        number_of_errors: usize,
        endpoint: Endpoint,
        status: StatusCode,
        title: &str,
        detail: &str,
    ) -> String {
        let status = status.as_str();

        format!(
            "api error; displaying 1 of {number_of_errors}\n\n\
            endpoint: {endpoint:?}\n\
            status code: {status}\n\
            title: {title}\n\
            detail: {detail}\n"
        )
    }

    /// Parses the provided JSON and parses fields to include extra error info.
    ///
    /// This also works if these fields are for some reason non-existent, which
    /// means that this method would also work on actual, valid responses.
    pub fn new(endpoint: Endpoint, r_json: &serde_json::Value, status: StatusCode) -> Self {
        error!("`ApiError` encountered! Faulty JSON: {r_json:#?}");

        let errors = r_json.get("errors").and_then(|e| e.as_array());

        if errors.is_none() {
            return Self::blank(endpoint, status);
        }

        let errors = errors.unwrap();
        let number_of_errors = errors.len();
        let first_err = errors.get(0);

        if first_err.is_none() || number_of_errors == 0 {
            return Self::blank(endpoint, status);
        }

        let first_err = first_err.unwrap();

        let title = first_err
            .get("title")
            .and_then(|s| s.as_str())
            .unwrap_or("unknown title");
        let detail = first_err
            .get("detail")
            .and_then(|s| s.as_str())
            .unwrap_or("unknown detail");

        let error_text = Self::format_error_text(number_of_errors, endpoint, status, title, detail);

        Self {
            error: error_text,
            help: Self::get_status_code_help(status),
        }
    }
}
