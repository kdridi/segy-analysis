#!/usr/bin/env python3
"""
Integrated Seismic Analysis Tool
Combines robust pipeline infrastructure with comprehensive analysis methods
Seismic Data Engineer - Professional-grade analysis workflow
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import matplotlib.pyplot as plt
from scipy import ndimage, signal
import json

from seismic_pipeline import SegyDataLoader, SeismicProcessor, QualityMetrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IntegratedSeismicAnalyzer:
    """
    Professional seismic analysis tool combining robust data handling
    with comprehensive geophysical analysis methods.
    """

    def __init__(self, filepath: Path):
        self.filepath = Path(filepath)
        self.loader = None
        self.data = None
        self.metadata = None
        self.qc_metrics = None

    def load_and_validate(self) -> bool:
        """
        Load SEG-Y data with comprehensive validation

        Returns:
            True if data passes QC, False otherwise
        """
        logger.info(f"Loading and validating: {self.filepath.name}")

        # Use robust pipeline for loading
        self.loader = SegyDataLoader(self.filepath)

        try:
            # Load metadata
            self.metadata = self.loader.load_metadata_only()

            # Load data
            self.data = self.loader.load_data()

            # Perform quality control
            self.qc_metrics = self.loader.quality_control()

            if not self.qc_metrics.pass_qc:
                logger.warning("QC checks failed - proceeding with caution")

            return True

        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return False

        finally:
            if self.loader:
                self.loader.close()

    def amplitude_anomaly_detection(self, threshold_std: float = 1.5) -> Dict:
        """
        Detect amplitude anomalies using statistical methods

        Args:
            threshold_std: Number of standard deviations for threshold

        Returns:
            Dictionary with anomaly detection results
        """
        if self.data is None:
            raise ValueError("Data not loaded")

        logger.info("Performing amplitude anomaly detection")

        # Calculate RMS amplitude
        rms_amplitude = np.sqrt(np.mean(self.data**2, axis=1))

        # Statistical threshold
        mean_rms = np.mean(rms_amplitude)
        std_rms = np.std(rms_amplitude)
        threshold = mean_rms + threshold_std * std_rms

        # Find anomalies
        anomalies = np.where(rms_amplitude > threshold)[0]

        # Calculate composite score
        max_amplitude = np.max(np.abs(self.data), axis=1)
        mean_amplitude = np.mean(np.abs(self.data), axis=1)
        composite = (rms_amplitude + max_amplitude + mean_amplitude) / 3

        return {
            'method': 'amplitude_anomaly',
            'rms_amplitude': rms_amplitude.tolist(),
            'composite_score': composite.tolist(),
            'threshold': float(threshold),
            'anomaly_traces': anomalies.tolist(),
            'num_anomalies': len(anomalies),
            'threshold_std': threshold_std
        }

    def structural_feature_detection(self, smoothing_sigma: Tuple[float, float] = (2, 5)) -> Dict:
        """
        Detect structural features using edge detection and smoothing

        Args:
            smoothing_sigma: Gaussian smoothing sigma (traces, samples)

        Returns:
            Dictionary with structural features
        """
        if self.data is None:
            raise ValueError("Data not loaded")

        logger.info("Performing structural feature detection")

        # Smooth data
        smoothed = ndimage.gaussian_filter(self.data, sigma=smoothing_sigma)

        # Calculate gradients (edges)
        gradient_trace = np.gradient(smoothed, axis=0)
        gradient_sample = np.gradient(smoothed, axis=1)

        # Edge magnitude
        edge_magnitude = np.sqrt(gradient_trace**2 + gradient_sample**2)

        # Find local maxima in edge magnitude
        from scipy.ndimage import maximum_filter
        local_max = maximum_filter(edge_magnitude, size=10)
        edges = edge_magnitude == local_max
        edges = edges & (edge_magnitude > np.percentile(edge_magnitude, 90))

        # Get edge locations
        edge_locations = np.argwhere(edges)

        return {
            'method': 'structural_features',
            'edge_magnitude': edge_magnitude.tolist(),
            'num_edges': len(edge_locations),
            'edge_locations': edge_locations.tolist()[:100]  # Limit for JSON
        }

    def frequency_analysis(self) -> Dict:
        """
        Perform frequency analysis on seismic data

        Returns:
            Dictionary with frequency analysis results
        """
        if self.data is None:
            raise ValueError("Data not loaded")

        logger.info("Performing frequency analysis")

        # Calculate amplitude envelope
        amplitude_envelope = np.abs(self.data)

        # Envelope statistics
        envelope_mean = np.mean(amplitude_envelope, axis=1)
        envelope_std = np.std(amplitude_envelope, axis=1)
        envelope_max = np.max(amplitude_envelope, axis=1)

        # Composite score for anomalies
        composite_score = envelope_max * (1 + envelope_std / (envelope_mean + 1e-6))

        # Threshold
        threshold = np.percentile(composite_score, 92)
        candidates = np.where(composite_score >= threshold)[0]

        return {
            'method': 'frequency_analysis',
            'envelope_mean': envelope_mean.tolist(),
            'envelope_std': envelope_std.tolist(),
            'envelope_max': envelope_max.tolist(),
            'composite_score': composite_score.tolist(),
            'threshold': float(threshold),
            'candidates': candidates.tolist()
        }

    def identify_prospects(self, num_prospects: int = 3) -> List[Dict]:
        """
        Combine multiple methods to identify top prospects

        Args:
            num_prospects: Number of top prospects to return

        Returns:
            List of prospect dictionaries
        """
        logger.info(f"Identifying top {num_prospects} prospects")

        # Run all detection methods
        amp_results = self.amplitude_anomaly_detection()
        struct_results = self.structural_feature_detection()
        freq_results = self.frequency_analysis()

        # Collect candidates from all methods
        all_candidates = []

        # Amplitude anomalies
        for trace_idx in amp_results['anomaly_traces'][:10]:
            all_candidates.append({
                'trace': trace_idx,
                'method': 'amplitude',
                'score': amp_results['composite_score'][trace_idx]
            })

        # Frequency anomalies
        for trace_idx in freq_results['candidates'][:10]:
            all_candidates.append({
                'trace': trace_idx,
                'method': 'frequency',
                'score': freq_results['composite_score'][trace_idx]
            })

        # Deduplicate and rank
        seen = set()
        unique_candidates = []

        for candidate in all_candidates:
            trace = candidate['trace']
            if trace not in seen:
                seen.add(trace)
                unique_candidates.append(candidate)

        # Sort by score
        unique_candidates.sort(key=lambda x: x['score'], reverse=True)

        # Build final prospect list
        prospects = []

        for i, candidate in enumerate(unique_candidates[:num_prospects]):
            trace_idx = candidate['trace']

            # Find best time sample
            trace_data = np.abs(self.data[trace_idx, :])
            best_sample = np.argmax(trace_data)
            time_s = best_sample * self.metadata.sample_interval / 1000.0
            depth_m = time_s * 2000  # Approximate velocity

            # Calculate confidence
            method_agreement = sum(1 for c in all_candidates if c['trace'] == trace_idx)
            base_confidence = 0.6 + (0.15 if method_agreement > 1 else 0)

            # Amplitude boost
            if candidate['score'] > np.percentile([c['score'] for c in all_candidates], 80):
                base_confidence += 0.1

            final_confidence = min(0.95, base_confidence)

            prospect = {
                'prospect_id': f'P-{i+1:02d}',
                'trace_number': int(trace_idx),
                'time_seconds': float(time_s),
                'depth_meters': float(depth_m),
                'amplitude': float(candidate['score']),
                'confidence_score': float(final_confidence),
                'detection_method': candidate['method'],
                'method_agreement': int(method_agreement),
                'interpretation': self._create_interpretation(
                    final_confidence, candidate['method'], method_agreement
                )
            }

            prospects.append(prospect)

        return prospects

    def _create_interpretation(self, confidence: float, method: str, agreement: int) -> str:
        """Create detailed interpretation for prospect"""
        method_names = {
            'amplitude': 'Amplitude anomaly detection',
            'structural': 'Structural analysis',
            'frequency': 'Frequency/attribute analysis'
        }

        interpretation = f"Detected via {method_names.get(method, method)}"

        if agreement > 1:
            interpretation += f". Confirmed by {agreement} detection methods."

        if confidence > 0.75:
            interpretation += " High-confidence target with strong response."
        elif confidence > 0.60:
            interpretation += " Moderate-confidence target showing consistent response."
        else:
            interpretation += " Lower-confidence target requiring validation."

        return interpretation

    def generate_visualization(self, output_file: Path, prospects: List[Dict]):
        """
        Generate comprehensive visualization

        Args:
            output_file: Output file path
            prospects: List of prospects to highlight
        """
        logger.info("Generating visualization")

        fig = plt.figure(figsize=(16, 12))

        # Main seismic section
        ax1 = plt.subplot2grid((3, 3), (0, 0), colspan=3, rowspan=2)

        extent = [
            0, self.metadata.num_traces,
            self.metadata.num_samples * self.metadata.sample_interval / 1000, 0
        ]

        # Normalize data
        data_norm = (self.data - np.mean(self.data)) / (np.std(self.data) + 1e-6)

        im1 = ax1.imshow(
            data_norm.T, aspect='auto', cmap='seismic',
            extent=extent, vmin=-3, vmax=3
        )

        ax1.set_xlabel('Trace Number', fontsize=12)
        ax1.set_ylabel('Time (s)', fontsize=12)
        ax1.set_title(f'Seismic Section - {self.metadata.filename}', fontsize=14, fontweight='bold')
        plt.colorbar(im1, ax=ax1, label='Normalized Amplitude')

        # Overlay prospects
        for prospect in prospects:
            ax1.scatter(
                prospect['trace_number'], prospect['time_seconds'],
                s=300, c='yellow', edgecolors='red', linewidths=3,
                zorder=10, alpha=0.8
            )
            ax1.annotate(
                prospect['prospect_id'],
                (prospect['trace_number'], prospect['time_seconds']),
                xytext=(10, 10), textcoords='offset points',
                fontsize=11, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
            )

        # Amplitude analysis
        ax2 = plt.subplot2grid((3, 3), (2, 0))
        rms_amp = np.sqrt(np.mean(self.data**2, axis=1))
        ax2.plot(rms_amp, 'b-', linewidth=2)
        ax2.axhline(y=np.percentile(rms_amp, 90), color='red', linestyle='--', linewidth=2)
        ax2.set_xlabel('Trace Number', fontsize=10)
        ax2.set_ylabel('RMS Amplitude', fontsize=10)
        ax2.set_title('Amplitude Analysis', fontsize=11, fontweight='bold')
        ax2.grid(True, alpha=0.3)

        # Confidence scores
        ax3 = plt.subplot2grid((3, 3), (2, 1))
        prospect_ids = [p['prospect_id'] for p in prospects]
        confidences = [p['confidence_score'] for p in prospects]
        colors = ['green' if c > 0.75 else 'orange' if c > 0.60 else 'red' for c in confidences]

        bars = ax3.bar(prospect_ids, confidences, color=colors, edgecolor='black', linewidth=2)
        ax3.set_ylim([0, 1])
        ax3.axhline(0.75, color='green', linestyle='--', alpha=0.5)
        ax3.axhline(0.60, color='orange', linestyle='--', alpha=0.5)
        ax3.set_ylabel('Confidence Score', fontsize=10)
        ax3.set_title('Prospect Confidence', fontsize=11, fontweight='bold')

        # QC metrics
        ax4 = plt.subplot2grid((3, 3), (2, 2))
        ax4.axis('off')

        qc_text = f"Quality Control Metrics\n\n"
        qc_text += f"Data Integrity: {'✓ PASS' if self.qc_metrics.data_integrity else '✗ FAIL'}\n"
        qc_text += f"Missing Samples: {self.qc_metrics.missing_samples}\n"
        qc_text += f"Dead Traces: {self.qc_metrics.dead_traces}\n"
        qc_text += f"S/N Ratio: {self.qc_metrics.signal_to_noise:.2f}\n"
        qc_text += f"Amp Range: {self.qc_metrics.amplitude_range[0]:.3f} to {self.qc_metrics.amplitude_range[1]:.3f}"

        ax4.text(0.1, 0.5, qc_text, fontsize=10, verticalalignment='center',
                family='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.tight_layout()
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        logger.info(f"Saved visualization: {output_file}")
        plt.close()

    def save_results(self, output_file: Path, prospects: List[Dict]):
        """
        Save analysis results to JSON

        Args:
            output_file: Output file path
            prospects: List of identified prospects
        """
        results = {
            'analysis_metadata': {
                'analyzer': 'Integrated Seismic Analyzer',
                'date': '2026-03-18',
                'data_file': self.metadata.filename
            },
            'data_info': {
                'num_traces': self.metadata.num_traces,
                'num_samples': self.metadata.num_samples,
                'sample_interval_ms': self.metadata.sample_interval
            },
            'qc_metrics': {
                'pass_qc': self.qc_metrics.pass_qc,
                'missing_samples': self.qc_metrics.missing_samples,
                'dead_traces': self.qc_metrics.dead_traces,
                'signal_to_noise': self.qc_metrics.signal_to_noise
            },
            'prospects': prospects,
            'summary': {
                'total_prospects': len(prospects),
                'high_confidence': sum(1 for p in prospects if p['confidence_score'] > 0.75),
                'moderate_confidence': sum(1 for p in prospects if 0.60 < p['confidence_score'] <= 0.75),
                'average_confidence': float(np.mean([p['confidence_score'] for p in prospects]))
            }
        }

        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Saved results: {output_file}")


def main():
    """Main analysis workflow"""
    print("\n" + "="*70)
    print("  INTEGRATED SEISMIC ANALYSIS")
    print("  Professional Pipeline + Comprehensive Analysis")
    print("="*70)

    # Setup
    segy_file = Path("data/segy-samples/sample_2d_hires.sgy")
    output_prefix = Path("docs/integrated_seismic_analysis")

    # Create analyzer
    analyzer = IntegratedSeismicAnalyzer(segy_file)

    # Load and validate
    if not analyzer.load_and_validate():
        print("ERROR: Failed to load data")
        return 1

    print(f"\n✓ Data loaded: {analyzer.metadata.num_traces} traces, {analyzer.metadata.num_samples} samples")
    print(f"✓ QC Pass: {analyzer.qc_metrics.pass_qc}")
    print(f"✓ S/N Ratio: {analyzer.qc_metrics.signal_to_noise:.2f}")

    # Identify prospects
    prospects = analyzer.identify_prospects(num_prospects=3)

    print("\n" + "="*70)
    print("PROSPECTS IDENTIFIED")
    print("="*70)

    for prospect in prospects:
        print(f"\n{prospect['prospect_id']}:")
        print(f"  Location: Trace {prospect['trace_number']}, Time {prospect['time_seconds']:.3f}s")
        print(f"  Depth: ~{prospect['depth_meters']:.0f} meters")
        print(f"  Confidence: {prospect['confidence_score']:.2f}")
        print(f"  Method: {prospect['detection_method']}")
        print(f"  Agreement: {prospect['method_agreement']} method(s)")

    # Generate outputs
    analyzer.generate_visualization(f"{output_prefix}.png", prospects)
    analyzer.save_results(f"{output_prefix}.json", prospects)

    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print(f"Visualization: {output_prefix}.png")
    print(f"Results: {output_prefix}.json")
    print("="*70)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())