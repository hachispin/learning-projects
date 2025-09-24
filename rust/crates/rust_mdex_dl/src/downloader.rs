//! Contains functions related to downloading and saving images.

use std::path::Path;
use std::sync::Arc;

use bytes::Bytes;
use futures;
use indicatif::{ProgressBar, ProgressStyle};
use miette::{ErrReport, IntoDiagnostic, Result};
use reqwest::{self, Url};
use tokio::{fs, sync::Semaphore};

/// Returns a tuple containing the fetched raw image data as bytes and
/// the file extension without the trailing dot (e.g. png, jpg, etc).
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
/// # Notes
///
/// * the existence of `save_dir` **must** be checked before calling
/// * `page` should be a zero-padded number such as "001".
async fn save_image_data(image_data: (Bytes, String), page: &str, save_dir: &Path) -> Result<()> {
    let filename = format!("{}.{}", page, image_data.1);
    let save_path = save_dir.join(filename);

    fs::write(save_path, image_data.0).await.into_diagnostic()?;
    Ok(())
}

fn get_progress_bar(length: usize) -> ProgressBar {
    let length = length as u64;

    let pb: ProgressBar = ProgressBar::new(length);
    pb.set_style(
        ProgressStyle::with_template(concat!(
            "{spinner:.green} [{elapsed_precise}] ",
            "[{bar:40.cyan/blue}] {pos}/{len} ({eta})"
        ))
        .unwrap()
        .progress_chars("=>-"),
    );

    pb
}

/// Downloads the provided `urls` into `./images/` from cargo root
pub async fn download_images(images: &Vec<Url>) -> Result<()> {
    // semaphore with a clamp between `urls.len()` and 25
    let num_tasks = images.len().clamp(1, 25).into();
    let sema: Arc<Semaphore> = Semaphore::new(num_tasks).into();
    eprintln!("Using {num_tasks} task(s)");
    let pb: Arc<ProgressBar> = get_progress_bar(images.len()).into();

    // make minimal `reqwest::Client` for downloads
    let download_client = reqwest::ClientBuilder::new()
        .user_agent("hachispin/learning-projects")
        .build()
        .into_diagnostic()?;

    let zero_width = format!("{}", images.len()).len();
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).to_path_buf();
    let save_dir = root.join("images");

    if !save_dir.try_exists().into_diagnostic()? {
        fs::create_dir(&save_dir).await.into_diagnostic()?;
    }

    let mut handles = Vec::with_capacity(num_tasks);
    for (i, url) in images.iter().enumerate() {
        let sema = sema.clone();
        let pb = pb.clone();
        let url = url.clone();
        let save_dir = save_dir.clone();
        let download_client = download_client.clone();

        handles.push(tokio::spawn(async move {
            let page = format!("{:0>zero_width$}", i);
            let _permit = sema.acquire().await.unwrap();
            let data = get_image_data(&download_client, &url).await?;
            save_image_data(data, &page, &save_dir).await?;

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
