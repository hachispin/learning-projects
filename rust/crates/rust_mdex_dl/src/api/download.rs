use crate::{
    Endpoint,
    api::models::{Chapter, Manga},
    config::Config,
};

use std::sync::Arc;

use isolang::Language;
use miette::{IntoDiagnostic, Result};
use reqwest::{self, Client, Url};
use tokio::sync::Semaphore;

pub struct DownloadClient {
    client: Client,
    base_url: Url,
    language: Language,
    image_semaphore: Arc<Semaphore>,
    chapter_semaphore: Arc<Semaphore>,
}

impl DownloadClient {
    pub fn new(cfg: &Config) -> Result<Self> {
        let user_agent = cfg.client.user_agent.clone();
        let chapter_permits = cfg.concurrency.chapter_permits;
        let image_permits = cfg.concurrency.image_permits;

        let client = Client::builder()
            .user_agent(user_agent)
            .build()
            .into_diagnostic()?;

        let base_url = cfg.client.base_url.clone();
        let image_semaphore = Arc::from(Semaphore::new(image_permits));
        let language = cfg.client.language;
        let chapter_semaphore = Arc::from(Semaphore::new(chapter_permits));

        Ok(Self {
            client,
            base_url,
            language,
            image_semaphore,
            chapter_semaphore,
        })
    }

    // pub fn download_chapter(&self, chapter: Chapter, parent_manga: Manga) -> Result<()> {
    //     let manga_title = parent_manga.title(self.language);
    //     let chapter_title = chapter.formatted_title(self.language);
    // }
}
