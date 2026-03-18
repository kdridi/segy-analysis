#!/usr/bin/env python3
"""
Unit tests for Seismic Data Processing Pipeline
Run with: pytest scripts/test_seismic_pipeline.py -v
"""

import pytest
from pathlib import Path
import numpy as np
import json
from scripts.seismic_pipeline import (
    SegyDataLoader,
    SeismicProcessor,
    SegyMetadata,
    QualityMetrics,
    SegyPipelineError
)


class TestSegyDataLoader:
    """Test suite for SegyDataLoader class"""

    @pytest.fixture
    def sample_file(self):
        """Path to sample SEG-Y file"""
        return Path("data/segy-samples/sample_2d_small.sgy")

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing files"""
        with pytest.raises(FileNotFoundError):
            loader = SegyDataLoader("nonexistent_file.sgy")

    def test_load_metadata_only(self, sample_file):
        """Test metadata loading without reading full data"""
        loader = SegyDataLoader(sample_file)
        metadata = loader.load_metadata_only()

        assert isinstance(metadata, SegyMetadata)
        assert metadata.num_traces > 0
        assert metadata.num_samples > 0
        assert metadata.sample_interval > 0
        loader.close()

    def test_load_all_data(self, sample_file):
        """Test loading full dataset"""
        loader = SegyDataLoader(sample_file)
        metadata = loader.load_metadata_only()
        data = loader.load_data()

        assert data.shape[0] == metadata.num_traces
        assert data.shape[1] == metadata.num_samples
        assert data.dtype == np.float32
        loader.close()

    def test_load_trace_subset(self, sample_file):
        """Test loading subset of traces"""
        loader = SegyDataLoader(sample_file)
        metadata = loader.load_metadata_only()

        # Load only first 5 traces
        trace_indices = [0, 1, 2, 3, 4]
        data = loader.load_data(trace_indices=trace_indices)

        assert data.shape[0] == len(trace_indices)
        assert data.shape[1] == metadata.num_samples
        loader.close()

    def test_quality_control(self, sample_file):
        """Test QC metrics generation"""
        loader = SegyDataLoader(sample_file)
        loader.load_metadata_only()
        loader.load_data()

        qc = loader.quality_control()

        assert isinstance(qc, QualityMetrics)
        assert bool(qc.data_integrity) is True
        assert qc.missing_samples == 0
        assert isinstance(qc.signal_to_noise, float)
        loader.close()

    def test_qc_without_data(self, sample_file):
        """Test that QC fails if no data is loaded"""
        loader = SegyDataLoader(sample_file)
        loader.load_metadata_only()

        with pytest.raises(SegyPipelineError):
            loader.quality_control()
        loader.close()


class TestSeismicProcessor:
    """Test suite for SeismicProcessor class"""

    @pytest.fixture
    def sample_file(self):
        """Path to sample SEG-Y file"""
        return Path("data/segy-samples/sample_2d_small.sgy")

    @pytest.fixture
    def processor(self):
        """Create processor instance"""
        return SeismicProcessor()

    def test_process_file_success(self, processor, sample_file, tmp_path):
        """Test successful file processing"""
        results = processor.process_file(sample_file)

        assert results['success'] is True
        assert 'metadata' in results
        assert 'qc_metrics' in results
        assert 'statistics' in results
        assert len(results['errors']) == 0

    def test_qc_metrics_structure(self, processor, sample_file):
        """Test QC metrics structure"""
        results = processor.process_file(sample_file)

        qc = results['qc_metrics']
        assert 'pass_qc' in qc
        assert 'missing_samples' in qc
        assert 'dead_traces' in qc
        assert 'amplitude_range' in qc
        assert 'signal_to_noise' in qc

    def test_metadata_structure(self, processor, sample_file):
        """Test metadata structure"""
        results = processor.process_file(sample_file)

        metadata = results['metadata']
        assert 'filename' in metadata
        assert 'num_traces' in metadata
        assert 'num_samples' in metadata
        assert 'sample_interval_ms' in metadata
        assert metadata['num_traces'] > 0
        assert metadata['num_samples'] > 0

    def test_statistics_calculations(self, processor, sample_file):
        """Test statistical calculations"""
        results = processor.process_file(sample_file)

        stats = results['statistics']
        assert 'mean' in stats
        assert 'std' in stats
        assert 'min' in stats
        assert 'max' in stats
        assert 'rms' in stats

        # Verify RMS is a reasonable positive value
        assert isinstance(stats['rms'], float)
        assert stats['rms'] > 0
        assert stats['rms'] >= stats['std']  # RMS should be >= std for zero-mean data

    def test_save_results(self, processor, sample_file, tmp_path):
        """Test saving results to file"""
        results = processor.process_file(sample_file)

        output_file = tmp_path / "test_results.json"
        processor.save_results(results, output_file)

        assert output_file.exists()

        # Verify JSON structure
        with open(output_file, 'r') as f:
            loaded = json.load(f)

        assert loaded['success'] == results['success']
        assert 'metadata' in loaded


class TestPipelineIntegration:
    """Integration tests for complete pipeline"""

    def test_full_pipeline_workflow(self, tmp_path):
        """Test complete pipeline from file to saved results"""
        # Setup
        input_file = Path("data/segy-samples/sample_2d_small.sgy")
        output_file = tmp_path / "pipeline_results.json"

        # Process
        processor = SeismicProcessor()
        results = processor.process_file(input_file)
        processor.save_results(results, output_file)

        # Verify
        assert results['success'] is True
        assert output_file.exists()
        assert results['qc_metrics']['pass_qc'] is True

    def test_memory_efficient_processing(self, tmp_path):
        """Test memory-efficient subset processing"""
        input_file = Path("data/segy-samples/sample_2d_small.sgy")

        # Load only first 10 traces
        trace_subset = list(range(10))

        processor = SeismicProcessor()
        results = processor.process_file(input_file, load_subset=trace_subset)

        assert results['success'] is True
        assert results['data_shape'][0] == 10


def test_sample_files_exist():
    """Test that sample SEG-Y files are available"""
    sample_dir = Path("data/segy-samples")
    assert sample_dir.exists()

    sample_files = list(sample_dir.glob("*.sgy"))
    assert len(sample_files) >= 3


if __name__ == "__main__":
    # Run tests manually if pytest not available
    print("Running tests manually...")
    pytest.main([__file__, "-v"])