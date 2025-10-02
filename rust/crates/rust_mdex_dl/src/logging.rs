//! Contains the function [`init_logging`], which is self-explanatory.

use crate::{config::Logging, paths::log_save_dir};

use std::fs::File;

use chrono::Utc;
use simplelog::{ConfigBuilder, WriteLogger};

/// Initialises logging and creates a log file to write all messages to.
/// This should only be called once.
///
/// This function may panic with [`log::SetLoggerError`]
/// or [`std::io::Error`], which is intentional.
pub fn init_logging(logging_cfg: &Logging) {
    if !logging_cfg.enabled {
        return;
    }

    let now = Utc::now().format("%Y-%m-%d_%H-%M-%S");
    let log_file = log_save_dir().join(format!("{now}.log"));
    let config = ConfigBuilder::new()
        .add_filter_ignore_str("rustyline")
        .set_target_level(logging_cfg.filter)
        .build();

    WriteLogger::init(logging_cfg.filter, config, File::create(log_file).unwrap()).unwrap()
}
