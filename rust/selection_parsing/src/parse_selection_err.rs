//! Contains the `ParseSelectionError` struct along with
//! preset error templates in its implementation.
//!
//! Use these error templates to construct `miette`
//! diagnostics; construction of the `ParseSelectionError`
//! struct itself isn't public.

use miette::{Diagnostic, NamedSource, SourceSpan};
use thiserror::Error;

#[derive(Error, Debug, Diagnostic)]
#[error("{error}")]
#[diagnostic(help("{help}"))]
pub struct ParseSelectionError {
    error: String,
    #[source_code]
    src: NamedSource<String>,
    #[label("here!")]
    pos: SourceSpan,
    help: String,
}

/// Helper functions for presets
impl ParseSelectionError {
    pub fn no_input() -> ParseSelectionError {
        ParseSelectionError {
            error: "no input made".to_string(),
            src: NamedSource::new(file!(), Default::default()),
            pos: (0, 0).into(),
            help: "make a selection using the provided syntax or quit".to_string(),
        }
    }

    pub fn no_selection_comma(src: &str, pos: (usize, usize)) -> ParseSelectionError {
        ParseSelectionError {
            error: "no selection found between comma".to_string(),
            src: NamedSource::new(file!(), src.to_string()),
            pos: pos.into(),
            help: "remove this comma".to_string(),
        }
    }

    pub fn unexpected_token(src: &str, pos: (usize, usize)) -> ParseSelectionError {
        ParseSelectionError {
            error: "unexpected token".to_string(),
            src: NamedSource::new(file!(), src.to_string()),
            pos: pos.into(),
            help: "remove this character".to_string(),
        }
    }

    pub fn unexpected_whitespace(src: &str, pos: (usize, usize)) -> ParseSelectionError {
        ParseSelectionError {
            error: "unexpected whitespace".to_string(),
            src: NamedSource::new(file!(), src.to_string()),
            pos: pos.into(),
            help: concat!(
                "use commas as separators, not spaces. if the issue was\n",
                "with a range, remove the whitespace around the dash"
            )
            .to_string(),
        }
    }

    pub fn invalid_range_operands(src: &str, pos: (usize, usize)) -> ParseSelectionError {
        ParseSelectionError {
            error: "invalid range operands".to_string(),
            src: NamedSource::new(file!(), src.to_string()),
            pos: pos.into(),
            help: "negative numbers aren't supported".to_string(),
        }
    }

    pub fn missing_range_operands(src: &str, pos: (usize, usize)) -> ParseSelectionError {
        ParseSelectionError {
            error: "missing range operands".to_string(),
            src: NamedSource::new(file!(), src.to_string()),
            pos: pos.into(),
            help: concat!(
                "make sure there's a number before and after the dash\n",
                "note that negative numbers aren't supported"
            )
            .to_string(),
        }
    }

    pub fn invalid_range_order(src: &str, pos: (usize, usize)) -> ParseSelectionError {
        ParseSelectionError {
            error: "start of range greater than end".to_string(),
            src: NamedSource::new(file!(), src.to_string()),
            pos: pos.into(),
            help: "re-order to ascending order".to_string(),
        }
    }

    pub fn overflow(src: &str, pos: (usize, usize)) -> ParseSelectionError {
        ParseSelectionError {
            error: "i32 overflow".to_string(),
            src: NamedSource::new(file!(), src.to_string()),
            pos: pos.into(),
            help: "enter a smaller number".to_string(),
        }
    }
}
