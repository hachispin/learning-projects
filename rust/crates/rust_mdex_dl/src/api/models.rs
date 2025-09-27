//! Contains the `Manga` and `Chapter` structs/impls

use crate::ApiClient;
use crate::api::endpoints::Endpoint;

use miette::{IntoDiagnostic, Result};
use reqwest::Url;
use uuid::Uuid;

struct Manga {
    title: String,
}

/// Contains chapter info.
///
/// This is designed to be eager; the [new()](`Self::new()`) function
/// makes a request to gather all info needed given a chapter's uuid.
#[allow(unused)]
struct Chapter {
    uuid: Uuid,
    title: String,
    chapter: usize,
    parent: Manga,
    scanlation_group: String,
    volume: Option<usize>,
}

impl Chapter {}
