# Seismic Data Processing Pipeline

## Overview

This guide documents the enhanced SEG-Y data processing pipeline designed for robust seismic data handling, quality control, and analysis.

## Architecture

### Core Components

1. **SegyDataLoader**: Memory-efficient SEG-Y file loading with error handling
2. **SeismicProcessor**: High-level pipeline orchestration
3. **QualityMetrics**: Data quality control and validation
4. **SegyMetadata**: Structured metadata container

### Key Features

- **Memory Efficient**: Supports full file or subset loading
- **Quality Control**: Built-in QC checks for data integrity
- **Error Handling**: Robust exception handling and logging
- **Type Hints**: Full type annotations for better IDE support
- **Structured Logging**: Clear logging for debugging and monitoring

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Core dependencies
pip install segyio numpy scipy matplotlib
```

## Usage

### Basic Pipeline Usage

```python
from scripts.seismic_pipeline import SeismicProcessor

# Create processor
processor = SeismicProcessor()

# Process SEG-Y file
results = processor.process_file("data/segy-samples/sample_2d_hires.sgy")

# Check results
if results['success']:
    print(f"QC Pass: {results['qc_metrics']['pass_qc']}")
    print(f"SNR: {results['qc_metrics']['signal_to_noise']:.2f}")
    print(f"RMS: {results['statistics']['rms']:.2f}")
```

### Memory-Efficient Processing

```python
# Load only specific traces (useful for large files)
trace_subset = list(range(0, 100, 10))  # Every 10th trace
results = processor.process_file("large_file.sgy", load_subset=trace_subset)
```

### Quality Control Metrics

The pipeline provides comprehensive QC metrics:

- **Data Integrity**: Checks for missing samples
- **Dead Traces**: Identifies traces with no signal
- **Amplitude Range**: Validates data range
- **Signal-to-Noise**: Basic SNR estimation
- **Pass/Fail**: Overall QC assessment

## Data Format Support

### Supported SEG-Y Formats

- **Format 1**: IBM float (legacy)
- **Format 5**: IEEE float (recommended)

### Sample Data

The project includes sample SEG-Y files:

- `sample_2d_small.sgy` (72KB) - Quick tests
- `sample_2d_medium.sgy` (420KB) - Standard demo
- `sample_2d_hires.sgy` (408KB) - High-resolution analysis

## Pipeline Stages

### Stage 1: Metadata Loading
- File format validation
- Trace and sample counting
- Sample interval extraction

### Stage 2: Data Loading
- Memory-efficient loading
- Support for trace subsets
- Error recovery (strict → ignore_geometry)

### Stage 3: Quality Control
- Missing value detection
- Dead trace identification
- Amplitude validation
- SNR estimation

### Stage 4: Statistics
- Mean, std, min, max
- RMS amplitude
- Data shape confirmation

## Output Format

Results are saved as JSON with the following structure:

```json
{
  "timestamp": "ISO-8601 timestamp",
  "success": true/false,
  "errors": [],
  "metadata": {
    "filename": "string",
    "num_traces": int,
    "num_samples": int,
    "sample_interval_ms": float,
    "format": int
  },
  "qc_metrics": {
    "pass_qc": true/false,
    "missing_samples": int,
    "dead_traces": int,
    "amplitude_range": [min, max],
    "signal_to_noise": float
  },
  "statistics": {
    "mean": float,
    "std": float,
    "min": float,
    "max": float,
    "rms": float
  }
}
```

## Error Handling

The pipeline uses custom exceptions:

- `SegyPipelineError`: Raised for pipeline-specific errors
- Automatic fallback from strict to ignore_geometry mode
- Detailed error logging for debugging

## Performance Considerations

### Memory Usage
- Full file loading: O(n_traces × n_samples)
- Subset loading: O(n_subset × n_samples)
- Data type: float32 for balance of precision and memory

### Processing Speed
- Metadata only: < 1 second
- Full processing: ~1-5 seconds per 1000 traces
- QC checks: Minimal overhead (~10%)

## Future Enhancements

### Planned Features
1. **segyzak Integration**: Migrate to segyzak for enhanced SEG-Y operations
2. **xarray Support**: Labeled multidimensional arrays for better data handling
3. **Parallel Processing**: Dask integration for large datasets
4. **Advanced QC**: Frequency analysis, velocity checks
5. **Visualization Pipeline**: Automated plot generation

### Migration Path
- Current: segyio-based implementation
- Target: segyzak + xarray + dask
- Timeline: Based on project requirements

## Troubleshooting

### Common Issues

**Issue**: `FileNotFoundError`
- **Solution**: Check file path and ensure .sgy file exists

**Issue**: `SegyPipelineError: Failed to open SEG-Y file`
- **Solution**: File may be corrupted or in unsupported format

**Issue**: QC fails with high dead trace count
- **Solution**: Check data acquisition parameters, may indicate sensor issues

**Issue**: Low SNR (< 1.0)
- **Solution**: May indicate noisy data or acquisition problems

## Testing

```bash
# Run basic pipeline test
python3 scripts/seismic_pipeline.py

# Expected output: Success=True, QC Pass=True
```

## Contributing

When extending the pipeline:

1. Maintain type hints
2. Add comprehensive logging
3. Include QC metrics for new features
4. Update this documentation
5. Test with sample data files

## References

- [SEG-Y Rev 2 Specification](https://www.seg.org/)
- [segyio Documentation](https://segyio.readthedocs.io/)
- [segyzak Repository](https://github.com/statoil/segyzak)

---

**Maintained by**: Seismic Data Engineer
**Last Updated**: 2026-03-18
**Version**: 1.0.0