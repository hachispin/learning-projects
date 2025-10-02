//! Contains user-defined errors. What else?

use miette::Diagnostic;
use thiserror::Error;

#[derive(Error, Debug, Diagnostic)]
#[error("{error}")]
#[diagnostic(help("{help}"))]
pub struct ApiError {
    error: String,
    help: String,
}

impl ApiError {
    /// Helper for [`ApiError::new()`] in constructing [`ApiError::help`]
    fn get_status_code_help(status_code: u16) -> String {
        match status_code {
            400 | 404 => "check that the uuid you've entered actually exists",
            401 => "authentication needed. (you shouldn't be seeing this!)",
            403 => "you lack permission to access this. try something else",
            429 => "you've been ratelimited. i swear i'll implement ratelimit handling later",
            500 => "something went wrong with mangadex, consider retrying",
            503 => "try again in a few minutes",
            400..=499 => "this is a client error (generic 4xx)",
            500..=599 => "this is a server error (generic 5xx)",
            _ => "no help exists for this status code. sorry!",
        }
        .to_string()
    }

    /// Helper for [`ApiError::new()`] if "errors" field in `r_json` doesn't exist
    fn blank(status_code: u16) -> Self {
        Self {
            error: format!(
                "api error\n\n\
                status code: {status_code}\n\
                (missing 'errors' field, couldn't gather more info)\n"
            )
            .to_string(),
            help: Self::get_status_code_help(status_code),
        }
    }

    /// Helper for [`ApiError::new()`] in constructing [`ApiError::error`]
    fn format_error_text(
        number_of_errors: usize,
        status_code: u16,
        title: &str,
        detail: &str,
    ) -> String {
        format!(
            "api error; displaying 1 of {number_of_errors}\n\n\
            status code: {status_code}\n\
            title: {title}\n\
            detail: {detail}\n"
        )
    }

    /// Parses the provided JSON and parses fields to include extra info.
    ///
    /// This also works if these fields are for some reason non-existent.
    pub fn new(r_json: &serde_json::Value, status_code: u16) -> Self {
        let errors = r_json.get("errors").and_then(|e| e.as_array());

        if errors.is_none() {
            return Self::blank(status_code);
        }

        let errors = errors.unwrap();
        let number_of_errors = errors.len();
        let first_err = errors.get(0);

        if first_err.is_none() || number_of_errors == 0 {
            return Self::blank(status_code);
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

        let error_text = Self::format_error_text(number_of_errors, status_code, title, detail);

        Self {
            error: error_text,
            help: Self::get_status_code_help(status_code),
        }
    }
}
