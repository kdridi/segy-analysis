#!/usr/bin/env python3
"""
SEG-Y Prospect Analyzer CLI Tool
Analyzes SEG-Y files for prospects (amplitude anomalies, structural traps).
Outputs JSON with coordinates, depth, and confidence scores.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
import numpy as np
import segyio
from scipy import ndimage
from scipy.signal import find_peaks, hilbert


class SegyProspectAnalyzer:
    """Analyzes SEG-Y data for seismic prospects."""

    def __init__(self, filepath: str):
        """
        Initialize the SEG-Y prospect analyzer.

        Parameters:
        -----------
        filepath : str
            Path to SEG-Y file
        """
        self.filepath = Path(filepath)
        self.data = None
        self.metadata = {}
        self.prospects = {
            'amplitude_anomalies': [],
            'structural_traps': [],
            'summary': {}
        }

    def load_segy(self) -> bool:
        """Load SEG-Y file and extract data."""
        try:
            print(f"Loading {self.filepath.name}...")

            with segyio.open(self.filepath, 'r', strict=False) as f:
                # Extract metadata
                self.metadata = {
                    'n_traces': f.tracecount,
                    'n_samples': len(f.samples),
                    'sample_interval_us': f.bin[segyio.BinField.Interval],
                    'format': f.bin[segyio.BinField.Format],
                    'samples': list(f.samples),
                }

                # Load all traces
                self.data = np.stack([f.trace[i] for i in range(f.tracecount)])

                # Extract coordinate information from headers
                self.metadata['source_x'] = []
                self.metadata['source_y'] = []
                self.metadata['cdp_numbers'] = []

                for i in range(f.tracecount):
                    self.metadata['source_x'].append(
                        f.header[i][segyio.TraceField.SourceX]
                    )
                    self.metadata['source_y'].append(
                        f.header[i][segyio.TraceField.SourceY]
                    )
                    self.metadata['cdp_numbers'].append(
                        f.header[i][segyio.TraceField.CDP_TRACE]
                    )

            print(f"✓ Loaded: {self.data.shape} (traces × samples)")
            return True

        except Exception as e:
            print(f"✗ Error loading SEG-Y file: {e}")
            return False

    def detect_amplitude_anomalies(
        self,
        threshold_std: float = 2.5,
        min_cluster_size: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Detect amplitude anomalies in the seismic data.

        Parameters:
        -----------
        threshold_std : float
            Number of standard deviations for anomaly threshold
        min_cluster_size : int
            Minimum size of anomalous clusters to report

        Returns:
        --------
        List of detected anomalies with metadata
        """
        print("\nDetecting amplitude anomalies...")

        anomalies = []

        # Calculate statistics
        mean_amp = np.mean(self.data)
        std_amp = np.std(self.data)
        abs_data = np.abs(self.data)

        # Find anomalous values
        threshold = mean_amp + threshold_std * std_amp
        anomalous_mask = abs_data > threshold

        if not np.any(anomalous_mask):
            print("  No amplitude anomalies detected.")
            return anomalies

        # Find connected components (clusters)
        labeled_mask, num_clusters = ndimage.label(anomalous_mask)

        # Sample interval in seconds
        dt = self.metadata['sample_interval_us'] / 1e6

        # Process each cluster
        for cluster_id in range(1, num_clusters + 1):
            cluster_mask = labeled_mask == cluster_id

            # Skip small clusters
            if np.sum(cluster_mask) < min_cluster_size:
                continue

            # Get cluster properties
            cluster_indices = np.where(cluster_mask)
            trace_indices = cluster_indices[0]
            sample_indices = cluster_indices[1]

            # Calculate cluster statistics
            center_trace = int(np.mean(trace_indices))
            center_sample = int(np.mean(sample_indices))

            # Get coordinates from headers
            x_coord = self.metadata['source_x'][center_trace]
            y_coord = self.metadata['source_y'][center_trace]
            depth_time = center_sample * dt

            # Calculate confidence based on deviation from threshold
            max_deviation = np.max(abs_data[cluster_mask]) - threshold
            confidence = min(1.0, max_deviation / (2 * std_amp))

            anomalies.append({
                'id': f'AA-{len(anomalies) + 1:03d}',
                'type': 'amplitude_anomaly',
                'coordinates': {
                    'x': float(x_coord),
                    'y': float(y_coord),
                    'trace': int(center_trace),
                    'sample': int(center_sample)
                },
                'depth': {
                    'time_s': float(depth_time),
                    'sample_index': int(center_sample)
                },
                'amplitude': {
                    'value': float(self.data[center_trace, center_sample]),
                    'deviation_std': float(
                        (abs_data[center_trace, center_sample] - mean_amp) / std_amp
                    )
                },
                'cluster_size': int(np.sum(cluster_mask)),
                'confidence': float(confidence),
                'description': self._describe_amplitude_anomaly(
                    confidence, depth_time, np.sum(cluster_mask)
                )
            })

        print(f"  ✓ Found {len(anomalies)} amplitude anomalies")
        return anomalies

    def detect_structural_traps(
        self,
        prominence_threshold: float = 0.3,
        distance_min: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Detect structural traps based on amplitude patterns and time shifts.

        Parameters:
        -----------
        prominence_threshold : float
            Minimum prominence for peak detection (normalized)
        distance_min : int
            Minimum distance between peaks in samples

        Returns:
        --------
        List of detected structural traps with metadata
        """
        print("\nDetecting structural traps...")

        traps = []
        dt = self.metadata['sample_interval_us'] / 1e6

        # Method 1: Envelope analysis for bright spots
        envelope = self._calculate_envelope()

        # Method 2: Look for coherent patterns across traces
        for trace_idx in range(0, self.metadata['n_traces'], 5):  # Sample every 5 traces
            trace_data = self.data[trace_idx, :]

            # Normalize trace
            if np.std(trace_data) > 0:
                normalized_trace = (trace_data - np.mean(trace_data)) / np.std(trace_data)
            else:
                continue

            # Find peaks
            peaks, properties = find_peaks(
                np.abs(normalized_trace),
                prominence=prominence_threshold,
                distance=distance_min
            )

            # Get prominence for each peak
            prominences = properties.get('prominences', np.ones(len(peaks)) * 0.5)

            for i, peak_idx in enumerate(peaks):
                # Calculate local coherence (check neighboring traces)
                coherence_score = self._calculate_local_coherence(
                    trace_idx, peak_idx, window=5
                )

                # Only report if reasonably coherent
                if coherence_score > 0.3:
                    # Get coordinates
                    x_coord = self.metadata['source_x'][trace_idx]
                    y_coord = self.metadata['source_y'][trace_idx]
                    depth_time = peak_idx * dt

                    # Calculate confidence
                    prominence = prominences[i] if i < len(prominences) else 0.5
                    confidence = min(1.0, coherence_score * prominence)

                    traps.append({
                        'id': f'ST-{len(traps) + 1:03d}',
                        'type': 'structural_trap',
                        'coordinates': {
                            'x': float(x_coord),
                            'y': float(y_coord),
                            'trace': int(trace_idx),
                            'sample': int(peak_idx)
                        },
                        'depth': {
                            'time_s': float(depth_time),
                            'sample_index': int(peak_idx)
                        },
                        'amplitude': float(self.data[trace_idx, peak_idx]),
                        'coherence': float(coherence_score),
                        'confidence': float(confidence),
                        'description': self._describe_structural_trap(
                            confidence, depth_time, coherence_score
                        )
                    })

        # Remove duplicates based on proximity
        traps = self._remove_duplicate_prospects(traps, min_distance=10)

        print(f"  ✓ Found {len(traps)} potential structural traps")
        return traps

    def _calculate_envelope(self) -> np.ndarray:
        """Calculate the envelope (instantaneous amplitude) of seismic data."""
        # Using Hilbert transform approximation via analytic signal
        envelope = np.abs(hilbert(self.data, axis=1))
        return envelope

    def _calculate_local_coherence(
        self,
        trace_idx: int,
        sample_idx: int,
        window: int = 5
    ) -> float:
        """
        Calculate local coherence around a point.

        Parameters:
        -----------
        trace_idx : int
            Center trace index
        sample_idx : int
            Center sample index
        window : int
            Half-window size in traces

        Returns:
        --------
        Coherence score between 0 and 1
        """
        # Define window bounds
        trace_start = max(0, trace_idx - window)
        trace_end = min(self.metadata['n_traces'], trace_idx + window + 1)

        # Extract window data
        window_data = self.data[trace_start:trace_end, sample_idx]

        # Calculate coherence as normalized variance
        if len(window_data) < 2:
            return 0.0

        # Coherence: high if values are similar (low variance)
        mean_val = np.mean(window_data)
        if np.std(window_data) > 0:
            coherence = 1.0 / (1.0 + np.std(window_data) / (np.abs(mean_val) + 1e-10))
        else:
            coherence = 1.0

        return coherence

    def _remove_duplicate_prospects(
        self,
        prospects: List[Dict[str, Any]],
        min_distance: int = 10
    ) -> List[Dict[str, Any]]:
        """Remove duplicate prospects based on proximity."""
        if not prospects:
            return []

        # Sort by confidence (highest first)
        sorted_prospects = sorted(
            prospects,
            key=lambda x: x['confidence'],
            reverse=True
        )

        unique_prospects = []

        for prospect in sorted_prospects:
            is_duplicate = False

            for existing in unique_prospects:
                # Calculate distance
                trace_dist = abs(
                    prospect['coordinates']['trace'] -
                    existing['coordinates']['trace']
                )
                sample_dist = abs(
                    prospect['coordinates']['sample'] -
                    existing['coordinates']['sample']
                )

                if trace_dist < min_distance and sample_dist < min_distance:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_prospects.append(prospect)

        return unique_prospects

    def _describe_amplitude_anomaly(
        self,
        confidence: float,
        depth_time: float,
        cluster_size: int
    ) -> str:
        """Generate description for amplitude anomaly."""
        confidence_level = "high" if confidence > 0.7 else "moderate" if confidence > 0.4 else "low"

        return (
            f"Amplitude anomaly at {depth_time:.3f}s "
            f"with {confidence_level} confidence. "
            f"Cluster size: {cluster_size} samples."
        )

    def _describe_structural_trap(
        self,
        confidence: float,
        depth_time: float,
        coherence: float
    ) -> str:
        """Generate description for structural trap."""
        confidence_level = "high" if confidence > 0.7 else "moderate" if confidence > 0.4 else "low"

        return (
            f"Potential structural trap at {depth_time:.3f}s "
            f"with {confidence_level} confidence. "
            f"Coherence: {coherence:.2f}."
        )

    def analyze(
        self,
        anomaly_threshold: float = 2.5,
        trap_prominence: float = 0.3
    ) -> Dict[str, Any]:
        """
        Perform complete prospect analysis.

        Parameters:
        -----------
        anomaly_threshold : float
            Standard deviation threshold for amplitude anomalies
        trap_prominence : float
            Prominence threshold for structural trap detection

        Returns:
        --------
        Complete analysis results
        """
        if self.data is None:
            if not self.load_segy():
                return None

        # Detect prospects
        self.prospects['amplitude_anomalies'] = self.detect_amplitude_anomalies(
            threshold_std=anomaly_threshold
        )

        self.prospects['structural_traps'] = self.detect_structural_traps(
            prominence_threshold=trap_prominence
        )

        # Generate summary
        total_prospects = (
            len(self.prospects['amplitude_anomalies']) +
            len(self.prospects['structural_traps'])
        )

        high_confidence = sum(
            1 for p in (
                self.prospects['amplitude_anomalies'] +
                self.prospects['structural_traps']
            )
            if p['confidence'] > 0.7
        )

        self.prospects['summary'] = {
            'total_prospects': total_prospects,
            'amplitude_anomalies_count': len(self.prospects['amplitude_anomalies']),
            'structural_traps_count': len(self.prospects['structural_traps']),
            'high_confidence_count': high_confidence,
            'input_file': str(self.filepath),
            'data_shape': list(self.data.shape),
            'analysis_parameters': {
                'anomaly_threshold_std': anomaly_threshold,
                'trap_prominence_threshold': trap_prominence
            }
        }

        return self.prospects

    def export_json(self, output_file: str = None, pretty: bool = True) -> str:
        """
        Export analysis results to JSON.

        Parameters:
        -----------
        output_file : str, optional
            Output file path. If None, returns JSON string
        pretty : bool
            Whether to format JSON with indentation

        Returns:
        --------
        JSON string or output file path
        """
        if not self.prospects.get('summary'):
            print("No analysis results to export. Run analyze() first.")
            return None

        json_output = json.dumps(
            self.prospects,
            indent=2 if pretty else None,
            default=str  # Handle numpy types
        )

        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w') as f:
                f.write(json_output)

            print(f"\n✓ Results exported to: {output_path}")
            return str(output_path)

        return json_output


def main():
    """CLI entry point for SEG-Y prospect analyzer."""
    parser = argparse.ArgumentParser(
        description='Analyze SEG-Y files for seismic prospects',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic analysis
  python segy_prospect_analyzer.py data.sgy

  # Analyze with custom thresholds
  python segy_prospect_analyzer.py data.sgy --anomaly-threshold 3.0 --trap-prominence 0.4

  # Export to JSON file
  python segy_prospect_analyzer.py data.sgy --output results.json

  # Minimal output for scripting
  python segy_prospect_analyzer.py data.sgy --no-pretty --output - > results.json
        """
    )

    parser.add_argument(
        'input_file',
        type=str,
        help='Input SEG-Y file (.sgy or .segy)'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='Output JSON file (use "-" for stdout)'
    )

    parser.add_argument(
        '--anomaly-threshold',
        type=float,
        default=2.5,
        help='Standard deviation threshold for amplitude anomalies (default: 2.5)'
    )

    parser.add_argument(
        '--trap-prominence',
        type=float,
        default=0.3,
        help='Prominence threshold for structural traps (default: 0.3)'
    )

    parser.add_argument(
        '--no-pretty',
        action='store_true',
        help='Disable pretty JSON formatting'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    # Validate input file
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input_file}", file=sys.stderr)
        sys.exit(1)

    # Run analysis
    analyzer = SegyProspectAnalyzer(args.input_file)

    if not analyzer.load_segy():
        sys.exit(1)

    results = analyzer.analyze(
        anomaly_threshold=args.anomaly_threshold,
        trap_prominence=args.trap_prominence
    )

    if results is None:
        print("Error: Analysis failed", file=sys.stderr)
        sys.exit(1)

    # Output results
    if args.output == '-':
        # Output to stdout
        json_output = analyzer.export_json(pretty=not args.no_pretty)
        print(json_output)

    elif args.output:
        # Output to file
        analyzer.export_json(args.output, pretty=not args.no_pretty)

    else:
        # Default: print to stdout with file-based name
        default_output = input_path.stem + '_prospects.json'
        analyzer.export_json(default_output, pretty=not args.no_pretty)

    # Print summary
    if args.verbose:
        print("\n" + "="*60, file=sys.stderr)
        print("ANALYSIS SUMMARY", file=sys.stderr)
        print("="*60, file=sys.stderr)
        print(f"Total prospects found: {results['summary']['total_prospects']}", file=sys.stderr)
        print(f"  Amplitude anomalies: {results['summary']['amplitude_anomalies_count']}", file=sys.stderr)
        print(f"  Structural traps: {results['summary']['structural_traps_count']}", file=sys.stderr)
        print(f"  High confidence: {results['summary']['high_confidence_count']}", file=sys.stderr)


if __name__ == "__main__":
    main()