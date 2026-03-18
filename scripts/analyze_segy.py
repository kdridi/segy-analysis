#!/usr/bin/env python3
"""
SEG-Y Seismic Data Analysis for Resource Prospect Identification
Geoscience Analyst Agent
"""

import segyio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from scipy import ndimage
import json
from pathlib import Path

class SegyAnalyzer:
    def __init__(self, filepath):
        self.filepath = filepath
        self.segy = None
        self.data = None
        self.metadata = {}

    def load(self):
        """Load SEG-Y file and extract metadata"""
        print(f"Loading SEG-Y file: {self.filepath}")
        # Try 2D mode first, then 3D
        try:
            self.segy = segyio.open(self.filepath, "r", strict=False)
        except:
            self.segy = segyio.open(self.filepath, "r", ignore_geometry=True)

        # Extract metadata
        self.metadata = {
            'filename': Path(self.filepath).name,
            'num_traces': len(self.segy.trace),
            'num_samples': self.segy.bin[segyio.BinField.Samples],
            'sample_interval': self.segy.bin[segyio.BinField.Interval] / 1000.0,  # Convert to ms
            'format': self.segy.bin[segyio.BinField.Format],
        }

        # Get source-receiver geometry if available
        try:
            self.metadata['source_x'] = [self.segy.header[i][segyio.TraceField.SourceX] for i in range(len(self.segy.trace))]
            self.metadata['source_y'] = [self.segy.header[i][segyio.TraceField.SourceY] for i in range(len(self.segy.trace))]
            self.metadata['cdp_x'] = [self.segy.header[i][segyio.TraceField.CDP_X] for i in range(len(self.segy.trace))]
            self.metadata['cdp_y'] = [self.segy.header[i][segyio.TraceField.CDP_Y] for i in range(len(self.segy.trace))]
        except:
            print("Warning: Could not extract coordinate information")

        # Load data into memory
        self.data = np.zeros((len(self.segy.trace), self.metadata['num_samples']))
        for i, trace in enumerate(self.segy.trace):
            self.data[i, :] = trace

        print(f"Loaded {self.metadata['num_traces']} traces, {self.metadata['num_samples']} samples per trace")
        return self

    def get_statistics(self):
        """Calculate basic statistics"""
        if self.data is None:
            raise ValueError("Data not loaded. Call load() first.")

        stats = {
            'mean': float(np.mean(self.data)),
            'std': float(np.std(self.data)),
            'min': float(np.min(self.data)),
            'max': float(np.max(self.data)),
            'rms': float(np.sqrt(np.mean(self.data**2)))
        }
        return stats

    def detect_amplitude_anomalies(self, threshold_std=1.5):
        """Detect amplitude anomalies using statistical threshold"""
        if self.data is None:
            raise ValueError("Data not loaded. Call load() first.")

        # Calculate RMS amplitude along traces
        rms_amplitude = np.sqrt(np.mean(self.data**2, axis=1))

        # Calculate threshold
        mean_rms = np.mean(rms_amplitude)
        std_rms = np.std(rms_amplitude)
        threshold = mean_rms + threshold_std * std_rms

        # Find anomalies
        anomalies = np.where(rms_amplitude > threshold)[0]

        return {
            'rms_amplitude': rms_amplitude,
            'mean_rms': float(mean_rms),
            'std_rms': float(std_rms),
            'threshold': float(threshold),
            'anomaly_traces': anomalies.tolist(),
            'num_anomalies': len(anomalies)
        }

    def detect_structural_features(self):
        """Detect potential structural features using edge detection"""
        if self.data is None:
            raise ValueError("Data not loaded. Call load() first.")

        # Use Sobel edge detection to find reflector discontinuities
        edges_vertical = ndimage.sobel(self.data, axis=0)  # Detect features in trace direction
        edges_horizontal = ndimage.sobel(self.data, axis=1)  # Detect features in time direction

        # Combine edges
        edge_magnitude = np.sqrt(edges_vertical**2 + edges_horizontal**2)

        # Find high edge areas (potential faults or discontinuities)
        edge_threshold = np.percentile(edge_magnitude, 95)
        high_edges = edge_magnitude > edge_threshold

        return {
            'edge_magnitude': edge_magnitude,
            'edge_threshold': float(edge_threshold),
            'high_edge_percentage': float(np.sum(high_edges) / high_edges.size * 100)
        }

    def identify_prospects(self, num_prospects=3):
        """Identify potential resource prospects based on amplitude and structural analysis"""
        if self.data is None:
            raise ValueError("Data not loaded. Call load() first.")

        # Get amplitude anomalies
        amp_analysis = self.detect_amplitude_anomalies(threshold_std=2.0)

        # Get structural features
        struct_analysis = self.detect_structural_features()

        # Identify prospect locations
        prospects = []

        # Sort anomalies by amplitude strength
        anomaly_strengths = amp_analysis['rms_amplitude'][amp_analysis['anomaly_traces']]
        sorted_indices = np.argsort(anomaly_strengths)[::-1]

        # Create prospects from strongest anomalies
        for i, idx in enumerate(sorted_indices[:num_prospects]):
            trace_idx = amp_analysis['anomaly_traces'][idx]

            # Find time of maximum amplitude in this trace
            trace_data = self.data[trace_idx, :]
            max_amp_time = np.argmax(np.abs(trace_data))
            max_amp_depth = max_amp_time * self.metadata['sample_interval'] / 1000.0  # Convert to seconds

            # Calculate confidence score based on amplitude strength and structural context
            strength = anomaly_strengths[i]
            confidence = min(0.95, 0.5 + (strength - amp_analysis['mean_rms']) / (2 * amp_analysis['std_rms']))

            # Get coordinates if available
            coordinates = {}
            if 'cdp_x' in self.metadata and len(self.metadata['cdp_x']) > trace_idx:
                coordinates['cdp_x'] = float(self.metadata['cdp_x'][trace_idx])
                coordinates['cdp_y'] = float(self.metadata['cdp_y'][trace_idx])

            prospect = {
                'prospect_id': f'P-{i+1:02d}',
                'trace_number': int(trace_idx),
                'depth_twoseconds': float(max_amp_depth),
                'depth_meters': float(max_amp_depth * 1500),  # Approximate conversion (1500 m/s)
                'amplitude': float(strength),
                'confidence_score': float(confidence),
                'coordinates': coordinates if coordinates else None,
                'interpretation': self._interpret_prospect(strength, confidence)
            }

            prospects.append(prospect)

        return prospects, amp_analysis, struct_analysis

    def _interpret_prospect(self, amplitude, confidence):
        """Generate interpretation for a prospect"""
        if confidence > 0.7:
            return "High-confidence amplitude anomaly. Possible hydrocarbon indicator or significant impedance contrast. Recommended for further investigation."
        elif confidence > 0.5:
            return "Moderate-confidence amplitude anomaly. May indicate geological feature or resource potential. Requires additional analysis."
        else:
            return "Low-confidence anomaly. Could be processing artifact or geological noise. Verification recommended."

    def create_visualization(self, output_prefix):
        """Create visualization plots"""
        if self.data is None:
            raise ValueError("Data not loaded. Call load() first.")

        fig, axes = plt.subplots(2, 2, figsize=(15, 12))

        # Plot 1: Seismic section
        ax1 = axes[0, 0]
        extent = [0, self.metadata['num_traces'],
                  self.metadata['num_samples'] * self.metadata['sample_interval'] / 1000, 0]
        im1 = ax1.imshow(self.data.T, aspect='auto', cmap='seismic', extent=extent)
        ax1.set_xlabel('Trace Number')
        ax1.set_ylabel('Time (s)')
        ax1.set_title('Seismic Section')
        plt.colorbar(im1, ax=ax1, label='Amplitude')

        # Plot 2: Amplitude analysis
        ax2 = axes[0, 1]
        amp_analysis = self.detect_amplitude_anomalies()
        traces = np.arange(self.metadata['num_traces'])
        ax2.plot(traces, amp_analysis['rms_amplitude'], 'b-', label='RMS Amplitude')
        ax2.axhline(y=amp_analysis['threshold'], color='red', linestyle='--', label='Threshold')
        ax2.scatter(amp_analysis['anomaly_traces'],
                   amp_analysis['rms_amplitude'][amp_analysis['anomaly_traces']],
                   c='red', s=50, zorder=5, label='Anomalies')
        ax2.set_xlabel('Trace Number')
        ax2.set_ylabel('RMS Amplitude')
        ax2.set_title('Amplitude Anomaly Detection')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # Plot 3: Structural edge detection
        ax3 = axes[1, 0]
        struct_analysis = self.detect_structural_features()
        extent = [0, self.metadata['num_traces'],
                  self.metadata['num_samples'] * self.metadata['sample_interval'] / 1000, 0]
        im3 = ax3.imshow(struct_analysis['edge_magnitude'].T, aspect='auto',
                        cmap='hot', extent=extent)
        ax3.set_xlabel('Trace Number')
        ax3.set_ylabel('Time (s)')
        ax3.set_title('Structural Feature Detection (Edges)')
        plt.colorbar(im3, ax=ax3, label='Edge Magnitude')

        # Plot 4: Prospect locations
        ax4 = axes[1, 1]
        prospects, _, _ = self.identify_prospects(num_prospects=3)

        # Create a map view if coordinates available
        if prospects and prospects[0]['coordinates']:
            cdp_x = [p['coordinates']['cdp_x'] for p in prospects]
            cdp_y = [p['coordinates']['cdp_y'] for p in prospects]
            confidences = [p['confidence_score'] for p in prospects]

            scatter = ax4.scatter(cdp_x, cdp_y, c=confidences, s=200,
                                 cmap='YlOrRd', vmin=0, vmax=1, edgecolors='black')

            for i, prospect in enumerate(prospects):
                ax4.annotate(prospect['prospect_id'],
                           (cdp_x[i], cdp_y[i]),
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=10, fontweight='bold')

            ax4.set_xlabel('CDP X')
            ax4.set_ylabel('CDP Y')
            ax4.set_title('Prospect Locations Map')
            plt.colorbar(scatter, ax=ax4, label='Confidence Score')
        else:
            # Show trace-based view
            trace_nums = [p['trace_number'] for p in prospects]
            depths = [p['depth_twoseconds'] for p in prospects]
            confidences = [p['confidence_score'] for p in prospects]

            scatter = ax4.scatter(trace_nums, depths, c=confidences, s=200,
                                 cmap='YlOrRd', vmin=0, vmax=1, edgecolors='black')

            for i, prospect in enumerate(prospects):
                ax4.annotate(prospect['prospect_id'],
                           (trace_nums[i], depths[i]),
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=10, fontweight='bold')

            ax4.set_xlabel('Trace Number')
            ax4.set_ylabel('Time (s)')
            ax4.set_title('Prospect Locations (Section View)')
            plt.colorbar(scatter, ax=ax4, label='Confidence Score')

        plt.tight_layout()
        plt.savefig(f'{output_prefix}_analysis.png', dpi=150, bbox_inches='tight')
        print(f"Saved visualization: {output_prefix}_analysis.png")
        plt.close()

    def generate_report(self, output_file):
        """Generate analysis report"""
        if self.data is None:
            raise ValueError("Data not loaded. Call load() first.")

        prospects, amp_analysis, struct_analysis = self.identify_prospects(num_prospects=3)
        stats = self.get_statistics()

        report = {
            'metadata': self.metadata,
            'statistics': stats,
            'amplitude_analysis': {
                'mean_rms': amp_analysis['mean_rms'],
                'std_rms': amp_analysis['std_rms'],
                'num_anomalies': amp_analysis['num_anomalies']
            },
            'structural_analysis': {
                'edge_threshold': struct_analysis['edge_threshold'],
                'high_edge_percentage': struct_analysis['high_edge_percentage']
            },
            'prospects': prospects,
            'summary': {
                'total_prospects_identified': len(prospects),
                'high_confidence_prospects': sum(1 for p in prospects if p['confidence_score'] > 0.7),
                'moderate_confidence_prospects': sum(1 for p in prospects if 0.5 < p['confidence_score'] <= 0.7),
                'average_confidence': float(np.mean([p['confidence_score'] for p in prospects]))
            }
        }

        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"Saved report: {output_file}")
        return report


def main():
    """Main analysis workflow"""
    print("=" * 60)
    print("SEG-Y Seismic Analysis for Resource Prospect Identification")
    print("Geoscience Analyst Agent")
    print("=" * 60)

    # Use the medium-resolution sample file (likely more features)
    segy_file = "/Users/kdridi/Documents/ellis/data/segy-samples/sample_2d_medium.sgy"
    output_prefix = "/Users/kdridi/Documents/ellis/docs/seismic_analysis"
    report_file = f"{output_prefix}_report.json"

    # Initialize analyzer
    analyzer = SegyAnalyzer(segy_file)

    # Load data
    analyzer.load()

    # Generate statistics
    print("\n--- Data Statistics ---")
    stats = analyzer.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value:.4f}")

    # Identify prospects
    print("\n--- Identifying Prospects ---")
    prospects, amp_analysis, struct_analysis = analyzer.identify_prospects(num_prospects=3)

    print(f"\nFound {len(prospects)} potential resource prospects:")
    for prospect in prospects:
        print(f"\n{prospect['prospect_id']}:")
        print(f"  Trace Number: {prospect['trace_number']}")
        print(f"  Depth: {prospect['depth_meters']:.1f} meters (approximate)")
        print(f"  Confidence Score: {prospect['confidence_score']:.2f}")
        print(f"  Interpretation: {prospect['interpretation']}")
        if prospect['coordinates']:
            print(f"  Coordinates: X={prospect['coordinates']['cdp_x']:.0f}, Y={prospect['coordinates']['cdp_y']:.0f}")

    # Create visualizations
    print("\n--- Creating Visualizations ---")
    analyzer.create_visualization(output_prefix)

    # Generate report
    print("\n--- Generating Analysis Report ---")
    report = analyzer.generate_report(report_file)

    print("\n" + "=" * 60)
    print("Analysis Complete!")
    print(f"Prospects identified: {len(prospects)}")
    print(f"High confidence: {report['summary']['high_confidence_prospects']}")
    print(f"Average confidence: {report['summary']['average_confidence']:.2f}")
    print("=" * 60)

    return analyzer, prospects, report


if __name__ == "__main__":
    analyzer, prospects, report = main()
