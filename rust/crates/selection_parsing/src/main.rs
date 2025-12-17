use std::num::{IntErrorKind, ParseIntError};

use miette::{ErrReport, IntoDiagnostic, Result};
use rustyline::{DefaultEditor, error::ReadlineError};

mod parse_selection_err;
use parse_selection_err::ParseSelectionError;

/// Helper for [`parse_selection()`]
///
/// Returns a vector with the numbers from `start` to `end` inclusive
fn to_range(start: i32, end: i32) -> Result<Vec<i32>, String> {
    if start > end {
        return Err("Start can't be greater than end; order must be ascending".to_string());
    }

    let mut nums: Vec<i32> = Vec::with_capacity((end - start + 1) as usize);

    // consider adding a bound here
    // e.g. (start + end) <= 10_000
    for i in start..=end {
        nums.push(i as i32);
    }

    Ok(nums)
}

/// Helper for [`parse_selection()`]
///
/// Validates and returns the tokens of a selection.
///
/// Returns `Ok` if all tokens are valid, or a [`ParseSelectionError`]
/// preset which describes the problem encountered.
///
/// # Examples
/// ...
fn validate_selection_tokens<'a>(
    src: &'a str,
    tokens: Vec<&'a str>,
) -> Result<Vec<&'a str>, ParseSelectionError> {
    let mut pos = 0usize;

    for token in &tokens {
        if token.is_empty() {
            return Err(ParseSelectionError::no_selection_comma(src, (pos, 0)));
        }

        for (i, c) in token.chars().enumerate() {
            if c.is_whitespace() {
                return Err(ParseSelectionError::unexpected_whitespace(
                    src,
                    (pos + i, 0),
                ));
            }

            if !c.is_digit(10) && c != '-' {
                return Err(ParseSelectionError::unexpected_token(src, (pos + i, 0)));
            }
        }

        pos += token.len() + 1; // +1 for comma
    }

    Ok(tokens)
}

/// Helper for [`parse_selection()`]
///
/// Validates and returns the individual numbers of a selection.
///
/// Returns `Ok` if all numbers are parsable, or a [`ParseSelectionError`]
/// preset which describes the problem encountered.
fn validate_selection_numbers<'a>(
    src: &str,
    numbers: Vec<(&'a str, usize)>,
) -> Result<Vec<(&'a str, usize)>, ParseSelectionError> {
    for (n, start) in &numbers {
        let span = (start.clone(), n.len());
        let tmp: Result<i32, ParseIntError> = n.parse();

        if tmp
            .as_ref()
            .is_err_and(|e| *e.kind() == IntErrorKind::PosOverflow)
        {
            return Err(ParseSelectionError::overflow(src, span));
        }

        assert!(tmp.is_ok());
    }

    Ok(numbers)
}

/// Helper for [`parse_selection()`]
///
/// Validates and returns the ranges of a selection.
///
/// Returns `Ok` if all ranges are valid, or a [`ParseSelectionError`]
/// preset which describes the problem encountered.
fn validate_selection_ranges<'a>(
    src: &str,
    ranges: Vec<(&'a str, usize)>,
) -> Result<Vec<(&'a str, usize)>, ParseSelectionError> {
    for (range, start) in &ranges {
        // for an arrow rather than a span in `miette`,
        // single chars should have a span length of 0
        let span_len = if range.len() == 1 { 0 } else { range.len() };
        let span = (start.clone(), span_len);
        let r_split: Vec<&str> = range.split("-").collect();

        if r_split.iter().any(|c| c.is_empty()) {
            return Err(ParseSelectionError::missing_range_operands(src, span));
        }

        if r_split.len() != 2 {
            return Err(ParseSelectionError::invalid_range_operands(src, span));
        }

        let (left, right) = (r_split[0].parse::<i32>(), r_split[1].parse::<i32>());

        // overflow should be the only possible error here;
        // otherwise there's a problem with the logic
        if !(left.is_ok() && right.is_ok()) {
            assert_eq!(*left.unwrap_err().kind(), IntErrorKind::PosOverflow);
            assert_eq!(*right.unwrap_err().kind(), IntErrorKind::PosOverflow);

            return Err(ParseSelectionError::overflow(src, span));
        }

        let (left, right) = (left.unwrap(), right.unwrap());

        if left > right {
            return Err(ParseSelectionError::invalid_range_order(src, span));
        }
    }

    Ok(ranges)
}

/// Accepted selections:
///
/// - A chapter: "2"
/// - A range of chapters: "3-8"
/// - A mix of both: "1, 3, 5-8, 11-14"
///
/// Ranges of chapters also include the starting and ending number.
///
/// e.g. "5-8" = Chapter 5, 6, 7, 8
///
/// Notes:
/// - Only ascending order is allowed; 6-2 is not valid.
/// - Negative numbers aren't allowed for simplicity
fn parse_selection(selection_input: String) -> Result<Vec<i32>, ParseSelectionError> {
    // trim trailing commas and whitespace
    let selection = selection_input.trim_matches(',').trim().to_string();

    if selection.is_empty() {
        return Err(ParseSelectionError::no_input());
    }

    let tokens: Vec<&str> = selection.split(',').map(|s| s.trim()).collect();
    let selection = tokens.join(","); // for input source display

    let tokens = validate_selection_tokens(&selection, tokens)?;

    // group individual numbers and ranges
    // the `usize` is the index in `selection` where the token starts
    let mut ranges: Vec<(&str, usize)> = Vec::new();
    let mut numbers: Vec<(&str, usize)> = Vec::new();
    let mut selected: Vec<i32> = Vec::new();

    // store `pos` for diagnostics as tuple
    let mut pos = 0usize;
    for t in tokens.iter() {
        assert!(!t.is_empty());

        if t.contains("-") {
            ranges.push((t, pos));
        } else {
            numbers.push((t, pos));
        }

        pos += t.len() + 1;
    }

    let numbers = validate_selection_numbers(&selection, numbers)?;
    let ranges = validate_selection_ranges(&selection, ranges)?;

    // we can remove `pos` info now that we've validated
    let numbers: Vec<&str> = numbers.iter().map(|tuple| tuple.0).collect();
    let ranges: Vec<&str> = ranges.iter().map(|tuple| tuple.0).collect();

    // unwrapping is also "safe" (well, should be...)
    for n in &numbers {
        selected.push(n.parse().unwrap());
    }

    for r in &ranges {
        let sides: Vec<i32> = r.split("-").map(|s| s.parse::<i32>().unwrap()).collect();
        let (left, right) = (sides[0], sides[1]);
        assert_eq!(sides.len(), 2);

        selected.extend(to_range(left, right).unwrap());
    }

    selected.sort();
    selected.dedup();

    Ok(selected)
}

fn parse_sel_help(input: &str) {
    match parse_selection(input.to_string()) {
        Ok(nums) => println!("{:?}", nums),
        Err(e) => eprintln!("{:?}", ErrReport::from(e)),
    }
}

fn main() -> Result<()> {
    miette::set_panic_hook();
    let mut rl = DefaultEditor::new().into_diagnostic()?;

    loop {
        let input = rl.readline(">> ");

        match input {
            Ok(line) => {
                rl.add_history_entry(line.as_str()).into_diagnostic()?;
                parse_sel_help(&line.trim());
            }
            Err(ReadlineError::Interrupted) => {
                println!("CTRL-C");
                break;
            }
            Err(ReadlineError::Eof) => {
                println!("CTRL-D");
                break;
            }
            Err(err) => {
                println!("Error: {:?}", err);
                break;
            }
        }
    }

    Ok(())
}
