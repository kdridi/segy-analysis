#!/usr/bin/env python3
"""
Enhanced SEG-Y Data Processing Pipeline
Seismic Data Engineer - Robust, memory-efficient processing with QC
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import segyio
from dataclasses import dataclass
import json
from datetime import datetime

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SegyMetadata:
    """SEG-Y file metadata container"""
    filename: str
    num_traces: int
    num_samples: int
    sample_interval: float  # milliseconds
    format: int
    data_type: str


@dataclass
class QualityMetrics:
    """Quality control metrics for SEG-Y data"""
    data_integrity: bool
    missing_samples: int
    dead_traces: int
    amplitude_range: Tuple[float, float]
    signal_to_noise: Optional[float] = None
    pass_qc: bool = True


class SegyPipelineError(Exception):
    """Custom exception for SEG-Y pipeline errors"""
    pass


class SegyDataLoader:
    """
    Robust SEG-Y data loader with error handling and QC checks
    """

    def __init__(self, filepath: Union[str, Path]):
        self.filepath = Path(filepath)
        if not self.filepath.exists():
            raise FileNotFoundError(f"SEG-Y file not found: {filepath}")

        self.segy = None
        self.metadata = None
        self.data = None

    def load_metadata_only(self) -> SegyMetadata:
        """Load only metadata (memory efficient for large files)"""
        logger.info(f"Loading metadata from: {self.filepath.name}")

        try:
            self.segy = segyio.open(str(self.filepath), "r", strict=False)
        except Exception as e:
            logger.warning(f"Strict mode failed, trying ignore_geometry: {e}")
            try:
                self.segy = segyio.open(str(self.filepath), "r", ignore_geometry=True)
            except Exception as e2:
                raise SegyPipelineError(f"Failed to open SEG-Y file: {e2}")

        metadata = SegyMetadata(
            filename=self.filepath.name,
            num_traces=len(self.segy.trace),
            num_samples=self.segy.bin[segyio.BinField.Samples],
            sample_interval=self.segy.bin[segyio.BinField.Interval] / 1000.0,
            format=self.segy.bin[segyio.BinField.Format],
            data_type="IEEE_FLOAT" if self.segy.bin[segyio.BinField.Format] == 5 else "UNKNOWN"
        )

        logger.info(f"Loaded metadata: {metadata.num_traces} traces, {metadata.num_samples} samples")
        return metadata

    def load_data(self, trace_indices: Optional[List[int]] = None) -> np.ndarray:
        """
        Load trace data with memory-efficient option for subset

        Args:
            trace_indices: Optional list of trace indices to load (for large files)

        Returns:
            numpy array of trace data
        """
        if self.segy is None:
            self.load_metadata_only()

        if trace_indices is None:
            # Load all traces
            logger.info("Loading all traces into memory")
            num_traces = len(self.segy.trace)
            num_samples = self.segy.bin[segyio.BinField.Samples]

            data = np.zeros((num_traces, num_samples), dtype=np.float32)
            for i, trace in enumerate(self.segy.trace):
                data[i, :] = trace
        else:
            # Load only specified traces
            logger.info(f"Loading {len(trace_indices)} traces")
            num_samples = self.segy.bin[segyio.BinField.Samples]
            data = np.zeros((len(trace_indices), num_samples), dtype=np.float32)

            for i, trace_idx in enumerate(trace_indices):
                if trace_idx < len(self.segy.trace):
                    data[i, :] = self.segy.trace[trace_idx]
                else:
                    logger.warning(f"Trace index {trace_idx} out of range")

        self.data = data
        logger.info(f"Loaded data shape: {data.shape}")
        return data

    def quality_control(self) -> QualityMetrics:
        """
        Perform quality control checks on loaded data

        Returns:
            QualityMetrics object with QC results
        """
        if self.data is None:
            raise SegyPipelineError("No data loaded for QC check")

        logger.info("Performing quality control checks")

        # Check for missing values
        missing_samples = np.isnan(self.data).sum()
        dead_traces = np.where(np.all(self.data == 0, axis=1))[0].size

        # Amplitude statistics
        amplitude_min = float(np.min(self.data))
        amplitude_max = float(np.max(self.data))

        # Basic signal-to-noise estimation (very simple)
        signal_level = np.std(self.data)
        noise_level = np.std(np.diff(self.data, axis=1))
        snr = signal_level / (noise_level + 1e-10)

        metrics = QualityMetrics(
            data_integrity=(missing_samples == 0),
            missing_samples=int(missing_samples),
            dead_traces=int(dead_traces),
            amplitude_range=(amplitude_min, amplitude_max),
            signal_to_noise=float(snr),
            pass_qc=(missing_samples == 0 and dead_traces < 0.1 * self.data.shape[0])
        )

        logger.info(f"QC Results: Pass={metrics.pass_qc}, Missing={missing_samples}, Dead={dead_traces}, SNR={snr:.2f}")

        return metrics

    def close(self):
        """Close SEG-Y file handle"""
        if self.segy is not None:
            self.segy.close()
            logger.info("SEG-Y file closed")


class SeismicProcessor:
    """
    High-level seismic data processing pipeline
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.loader = None
        self.metadata = None
        self.qc_metrics = None

    def process_file(self, filepath: Union[str, Path],
                    load_subset: Optional[List[int]] = None) -> Dict:
        """
        Process SEG-Y file with full pipeline

        Args:
            filepath: Path to SEG-Y file
            load_subset: Optional trace indices for subset loading

        Returns:
            Dictionary with processing results
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'errors': []
        }

        try:
            # Step 1: Load metadata
            logger.info("=== Step 1: Loading Metadata ===")
            self.loader = SegyDataLoader(filepath)
            self.metadata = self.loader.load_metadata_only()
            results['metadata'] = {
                'filename': self.metadata.filename,
                'num_traces': self.metadata.num_traces,
                'num_samples': self.metadata.num_samples,
                'sample_interval_ms': self.metadata.sample_interval,
                'format': self.metadata.format
            }

            # Step 2: Load data
            logger.info("=== Step 2: Loading Data ===")
            data = self.loader.load_data(trace_indices=load_subset)
            results['data_shape'] = data.shape

            # Step 3: Quality control
            logger.info("=== Step 3: Quality Control ===")
            self.qc_metrics = self.loader.quality_control()
            results['qc_metrics'] = {
                'pass_qc': self.qc_metrics.pass_qc,
                'missing_samples': self.qc_metrics.missing_samples,
                'dead_traces': self.qc_metrics.dead_traces,
                'amplitude_range': self.qc_metrics.amplitude_range,
                'signal_to_noise': self.qc_metrics.signal_to_noise
            }

            if not self.qc_metrics.pass_qc:
                raise SegyPipelineError("Quality control checks failed")

            # Step 4: Basic statistics
            logger.info("=== Step 4: Computing Statistics ===")
            stats = {
                'mean': float(np.mean(data)),
                'std': float(np.std(data)),
                'min': float(np.min(data)),
                'max': float(np.max(data)),
                'rms': float(np.sqrt(np.mean(data**2)))
            }
            results['statistics'] = stats

            results['success'] = True

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            results['errors'].append(str(e))
            results['success'] = False

        finally:
            # Cleanup
            if self.loader:
                self.loader.close()

        return results

    def save_results(self, results: Dict, output_file: Union[str, Path]):
        """Save processing results to JSON file"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Results saved to: {output_path}")


def main():
    """Example usage of the seismic processing pipeline"""
    import sys

    # Setup
    segy_file = "data/segy-samples/sample_2d_hires.sgy"
    output_file = "docs/seismic_pipeline_results.json"

    logger.info("=" * 60)
    logger.info("SEISMIC DATA PROCESSING PIPELINE")
    logger.info("=" * 60)

    # Create processor
    processor = SeismicProcessor()

    # Process file
    results = processor.process_file(segy_file)

    # Save results
    processor.save_results(results, output_file)

    # Print summary
    print("\n" + "=" * 60)
    print("PIPELINE SUMMARY")
    print("=" * 60)
    print(f"Success: {results['success']}")
    if results['success']:
        print(f"Traces: {results['metadata']['num_traces']}")
        print(f"Samples: {results['metadata']['num_samples']}")
        print(f"QC Pass: {results['qc_metrics']['pass_qc']}")
        print(f"SNR: {results['qc_metrics']['signal_to_noise']:.2f}")
        print(f"RMS Amplitude: {results['statistics']['rms']:.2f}")
    else:
        print("Errors:")
        for error in results['errors']:
            print(f"  - {error}")
    print("=" * 60)

    return 0 if results['success'] else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())