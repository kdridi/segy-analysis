# SEG-Y Prospect Analyzer CLI Tool

A command-line tool for analyzing SEG-Y seismic data files to identify prospects including amplitude anomalies and structural traps.

## Features

- **Amplitude Anomaly Detection**: Identifies areas with unusually high/low amplitudes that may indicate hydrocarbon reservoirs
- **Structural Trap Detection**: Finds coherent patterns that may represent structural traps
- **JSON Output**: Structured output with coordinates, depth, and confidence scores
- **Configurable Parameters**: Adjustable detection thresholds for different datasets
- **Works with Real SEG-Y Files**: Compatible with standard SEG-Y format files

## Installation

Ensure you have the required dependencies:

```bash
pip install numpy segyio scipy
```

## Usage

### Basic Usage

```bash
python3 scripts/segy_prospect_analyzer.py <input_file.sgy>
```

This will create a JSON file named `<input_file>_prospects.json` with the analysis results.

### Examples

**1. Basic analysis with default parameters:**
```bash
python3 scripts/segy_prospect_analyzer.py data/segy-samples/sample_2d_small.sgy
```

**2. Custom detection thresholds:**
```bash
python3 scripts/segy_prospect_analyzer.py data.sgy \
    --anomaly-threshold 3.0 \
    --trap-prominence 0.4
```

**3. Export to specific output file:**
```bash
python3 scripts/segy_prospect_analyzer.py data.sgy --output results.json
```

**4. Output to stdout for piping:**
```bash
python3 scripts/segy_prospect_analyzer.py data.sgy --output - | jq '.summary'
```

**5. Verbose mode with detailed progress:**
```bash
python3 scripts/segy_prospect_analyzer.py data.sgy --verbose
```

## Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--anomaly-threshold` | Standard deviation threshold for amplitude anomalies | 2.5 |
| `--trap-prominence` | Prominence threshold for structural traps (0.0-1.0) | 0.3 |
| `--output` | Output file path (use "-" for stdout) | `<input>_prospects.json` |
| `--no-pretty` | Disable pretty JSON formatting | False |
| `--verbose` | Enable detailed progress output | False |

## Output Format

The tool outputs JSON with the following structure:

```json
{
  "amplitude_anomalies": [
    {
      "id": "AA-001",
      "type": "amplitude_anomaly",
      "coordinates": {
        "x": 200.0,
        "y": 0.0,
        "trace": 4,
        "sample": 489
      },
      "depth": {
        "time_s": 0.978,
        "sample_index": 489
      },
      "amplitude": {
        "value": 0.832,
        "deviation_std": 6.872
      },
      "cluster_size": 219,
      "confidence": 1.0,
      "description": "Amplitude anomaly at 0.978s with high confidence. Cluster size: 219 samples."
    }
  ],
  "structural_traps": [
    {
      "id": "ST-001",
      "type": "structural_trap",
      "coordinates": {
        "x": 750.0,
        "y": 0.0,
        "trace": 15,
        "sample": 378
      },
      "depth": {
        "time_s": 0.756,
        "sample_index": 378
      },
      "amplitude": -0.142,
      "coherence": 0.461,
      "confidence": 1.0,
      "description": "Potential structural trap at 0.756s with high confidence. Coherence: 0.46."
    }
  ],
  "summary": {
    "total_prospects": 35,
    "amplitude_anomalies_count": 1,
    "structural_traps_count": 34,
    "high_confidence_count": 7,
    "input_file": "sample_2d_small.sgy",
    "data_shape": [30, 500],
    "analysis_parameters": {
      "anomaly_threshold_std": 2.5,
      "trap_prominence_threshold": 0.3
    }
  }
}
```

## Output Fields

### Common Fields

- **id**: Unique identifier (AA-XXX for amplitude anomalies, ST-XXX for structural traps)
- **type**: Type of prospect detected
- **coordinates**:
  - **x**: X coordinate from source header
  - **y**: Y coordinate from source header
  - **trace**: Trace number in the file
  - **sample**: Sample index within the trace
- **depth**:
  - **time_s**: Time in seconds
  - **sample_index**: Sample index
- **confidence**: Confidence score (0.0 to 1.0)
- **description**: Human-readable description

### Amplitude Anomaly Specific Fields

- **amplitude**:
  - **value**: Actual amplitude value
  - **deviation_std**: Deviation from mean in standard deviations
- **cluster_size**: Number of samples in the anomalous cluster

### Structural Trap Specific Fields

- **amplitude**: Amplitude value at the trap location
- **coherence**: Local coherence score (0.0 to 1.0)

## Detection Algorithms

### Amplitude Anomaly Detection

Uses statistical analysis to find values that deviate significantly from the mean:

1. Calculates global mean and standard deviation
2. Identifies values exceeding the threshold (default: 2.5σ)
3. Groups nearby anomalies into clusters
4. Reports clusters above minimum size threshold

### Structural Trap Detection

Uses peak detection and coherence analysis:

1. Normalizes trace data
2. Finds peaks using prominence threshold
3. Calculates local coherence across neighboring traces
4. Reports coherent features that may indicate structural traps

## Confidence Scoring

Confidence scores range from 0.0 to 1.0:

- **0.7 - 1.0**: High confidence - strong signal, well-defined features
- **0.4 - 0.7**: Moderate confidence - detectable features but less robust
- **0.0 - 0.4**: Low confidence - weak or ambiguous features

## Performance Notes

- Processing time scales with file size (traces × samples)
- Large files (>10,000 traces) may take several minutes
- Memory usage is approximately 8 bytes per sample point
- Duplicate removal is applied to prevent reporting overlapping prospects

## Tips for Best Results

1. **Start with default parameters**: The defaults work well for most datasets
2. **Adjust thresholds based on data quality**:
   - Noisy data: Increase `--anomaly-threshold` to 3.0-4.0
   - Clean data: Lower to 2.0 for more sensitivity
3. **Use verbose mode**: Monitor progress on large files
4. **Review confidence scores**: Focus on high-confidence prospects first
5. **Check the summary**: Always review the summary statistics

## Troubleshooting

**No prospects detected:**
- Try lowering the detection thresholds
- Check if the SEG-Y file has valid data
- Use `--verbose` to see what's happening

**Too many prospects detected:**
- Increase the `--anomaly-threshold` or `--trap-prominence`
- Focus on high-confidence results only

**File loading errors:**
- Verify the SEG-Y file format
- Check file permissions
- Ensure the file is not corrupted

## Integration with Other Tools

The JSON output can be easily integrated with:

- **GIS software**: Import coordinates for mapping
- **Visualization tools**: Plot prospects alongside seismic sections
- **Database systems**: Store results for further analysis
- **Machine learning**: Use as features for prediction models

## Example Workflow

```bash
# 1. Analyze SEG-Y file
python3 scripts/segy_prospect_analyzer.py survey_data.sgy --output prospects.json

# 2. Extract high-confidence prospects
cat prospects.json | jq '.structural_traps[] | select(.confidence > 0.7)'

# 3. Generate summary report
cat prospects.json | jq '.summary'

# 4. Export coordinates for mapping
cat prospects.json | jq '.amplitude_anomalies[].coordinates' > coords.json
```

## Technical Details

- **SEG-Y Reading**: Uses `segyio` library for robust file handling
- **Signal Processing**: Uses `scipy` for peak detection and filtering
- **Clustering**: Uses connected component analysis for anomaly grouping
- **Coordinate System**: Extracts from SEG-Y trace headers (SourceX, SourceY)

## Version History

- **v1.0** (2026-03-18): Initial release with amplitude anomaly and structural trap detection

## Support

For issues or questions, please refer to the project documentation or contact the development team.