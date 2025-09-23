use miette::{Diagnostic, NamedSource, SourceSpan};
use thiserror::Error;

#[derive(Error, Debug, Diagnostic)]
#[error("{error}")]
#[diagnostic(help("{help}"))]

/// An error for invalid UUIDs.
///
/// Construction is done through pre-defined error
/// templates to reduce caller-side boilerplate.
///
/// Errors exist for:
///
/// * invalid total length  (expected 36)
/// * invalid chunk length  (expected 8-4-4-4-12)
/// * unexpected tokens     (only letters a-f, numbers, and hyphens)
pub struct UuidError {
    error: String,
    #[source_code]
    src: NamedSource<String>,
    #[label("here!")]
    pos: SourceSpan,
    help: String,
}

impl UuidError {
    pub const CHUNK_SIZES: [usize; 5] = [8, 4, 4, 4, 12];

    pub fn invalid_length(src: &str) -> UuidError {
        UuidError {
            error: format!("expected length 36, instead got length {}", src.len()),
            src: NamedSource::new(file!(), src.to_string()),
            pos: (0, src.len()).into(),
            help: "enter a complete uuid".to_string(),
        }
    }

    pub fn invalid_token(src: &str, pos: usize) -> UuidError {
        assert!(pos < src.len());

        UuidError {
            error: format!("unexpected token, {}", src.chars().nth(pos).unwrap()),
            src: NamedSource::new(file!(), src.to_string()),
            pos: (pos, 0).into(),
            help: concat!(
                "remove this character; a uuid can only be made\n",
                "of lowercase letters a-f, numbers, and hyphens"
            )
            .to_string(),
        }
    }

    pub fn invalid_chunk_length(
        src: &str,
        pos: (usize, usize),
        expected: usize,
        received: usize,
    ) -> UuidError {
        UuidError {
            error: format!("expected length {expected}, instead got length {received}"),
            src: NamedSource::new(file!(), src.to_string()),
            pos: pos.into(),
            help: "check your hyphen positions".to_string(),
        }
    }

    pub fn invalid_chunk_count(src: &str, chunk_count: usize) -> UuidError {
        let hyphens = chunk_count.checked_sub(1).unwrap_or(0);

        UuidError {
            error: format!("unexpected hyphen count ({hyphens}); expected 4"),
            src: NamedSource::new(file!(), src.to_string()),
            pos: (0, src.len()).into(),
            help: "balance your hyphen count to 4".to_string(),
        }
    }
}

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
