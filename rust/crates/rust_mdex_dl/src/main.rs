use std::time::Instant;

mod client;
mod downloader;
mod errors;

use crate::client::ChapterCdnInfo;
use client::Client;
use errors::UuidError;

use miette::{self, ErrReport, IntoDiagnostic, Result};
use rustyline::history::FileHistory;
use tokio;

/// caller should've converted `uuid` into lowercase prior
fn validate_uuid(uuid: &str) -> Result<&str> {
    if uuid.len() != 36 {
        return Err(ErrReport::from(UuidError::invalid_length(uuid)));
    }

    // `char::is_ascii_hexdigit()` isn't used because
    // mangadex doesn't accept capital letters in uuids.
    for (i, c) in uuid.chars().enumerate() {
        if !"0123456789abcdef-".contains(c) {
            return Err(ErrReport::from(UuidError::invalid_token(uuid, i)));
        }
    }

    let parts_lengths: Vec<usize> = uuid.split("-").map(|p| p.len()).collect();

    if parts_lengths.len() != 5 {
        return Err(ErrReport::from(UuidError::invalid_chunk_count(
            uuid,
            parts_lengths.len(),
        )));
    }

    let mut pos = 0usize;
    for (part_length, expected_length) in parts_lengths.iter().zip(UuidError::CHUNK_SIZES) {
        if part_length != &expected_length {
            return Err(ErrReport::from(UuidError::invalid_chunk_length(
                uuid,
                (pos, *part_length),
                expected_length,
                *part_length,
            )));
        }

        pos += part_length + 1; // for hyphen
    }

    Ok(uuid)
}

/// Prompts the user continuously until a valid UUID is provided.
///
/// Note that this doesn't mean the UUID actually exists.
fn get_valid_uuid(
    rl: &mut rustyline::Editor<(), FileHistory>,
    prompt: Option<&str>,
) -> Result<String> {
    loop {
        let read = rl.readline(prompt.unwrap_or("Enter a UUID: "));
        let uuid = read
            .into_diagnostic()?
            .to_ascii_lowercase()
            .trim()
            .to_string();

        rl.add_history_entry(&uuid).into_diagnostic()?;

        match validate_uuid(&uuid) {
            Ok(_) => return Ok(uuid),
            Err(e) => eprintln!("{:?}", e),
        }
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    miette::set_panic_hook();

    let c = Client::new("https://api.mangadex.org", None)?;
    let mut rl = rustyline::DefaultEditor::new().into_diagnostic()?;

    println!("here's a test uuid: a54c491c-8e4c-4e97-8873-5b79e59da210");
    let chapter_uuid = get_valid_uuid(&mut rl, None)?;

    let r_json = c
        .get_ok_json(&format!("/at-home/server/{chapter_uuid}"))
        .await?;

    let cdn_info = ChapterCdnInfo::new(&r_json);
    let urls = cdn_info.construct_image_urls(false)?;

    let start = Instant::now();
    downloader::download_images(&urls).await?;
    eprintln!("{}", start.elapsed().as_millis());
    eprintln!("image 1: {}", urls.first().unwrap());

    Ok(())
}
