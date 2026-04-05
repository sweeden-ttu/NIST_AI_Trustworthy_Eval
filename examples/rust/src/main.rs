use anyhow::Result;
use clap::Parser;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Input JSON file
    #[arg(short, long, default_value = "input.json")]
    input: String,

    /// Output JSON file
    #[arg(short, long, default_value = "output.json")]
    output: String,

    /// Output format
    #[arg(short, long, value_enum, default_value = "json")]
    format: OutputFormat,
}

#[derive(clap::ValueEnum, Clone, Debug)]
enum OutputFormat {
    Json,
    Yaml,
    Csv,
}

#[derive(Serialize, Deserialize, Debug)]
struct AnalysisResult {
    experiment_id: String,
    question: String,
    statistics: Statistics,
    distributions: HashMap<String, Vec<f64>>,
}

#[derive(Serialize, Deserialize, Debug)]
struct Statistics {
    mean: f64,
    median: f64,
    std_dev: f64,
    min: f64,
    max: f64,
    count: usize,
}

fn main() -> Result<()> {
    let args = Args::parse();

    println!("Analyzing statistics from: {}", args.input);

    // Read input
    let input_data = std::fs::read_to_string(&args.input)?;
    let data: serde_json::Value = serde_json::from_str(&input_data)?;

    // Extract metrics
    let metrics = extract_metrics(&data);

    // Calculate statistics
    let stats = calculate_statistics(&metrics);

    // Create result
    let result = AnalysisResult {
        experiment_id: data["experiment_id"]
            .as_str()
            .unwrap_or("unknown")
            .to_string(),
        question: data["question"].as_str().unwrap_or("unknown").to_string(),
        statistics: stats,
        distributions: HashMap::new(),
    };

    // Write output
    match args.format {
        OutputFormat::Json => {
            let json = serde_json::to_string_pretty(&result)?;
            std::fs::write(&args.output, json)?;
        }
        OutputFormat::Yaml => {
            let yaml = serde_yaml::to_string(&result)?;
            std::fs::write(&args.output, yaml)?;
        }
        OutputFormat::Csv => {
            let csv = metrics_to_csv(&metrics);
            std::fs::write(&args.output, csv)?;
        }
    }

    println!("Results written to: {}", args.output);
    Ok(())
}

fn extract_metrics(data: &serde_json::Value) -> Vec<f64> {
    let mut metrics = Vec::new();

    if let Some(evaluation) = data.get("metrics").and_then(|m| m.get("evaluation")) {
        if let Some(accuracy) = evaluation.get("accuracy").and_then(|v| v.as_f64()) {
            metrics.push(accuracy);
        }
        if let Some(f1) = evaluation.get("f1_score").and_then(|v| v.as_f64()) {
            metrics.push(f1);
        }
        if let Some(medal) = evaluation.get("any_medal_rate").and_then(|v| v.as_f64()) {
            metrics.push(medal);
        }
    }

    metrics
}

fn calculate_statistics(values: &[f64]) -> Statistics {
    if values.is_empty() {
        return Statistics {
            mean: 0.0,
            median: 0.0,
            std_dev: 0.0,
            min: 0.0,
            max: 0.0,
            count: 0,
        };
    }

    let count = values.len();
    let sum: f64 = values.iter().sum();
    let mean = sum / count as f64;

    let mut sorted = values.to_vec();
    sorted.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let median = if count % 2 == 0 {
        (sorted[count / 2 - 1] + sorted[count / 2]) / 2.0
    } else {
        sorted[count / 2]
    };

    let variance: f64 = values.iter().map(|v| (v - mean).powi(2)).sum::<f64>() / count as f64;
    let std_dev = variance.sqrt();

    Statistics {
        mean,
        median,
        std_dev,
        min: *sorted.first().unwrap_or(&0.0),
        max: *sorted.last().unwrap_or(&0.0),
        count,
    }
}

fn metrics_to_csv(values: &[f64]) -> String {
    let mut csv = String::from("index,value\n");
    for (i, v) in values.iter().enumerate() {
        csv.push_str(&format!("{},{}\n", i, v));
    }
    csv
}
