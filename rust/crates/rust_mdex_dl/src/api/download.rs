use crate::{
    api::models::{Chapter, Manga},
    config::{Config, ImageQuality, Images},
    paths::manga_save_dir,
};

use std::{path::PathBuf, sync::Arc};

use bytes::Bytes;
use indicatif::{ProgressBar, ProgressStyle};
use isolang::Language;
use miette::{ErrReport, IntoDiagnostic, Result};
use reqwest::{self, Client, Url};
use serde::Deserialize;
use serde_json;
use tokio::{sync::Semaphore, time::Instant};

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ChapterCdnData {
    hash: String,
    data: Vec<String>,
    data_saver: Vec<String>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ChapterCdn {
    base_url: Url,
    chapter: ChapterCdnData,
}

impl ChapterCdn {
    /// Constructs a new [`ChapterCdn`].
    ///
    /// The response, `r_json` must be from [`Endpoint::GetChapterCdn`] for this to work.
    pub fn new(r_json: &serde_json::Value) -> Result<Self> {
        serde_json::from_value(r_json.clone()).into_diagnostic()
    }

    /// Constructs the image urls in the format:
    ///
    /// `$.baseUrl / $QUALITY / $.chapter.hash / $.chapter.$QUALITY[*]`
    ///
    /// Reference: https://api.mangadex.org/docs/04-chapter/retrieving-chapter/#howto
    fn construct_image_urls(&self, quality: ImageQuality) -> Result<Vec<Url>> {
        info!("Constructing image urls with quality '{quality:?}'");

        let quality = match quality {
            ImageQuality::Lossless => "data",
            ImageQuality::Lossy => "data-saver",
        };

        let image_names = match quality {
            "data" => &self.chapter.data,
            "data-saver" => &self.chapter.data_saver,
            _ => unreachable!(),
        };

        let url_prefix = self
            .base_url
            .join(&format!("{quality}/"))
            .into_diagnostic()?
            .join(&format!("{}/", &self.chapter.hash))
            .into_diagnostic()?;
        debug!("Image url prefix {:?}", url_prefix.as_str());

        let mut images = Vec::with_capacity(image_names.len() + 1);
        for name in image_names {
            images.push(url_prefix.join(&name).into_diagnostic()?);
        }

        debug!(
            "First image url: {:?}",
            images.iter().next().and_then(|u| Some(u.as_str()))
        );

        trace!(
            "All image urls: {:?}",
            images.iter().map(|u| u.as_str()).collect::<Vec<&str>>()
        );

        Ok(images)
    }
}

#[derive(Debug, Clone)]
pub struct DownloadClient {
    client: Client,
    language: Language,
    image_semaphore: Arc<Semaphore>,
    chapter_semaphore: Arc<Semaphore>,
}

impl DownloadClient {
    /// Constructs a new [`DownloadClient`].
    ///
    /// If [`Client::builder`] fails, returns Err value.
    pub fn new(cfg: &Config) -> Result<Self> {
        let user_agent = cfg.client.user_agent.clone();
        let chapter_permits = cfg.concurrency.chapter_permits;
        let image_permits = cfg.concurrency.image_permits;

        let client = Client::builder()
            .user_agent(user_agent)
            .build()
            .into_diagnostic()?;

        let image_semaphore = Arc::from(Semaphore::new(image_permits));
        let language = cfg.client.language;
        let chapter_semaphore = Arc::from(Semaphore::new(chapter_permits));

        Ok(Self {
            client,
            language,
            image_semaphore,
            chapter_semaphore,
        })
    }

    /* Helpers for `download_chapter()` */

    /// Constructs and returns a styled [`ProgressBar`] wrapped in [`Arc<T>`]
    fn get_progress_bar(length: usize) -> Arc<ProgressBar> {
        let length = length as u64;

        let pb: ProgressBar = ProgressBar::new(length);
        pb.set_style(
            ProgressStyle::with_template(
                "[{elapsed_precise}] [{bar:40.cyan/blue}] {pos}/{len} ({eta})",
            )
            .unwrap()
            .progress_chars("=>-"),
        );

        Arc::new(pb)
    }

    /// Returns a tuple, `(Bytes, String)` on success.
    ///
    /// `Bytes` is self explanatory, while `String` contains the filename
    /// extension **without the leading dot**. (e.g, "png", not ".png")
    ///
    /// Note that the extension can only be "JPEG", "PNG", or "GIF" according to ref.
    ///
    /// Reference: https://api.mangadex.org/docs/04-chapter/upload/#requirements-and-limitations
    async fn download_image(&self, image_url: &Url) -> Result<(Bytes, String)> {
        let ext = image_url.as_str().split('.').last().unwrap_or("png");
        assert!(["png", "jpg", "jpeg", "gif"].iter().any(|v| ext == *v));

        let data = self
            .client
            .get(image_url.as_ref())
            .send()
            .await
            .into_diagnostic()?
            .bytes()
            .await
            .into_diagnostic()?;

        trace!("Downloaded image {:?}", image_url.as_str());
        Ok((data, ext.to_string()))
    }

    /// Saves the image bytes into `chapter_dir` using `page`, which should be zero-padded.
    ///
    /// The tuple, `image_info` comes from [`Self::download_image`],
    /// formatted as `(image_bytes, image_file_format)` accordingly.
    ///
    /// `chapter_dir` should be the path: `project_root/parent_manga/chapter`
    /// and should be created beforehand.
    async fn save_image(
        &self,
        image_info: (Bytes, String),
        chapter_dir: PathBuf,
        page: &str,
    ) -> Result<()> {
        let filename = format!("{}.{}", page, image_info.1);
        let save = chapter_dir.join(filename);

        tokio::fs::write(chapter_dir.join(&save), image_info.0)
            .await
            .into_diagnostic()?;

        trace!("Saved page {} to {:?}", page, &save.to_str());
        Ok(())
    }

    /// Downloads a chapter's images.
    pub async fn download_chapter(
        &self,
        cdn: ChapterCdn,
        chapter: Chapter,
        parent_manga: Manga,
        images_cfg: &Images,
    ) -> Result<()> {
        let images_cfg = images_cfg.clone();
        let images = cdn.construct_image_urls(images_cfg.quality)?;
        let zero_pad = format!("{}", images.len()).len();

        let manga_title = &parent_manga.title(self.language);
        let chapter_title = &chapter.formatted_title();
        let chapter_dir = &manga_save_dir().join(manga_title).join(chapter_title);

        std::fs::create_dir_all(&chapter_dir).into_diagnostic()?;
        let chapter_dir = chapter_dir.canonicalize().into_diagnostic()?;

        let pb = DownloadClient::get_progress_bar(images.len());
        let mut handles = Vec::with_capacity(images.len() + 1);
        let handle_client = Arc::new(self.clone());

        info!(
            "Downloading {} images from chapter {:?} of manga {:?}",
            images.len(),
            chapter.data.attributes.chapter,
            manga_title,
        );

        let start = Instant::now();

        for (i, url) in images.iter().enumerate() {
            // clone for async **move**
            let semaphore = self.image_semaphore.clone();
            let pb = pb.clone();
            let url = url.clone();
            let chapter_dir = chapter_dir.clone();
            let h = handle_client.clone();

            handles.push(tokio::spawn(async move {
                let _permit = semaphore.acquire().await.into_diagnostic()?;
                let page = format!("{:0>zero_pad$}", i);
                let data = h.download_image(&url).await?;

                debug!(
                    "Page {} downloaded in {}ms, size is {} bytes",
                    page,
                    (Instant::now() - start).as_millis(),
                    data.0.len()
                );

                h.save_image(data, chapter_dir, &page).await?;

                pb.inc(1);
                Ok::<(), ErrReport>(())
            }));
        }

        futures::future::try_join_all(handles)
            .await
            .into_diagnostic()?;

        info!(
            "Completed downloads in {}ms",
            (Instant::now() - start).as_millis()
        );

        pb.finish();
        Ok(())
    }

    pub async fn download_chapters() {}
}
