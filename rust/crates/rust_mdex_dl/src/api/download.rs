//! Contains downloading utilities for chapters, mainly through [`DownloadClient`]

use crate::{
    api::{
        client::ApiClient,
        endpoints::Endpoint,
        models::{Chapter, Manga},
    },
    config::{Config, ImageQuality, Images},
    paths::manga_save_dir,
};

use std::{
    path::PathBuf,
    sync::{
        Arc,
        atomic::{AtomicUsize, Ordering},
    },
};

use bytes::Bytes;
use indicatif::{MultiProgress, ProgressBar, ProgressStyle};
use isolang::Language;
use itertools::Itertools;
use log::{debug, error, info, trace, warn};
use miette::{ErrReport, IntoDiagnostic, Result};
use reqwest::{self, Client, Url};
use sanitise_file_name::sanitise;
use serde::Deserialize;
use serde_json;
use tokio::{sync::Semaphore, time::Instant};

/// Stores the response structure of the [GetChapterCdn](`crate::Endpoint::GetChapterCdn`)
/// endpoint for deserializing.
#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ChapterCdnData {
    hash: String,
    data: Vec<String>,
    data_saver: Vec<String>,
}

/// A wrapper over [`ChapterCdnData`] for constructing image urls.
#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ChapterCdn {
    base_url: Url,
    chapter: ChapterCdnData,
}

impl ChapterCdn {
    // the max requests per minute for `Endpoint::GetChapterCdn`
    // https://api.mangadex.org/docs/2-limitations/#endpoint-specific-rate-limits
    const RATELIMIT: u32 = 40;

    /// Constructs a new [`ChapterCdn`] for the given [`Chapter`]
    pub async fn new(api: &ApiClient, chapter: &Chapter) -> Result<Self> {
        debug!("Fetching CDN for chapter_uuid={}", chapter.uuid());
        let endpoint = Endpoint::GetChapterCdn(chapter.uuid());

        let r_json = api.get_ok_json(endpoint).await.map_err(|e| {
            error!(
                "Failed to fetch cdn for chapter {}: {e}",
                chapter.formatted_title()
            );
            error!("Chapter info: {:?}", chapter);
            miette::miette!("failed to fetch {}", chapter.uuid())
        })?;

        let cdn = serde_json::from_value::<Self>(r_json).into_diagnostic()?;
        let num_lossless = cdn.chapter.data.len();
        let num_lossy = cdn.chapter.data_saver.len();

        if num_lossless != num_lossy {
            warn!(
                "Inconsistent number of images for chapter {}: {} lossless images, {} lossy images.",
                chapter.uuid(),
                num_lossless,
                num_lossy
            );
        }

        if cdn.chapter.hash.is_empty() {
            warn!("Empty `hash` for cdn of chapter {}", chapter.uuid())
        }

        if num_lossless == 0 {
            warn!(
                "Empty `data` (no lossless images) for cdn of chapter {}",
                chapter.uuid()
            );
        }

        if num_lossy == 0 {
            warn!(
                "Empty `data-saver` (no lossy images) for cdn of chapter {}",
                chapter.uuid()
            );
        }

        Ok(cdn)
    }

    /// Constructs the image urls in the format:
    ///
    /// `$.baseUrl / $QUALITY / $.chapter.hash / $.chapter.$QUALITY[*]`
    ///
    /// Reference: https://api.mangadex.org/docs/04-chapter/retrieving-chapter/#howto
    fn construct_image_urls(&self, quality: ImageQuality) -> Result<Vec<Url>> {
        debug!(
            "Constructing image urls, hash={}, quality={:?}",
            self.chapter.hash, quality
        );

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

        debug!("constructed_url_prefix={:?}", url_prefix.as_str());

        let mut images = Vec::with_capacity(image_names.len() + 1);
        for name in image_names {
            images.push(url_prefix.join(name).into_diagnostic()?);
        }

        debug!(
            "first_image_url={:?}",
            images.first().map(|u| u.as_str()),
        );

        trace!(
            "all_image_urls={:?}",
            images.iter().map(|u| u.as_str()).collect::<Vec<&str>>()
        );

        Ok(images)
    }
}

/// Stores info needed for downloading a chapter; used in [`DownloadClient::download_chapter`]
#[derive(Debug)]
struct ChapterDownloadInfo {
    chapter: Chapter,
    cdn: ChapterCdn,
    pb: ProgressBar,
}

impl ChapterDownloadInfo {
    /// Constructs and returns a styled [`ProgressBar`]
    fn get_progress_bar(length: usize) -> ProgressBar {
        let length = length as u64;

        let pb: ProgressBar = ProgressBar::new(length);
        pb.set_style(
            ProgressStyle::with_template(
                "[{elapsed_precise}] [{bar:40.cyan/blue}] {pos}/{len} ({eta})",
            )
            .unwrap()
            .progress_chars("=>-"),
        );

        pb
    }

    /// Using a chapter, fetches its cdn and gives it a progress bar.
    async fn new(api: &ApiClient, chapter: Chapter) -> Result<Self> {
        let cdn = ChapterCdn::new(api, &chapter).await?;
        let num_images = cdn.chapter.data.len();
        let pb = Self::get_progress_bar(num_images);

        Ok(Self { chapter, cdn, pb })
    }
}

/// Handles fetching of cdns and downloading of chapters.
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

    /// Returns a tuple, `(Bytes, String)` on success.
    ///
    /// `Bytes` is self explanatory, while `String` contains the filename
    /// extension **without the leading dot**. (e.g, "png", not ".png")
    ///
    /// Note that the extension can only be "JPEG", "PNG", or "GIF" according to ref.
    ///
    /// Reference: https://api.mangadex.org/docs/04-chapter/upload/#requirements-and-limitations
    async fn download_image(&self, image_url: &Url) -> Result<(Bytes, String)> {
        let ext = image_url.as_str().split('.').next_back().unwrap_or("png");

        if !["png", "jpg", "jpeg", "gif"].contains(&ext) {
            warn!(
                "Unexpected image url extension {:?} for image url {}",
                ext,
                &image_url.as_str()
            );
        }

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
    /// `chapter_dir` should follow the format: `project_root/parent_manga/chapter`
    /// and be created beforehand.
    async fn save_image(
        &self,
        image_info: (Bytes, String),
        chapter_dir: PathBuf,
        page: &str,
    ) -> Result<()> {
        let filename = format!("{}.{}", page, image_info.1);
        let save = chapter_dir.join(filename);

        tokio::fs::write(&save, image_info.0)
            .await
            .into_diagnostic()?;

        trace!("Saved page {} to {:?}", page, &save.to_str());
        Ok(())
    }

    /// Downloads and saves a chapter's images concurrently and returns the total size in bytes.
    ///
    /// This also creates the dirs needed to store these images.
    async fn download_chapter(
        &self,
        download_info: ChapterDownloadInfo,
        parent_manga_title: &str,
        images_cfg: &Images,
    ) -> Result<usize> {
        let images_cfg = images_cfg.clone();
        let images = download_info.cdn.construct_image_urls(images_cfg.quality)?;
        let zero_pad = format!("{}", images.len()).len();

        let chapter_uuid_suffix = download_info.chapter.uuid().to_string()[..8].to_string();
        let chapter_size = Arc::new(AtomicUsize::new(0));
        let chapter_title = &download_info.chapter.formatted_title();

        let parent_manga_title_safe = sanitise(parent_manga_title);
        let chapter_title_safe = sanitise(chapter_title);

        let chapter_dir = &manga_save_dir()
            .join(parent_manga_title_safe)
            .join(chapter_title_safe);

        tokio::fs::create_dir_all(&chapter_dir)
            .await
            .into_diagnostic()?;

        let chapter_dir = chapter_dir.canonicalize().into_diagnostic()?;
        let mut handles = Vec::with_capacity(images.len() + 1);
        let handle_client = Arc::new(self.clone());

        info!(
            "Downloading {} images from chapter {:?} of manga {:?}",
            images.len(),
            download_info.chapter.data.attributes.chapter,
            parent_manga_title,
        );

        let pb = Arc::new(download_info.pb);
        let start = Instant::now();

        for (i, url) in images.into_iter().enumerate() {
            let chapter_uuid_suffix = chapter_uuid_suffix.clone();
            let chapter_dir = chapter_dir.clone();

            // `Arc<T>` clones
            let semaphore = self.image_semaphore.clone();
            let pb = pb.clone();
            let chapter_size = chapter_size.clone();
            let h = handle_client.clone();

            handles.push(tokio::spawn(async move {
                let _permit = semaphore.acquire().await.into_diagnostic()?;
                let page = format!("{:0>zero_pad$}", i);
                let data = h.download_image(&url).await?;

                let size_bytes = data.0.len();
                let size_mib = size_bytes as f64 / 1_048_576.0;

                debug!(
                    "chapter_uuid_suffix={} page={} dl_time_ms={} size_mib={:.3}",
                    chapter_uuid_suffix,
                    page,
                    (Instant::now() - start).as_millis(),
                    size_mib,
                );

                chapter_size.fetch_add(size_bytes, Ordering::Relaxed);
                h.save_image(data, chapter_dir, &page).await?;

                pb.inc(1);
                Ok::<(), ErrReport>(())
            }));
        }

        futures::future::try_join_all(handles)
            .await
            .into_diagnostic()?;

        let chapter_size = chapter_size.load(Ordering::Relaxed);

        info!(
            "({}) Completed downloads in {}ms, total size is {:.3} MiB",
            chapter_uuid_suffix,
            (Instant::now() - start).as_millis(),
            chapter_size as f64 / 1_048_576.0,
        );

        pb.finish_and_clear();
        Ok(chapter_size)
    }

    /// Helper for [`Self::download_chapters`]
    async fn _download_chapters(
        &self,
        batch: Vec<ChapterDownloadInfo>,
        parent_manga: Arc<Manga>,
        pb_multi: &MultiProgress,
        images_cfg: &Images,
    ) -> Result<usize> {
        let start = Instant::now();
        let batch_size = Arc::new(AtomicUsize::new(0));
        let batch_len = batch.len();
        let parent_uuid = parent_manga.uuid();
        let parent_manga_title = parent_manga.title(self.language);
        let mut handles = Vec::with_capacity(batch.len() + 1);

        for info in batch {
            if info.chapter.parent_uuid() != parent_uuid {
                warn!(
                    "Expected chapter {} to have parent manga {}, instead got {}",
                    info.chapter.uuid(),
                    parent_uuid,
                    info.chapter.parent_uuid()
                );
                warn!("This may lead to chapters being saved to the wrong locations!");
            }

            pb_multi.add(info.pb.clone());

            let h = self.clone();
            let images_cfg = images_cfg.clone();
            let parent_manga_title = parent_manga_title.clone();

            // arc clones
            let semaphore = self.chapter_semaphore.clone();
            let batch_size = batch_size.clone();

            handles.push(tokio::spawn(async move {
                let _permit = semaphore.acquire().await.into_diagnostic()?;

                let chapter_size = h
                    .download_chapter(info, &parent_manga_title, &images_cfg)
                    .await?;

                batch_size.fetch_add(chapter_size, Ordering::Relaxed);

                Ok::<(), ErrReport>(())
            }));
        }

        futures::future::try_join_all(handles)
            .await
            .into_diagnostic()?;

        let batch_size = batch_size.load(Ordering::Relaxed);

        info!(
            "Batch download ({} chapters) completed in {}ms, total size is {:.3} MiB",
            batch_len,
            (Instant::now() - start).as_millis(),
            batch_size as f64 / 1_048_576.0,
        );

        Ok(batch_size)
    }

    /// Downloads all chapters given.
    ///
    /// Chapters are also downloaded concurrently, using
    /// [`Self::chapter_semaphore`] for the number of permits.
    ///
    /// NOTE: **All of these chapters should come from the same parent manga.**
    /// A warning is logged otherwise.
    pub async fn download_chapters(
        &self,
        api: &ApiClient,
        chapters: Vec<Chapter>,
        parent_manga: Manga,
        images_cfg: &Images,
    ) -> Result<()> {
        let start = Instant::now();
        let pb_multi = MultiProgress::new();
        let parent_manga = Arc::new(parent_manga);
        let manga_size = Arc::new(AtomicUsize::new(0));

        info!(
            "Downloading {} chapters of manga {:?}, manga_uuid={}",
            chapters.len(),
            parent_manga.title(self.language),
            parent_manga.uuid()
        );

        let dl_info_futs: Vec<_> = chapters
            .into_iter()
            .map(|c| async move { ChapterDownloadInfo::new(api, c).await })
            .collect();

        for batch in dl_info_futs
            .into_iter()
            .chunks(ChapterCdn::RATELIMIT as usize)
            .into_iter()
        {
            let batch = futures::future::try_join_all(batch).await;

            let batch = match batch {
                Ok(v) => v,
                Err(e) => {
                    error!(
                        "Encountered error {e} while using fetched cdns in `dl_info_results`!"
                    );
                    continue;
                }
            };

            let batch_size = self
                ._download_chapters(batch, parent_manga.clone(), &pb_multi, images_cfg)
                .await?;

            manga_size.fetch_add(batch_size, Ordering::Relaxed);
        }

        let manga_size = manga_size.load(Ordering::Relaxed);

        info!(
            "All downloads completed in {}ms, total size is {:.3} MiB",
            (Instant::now() - start).as_millis(),
            manga_size as f64 / 1_048_576.0,
        );

        Ok(())
    }
}
