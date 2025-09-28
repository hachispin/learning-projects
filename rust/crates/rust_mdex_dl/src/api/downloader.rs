//! Contains functions related to downloading and saving images.

use crate::config::Config;
use crate::paths::manga_save_dir;

use std::sync::Arc;

use bytes::Bytes;
use futures;
use indicatif::{ProgressBar, ProgressStyle};
use miette::{ErrReport, IntoDiagnostic, Result};
use reqwest::{self, Url};
use tokio::{fs, sync::Semaphore};

#[derive(Debug)]
/// Stores the JSON response of `GET at-home/server/:chapterId`
pub struct ChapterCdnInfo {
    base_url: String,
    hash: String,
    data: Vec<String>,
    data_saver: Vec<String>,
}

impl ChapterCdnInfo {
    /// Creates a new [`ChapterCdnInfo`] by reading `cdn_info`
    ///
    /// This should only be used with JSON from `GET at-home/server/:chapterId`
    /// Panics from [`Option::unwrap()`] will occur otherwise.
    ///
    /// This function is built upon the assumption that [`ApiClient::get_ok_json()`] is used.
    /// There should be no "errors" field and status is successful (200-299)
    pub fn new(cdn_info: &serde_json::Value) -> ChapterCdnInfo {
        let base_url = cdn_info["baseUrl"].as_str().unwrap().to_string();
        let chapter = cdn_info["chapter"].as_object().unwrap();
        let hash = chapter["hash"].as_str().unwrap().to_string();

        let data: Vec<String> = chapter["data"]
            .as_array()
            .unwrap()
            .iter()
            .map(|v| v.as_str().unwrap().to_string())
            .collect();

        let data_saver: Vec<String> = chapter["dataSaver"]
            .as_array()
            .unwrap()
            .iter()
            .map(|v| v.as_str().unwrap().to_string())
            .collect();

        ChapterCdnInfo {
            base_url,
            hash,
            data,
            data_saver,
        }
    }

    /// The constructed page urls are in the format:
    ///
    /// `$.baseUrl / $QUALITY / $.chapter.hash / $.chapter.$QUALITY[*]`
    pub fn construct_image_urls(&self, use_data_saver: bool) -> Result<Vec<Url>> {
        let quality = if use_data_saver { "data-saver" } else { "data" };
        let pages = if use_data_saver {
            &self.data_saver
        } else {
            &self.data
        };

        let mut urls: Vec<Url> = Vec::with_capacity(pages.len() + 1);
        let url_prefix_fmt = format!("{}/{}/{}/", self.base_url, quality, self.hash);
        let url_prefix = Url::parse(&url_prefix_fmt).into_diagnostic()?;

        for page in pages {
            let url = url_prefix.join(page).into_diagnostic()?;
            urls.push(url);
        }

        Ok(urls)
    }
}

/// Returns a tuple containing the fetched raw image data as bytes and
/// the file extension **without the leading dot** (e.g. png, jpg, etc).
async fn get_image_data(client: &reqwest::Client, image_url: &Url) -> Result<(Bytes, String)> {
    let ext = image_url
        .as_str()
        .split('.')
        .last()
        .unwrap_or("jpg")
        .to_string();

    let data = client
        .get(image_url.to_owned())
        .send()
        .await
        .into_diagnostic()?
        .bytes()
        .await
        .into_diagnostic()?;

    Ok((data, ext))
}

/// Saves images in `{save_dir}/{file_num}.{ext}` using the tuple from
/// [`Client::get_image_data()`] for the `image_data` parameter.
///
/// ## Notes
///
/// * the existence of `save_dir` **must** be checked before calling
/// * `page` should be a zero-padded number such as "001".
async fn save_image_data(image_data: (Bytes, String), page: &str) -> Result<()> {
    let filename = format!("{}.{}", page, image_data.1);

    fs::write(manga_save_dir().join(filename), image_data.0)
        .await
        .into_diagnostic()?;
    Ok(())
}

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

/// Downloads the provided `images` into [`manga_save_dir()`]
///
/// This uses a [`Semaphore`] to allow for concurrent image downloading.
/// The number of permits is set in `cfg` under concurrency.
pub async fn download_images(images: &Vec<Url>, cfg: &Config) -> Result<()> {
    let cfg = cfg.clone();
    let num_tasks = images.len().clamp(1, cfg.concurrency.image_permits).into();
    let zero_width = format!("{}", images.len()).len();

    let pb: Arc<ProgressBar> = get_progress_bar(images.len()).into();
    let sema: Arc<Semaphore> = Semaphore::new(num_tasks).into();
    let mut handles = Vec::with_capacity(images.len() + 1);

    let download_client = reqwest::ClientBuilder::new()
        .user_agent(cfg.client.user_agent)
        .build()
        .into_diagnostic()?;

    for (i, url) in images.iter().enumerate() {
        let sema = sema.clone();
        let pb = pb.clone();
        let url = url.clone();
        let download_client = download_client.clone();

        handles.push(tokio::spawn(async move {
            let page = format!("{:0>zero_width$}", i);
            let _permit = sema.acquire().await.unwrap();
            let data = get_image_data(&download_client, &url).await?;
            save_image_data(data, &page).await?;

            pb.inc(1);
            Ok::<(), ErrReport>(())
        }));
    }

    futures::future::try_join_all(handles)
        .await
        .into_diagnostic()?;

    pb.finish();
    Ok(())
}
