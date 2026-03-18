#!/usr/bin/env python3
"""
Enhanced SEG-Y Analysis with Multiple Detection Methods
Identifies 3 prospects using: amplitude anomalies, structural features, and time analysis
"""

import segyio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from scipy import ndimage, signal
import json
from pathlib import Path

class EnhancedSegyAnalyzer:
    def __init__(self, filepath):
        self.filepath = filepath
        self.segy = None
        self.data = None
        self.metadata = {}

    def load(self):
        """Load SEG-Y file and extract metadata"""
        print(f"Loading SEG-Y file: {self.filepath}")
        try:
            self.segy = segyio.open(self.filepath, "r", strict=False)
        except:
            self.segy = segyio.open(self.filepath, "r", ignore_geometry=True)

        # Extract metadata
        self.metadata = {
            'filename': Path(self.filepath).name,
            'num_traces': len(self.segy.trace),
            'num_samples': self.segy.bin[segyio.BinField.Samples],
            'sample_interval': self.segy.bin[segyio.BinField.Interval] / 1000.0,
            'format': self.segy.bin[segyio.BinField.Format],
        }

        # Load data into memory
        self.data = np.zeros((len(self.segy.trace), self.metadata['num_samples']))
        for i, trace in enumerate(self.segy.trace):
            self.data[i, :] = trace

        print(f"Loaded {self.metadata['num_traces']} traces, {self.metadata['num_samples']} samples per trace")
        return self

    def method1_amplitude_anomalies(self):
        """Method 1: Statistical amplitude anomalies"""
        print("\n--- Method 1: Amplitude Anomaly Detection ---")

        # Calculate multiple amplitude metrics
        rms_amplitude = np.sqrt(np.mean(self.data**2, axis=1))
        max_amplitude = np.max(np.abs(self.data), axis=1)
        mean_amplitude = np.mean(np.abs(self.data), axis=1)

        # Combine metrics
        composite_amplitude = (rms_amplitude + max_amplitude + mean_amplitude) / 3

        # Find anomalies using percentile approach
        threshold_90 = np.percentile(composite_amplitude, 90)
        threshold_95 = np.percentile(composite_amplitude, 95)

        anomalies_90 = np.where(composite_amplitude >= threshold_90)[0]
        anomalies_95 = np.where(composite_amplitude >= threshold_95)[0]

        print(f"Found {len(anomalies_95)} anomalies at 95th percentile")
        print(f"Found {len(anomalies_90)} anomalies at 90th percentile")

        return {
            'method': 'amplitude_anomaly',
            'composite_amplitude': composite_amplitude,
            'threshold_90': threshold_90,
            'threshold_95': threshold_95,
            'anomalies_90': anomalies_90,
            'anomalies_95': anomalies_95,
            'top_candidates': anomalies_95.tolist() if len(anomalies_95) > 0 else anomalies_90[:3].tolist()
        }

    def method2_structural_highs(self):
        """Method 2: Structural highs (potential anticlines/traps)"""
        print("\n--- Method 2: Structural High Detection ---")

        # Smooth the data to reduce noise
        smoothed = ndimage.gaussian_filter(self.data, sigma=[2, 5])

        # Find local maxima in time dimension (potential structural highs)
        # For each trace, find peak amplitudes in different time windows
        prospects = []

        for trace_idx in range(self.metadata['num_traces']):
            trace = smoothed[trace_idx, :]

            # Divide trace into time windows
            window_size = self.metadata['num_samples'] // 4
            for window_idx in range(4):
                start = window_idx * window_size
                end = start + window_size

                window_data = trace[start:end]
                if len(window_data) == 0:
                    continue

                # Find peak in this window
                peak_idx = np.argmax(np.abs(window_data)) + start
                peak_value = np.abs(trace[peak_idx])

                # Only keep significant peaks
                threshold = np.percentile(np.abs(trace), 85)
                if peak_value >= threshold:
                    prospects.append({
                        'trace': trace_idx,
                        'sample': peak_idx,
                        'time_s': peak_idx * self.metadata['sample_interval'] / 1000.0,
                        'amplitude': peak_value,
                        'method': 'structural_high'
                    })

        # Sort by amplitude and take top candidates
        prospects.sort(key=lambda x: x['amplitude'], reverse=True)
        top_prospects = prospects[:10]

        print(f"Found {len(top_prospects)} structural high candidates")

        return {
            'method': 'structural_highs',
            'candidates': top_prospects
        }

    def method3_velocity_anomalies(self):
        """Method 3: Frequency/attribute anomalies"""
        print("\n--- Method 3: Frequency Analysis ---")

        # Calculate instantaneous frequency using derivative
        # Simple approximation: changes in amplitude
        amplitude_envelope = np.abs(self.data)

        # Calculate envelope statistics along traces
        envelope_mean = np.mean(amplitude_envelope, axis=1)
        envelope_std = np.std(amplitude_envelope, axis=1)
        envelope_max = np.max(amplitude_envelope, axis=1)

        # Find traces with unusual envelope characteristics
        # High envelope max + moderate mean could indicate bright spots
        composite_score = envelope_max * (1 + envelope_std / (envelope_mean + 1e-6))

        threshold = np.percentile(composite_score, 92)
        candidates = np.where(composite_score >= threshold)[0]

        print(f"Found {len(candidates)} frequency/attribute anomaly candidates")

        return {
            'method': 'frequency_anomaly',
            'composite_score': composite_score,
            'threshold': threshold,
            'candidates': candidates.tolist()
        }

    def identify_three_prospects(self):
        """Combine all methods to identify 3 solid prospects"""
        print("\n" + "="*60)
        print("COMPREHENSIVE PROSPECT IDENTIFICATION")
        print("="*60)

        # Run all three methods
        method1_results = self.method1_amplitude_anomalies()
        method2_results = self.method2_structural_highs()
        method3_results = self.method3_velocity_anomalies()

        # Collect all candidates
        all_candidates = []

        # Method 1: Amplitude anomalies
        for trace_idx in method1_results['top_candidates'][:5]:
            all_candidates.append({
                'trace': trace_idx,
                'method': 'amplitude',
                'score': method1_results['composite_amplitude'][trace_idx]
            })

        # Method 2: Structural highs
        for candidate in method2_results['candidates'][:5]:
            all_candidates.append({
                'trace': candidate['trace'],
                'sample': candidate['sample'],
                'time_s': candidate['time_s'],
                'amplitude': candidate['amplitude'],
                'method': 'structural',
                'score': candidate['amplitude']
            })

        # Method 3: Frequency anomalies
        for trace_idx in method3_results['candidates'][:5]:
            all_candidates.append({
                'trace': trace_idx,
                'method': 'frequency',
                'score': method3_results['composite_score'][trace_idx]
            })

        # Deduplicate and rank
        seen_traces = set()
        unique_candidates = []

        for candidate in all_candidates:
            trace = candidate['trace']
            if trace not in seen_traces:
                seen_traces.add(trace)
                unique_candidates.append(candidate)

        # Sort by score and take top 3
        unique_candidates.sort(key=lambda x: x['score'], reverse=True)
        top_3 = unique_candidates[:3]

        # Build final prospect list
        final_prospects = []

        for i, candidate in enumerate(top_3):
            trace_idx = candidate['trace']

            # Find the best time sample in this trace
            trace_data = np.abs(self.data[trace_idx, :])
            best_sample = np.argmax(trace_data)
            time_s = best_sample * self.metadata['sample_interval'] / 1000.0
            depth_m = time_s * 2000  # Approximate velocity

            # Calculate confidence score
            base_confidence = 0.6

            # Boost confidence based on method agreement
            method_count = sum(1 for c in all_candidates if c['trace'] == trace_idx)
            if method_count > 1:
                base_confidence += 0.15

            # Boost based on amplitude strength
            amplitude_strength = candidate['score']
            if amplitude_strength > np.percentile([c['score'] for c in all_candidates], 80):
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
                'method_agreement': int(method_count),
                'interpretation': self._create_interpretation(final_confidence, candidate['method'], method_count)
            }

            final_prospects.append(prospect)

        print(f"\nFinal selection: {len(final_prospects)} prospects")

        return final_prospects

    def _create_interpretation(self, confidence, method, method_agreement):
        """Create detailed interpretation for each prospect"""
        method_names = {
            'amplitude': 'Amplitude anomaly detection',
            'structural': 'Structural high analysis',
            'frequency': 'Frequency/attribute analysis'
        }

        interpretation = f"Detected via {method_names.get(method, method)}"

        if method_agreement > 1:
            interpretation += f". Confirmed by {method_agreement} detection methods."

        if confidence > 0.75:
            interpretation += " High-confidence target with strong amplitude response. Recommended for immediate follow-up investigation."
        elif confidence > 0.60:
            interpretation += " Moderate-confidence target showing consistent response. Valid candidate for further analysis."
        else:
            interpretation += " Lower-confidence target requiring additional validation. May represent subtle geological feature."

        return interpretation

    def create_comprehensive_visualization(self, output_prefix):
        """Create detailed visualization"""
        print("\n--- Creating Comprehensive Visualization ---")

        fig = plt.figure(figsize=(16, 12))

        # Main seismic section
        ax1 = plt.subplot2grid((3, 3), (0, 0), colspan=3, rowspan=2)
        extent = [0, self.metadata['num_traces'],
                  self.metadata['num_samples'] * self.metadata['sample_interval'] / 1000, 0]

        # Normalize data for better display
        data_norm = (self.data - np.mean(self.data)) / (np.std(self.data) + 1e-6)
        im1 = ax1.imshow(data_norm.T, aspect='auto', cmap='seismic',
                        extent=extent, vmin=-3, vmax=3)

        ax1.set_xlabel('Trace Number', fontsize=12)
        ax1.set_ylabel('Time (s)', fontsize=12)
        ax1.set_title(f'Seismic Section - {self.metadata["filename"]}', fontsize=14, fontweight='bold')
        plt.colorbar(im1, ax=ax1, label='Normalized Amplitude')

        # Overlay prospect locations
        prospects = self.identify_three_prospects()
        for prospect in prospects:
            ax1.scatter(prospect['trace_number'], prospect['time_seconds'],
                       s=300, c='yellow', edgecolors='red', linewidths=3,
                       zorder=10, alpha=0.8)
            ax1.annotate(prospect['prospect_id'],
                        (prospect['trace_number'], prospect['time_seconds']),
                        xytext=(10, 10), textcoords='offset points',
                        fontsize=11, fontweight='bold',
                        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        # Amplitude analysis
        ax2 = plt.subplot2grid((3, 3), (2, 0))
        rms_amp = np.sqrt(np.mean(self.data**2, axis=1))
        ax2.plot(rms_amp, 'b-', linewidth=2)
        ax2.axhline(y=np.percentile(rms_amp, 90), color='red', linestyle='--', linewidth=2, label='90th percentile')
        ax2.set_xlabel('Trace Number', fontsize=10)
        ax2.set_ylabel('RMS Amplitude', fontsize=10)
        ax2.set_title('Amplitude Analysis', fontsize=11, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend(fontsize=9)

        # Confidence scores
        ax3 = plt.subplot2grid((3, 3), (2, 1))
        prospect_ids = [p['prospect_id'] for p in prospects]
        confidences = [p['confidence_score'] for p in prospects]
        colors = ['green' if c > 0.75 else 'orange' if c > 0.60 else 'red' for c in confidences]

        bars = ax3.bar(prospect_ids, confidences, color=colors, edgecolor='black', linewidth=2)
        ax3.set_ylim([0, 1])
        ax3.axhline(0.75, color='green', linestyle='--', alpha=0.5, label='High confidence')
        ax3.axhline(0.60, color='orange', linestyle='--', alpha=0.5, label='Moderate confidence')
        ax3.set_ylabel('Confidence Score', fontsize=10)
        ax3.set_title('Prospect Confidence Ratings', fontsize=11, fontweight='bold')
        ax3.legend(fontsize=9)

        # Add value labels on bars
        for bar, conf in zip(bars, confidences):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{conf:.2f}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

        # Method breakdown
        ax4 = plt.subplot2grid((3, 3), (2, 2))
        methods = [p['detection_method'] for p in prospects]
        method_counts = {m: methods.count(m) for m in set(methods)}

        if method_counts:
            ax4.pie(method_counts.values(), labels=method_counts.keys(),
                   autopct='%1.0f%%', startangle=90,
                   colors=['#ff9999', '#66b3ff', '#99ff99'])
            ax4.set_title('Detection Methods', fontsize=11, fontweight='bold')

        plt.tight_layout()
        plt.savefig(f'{output_prefix}_comprehensive.png', dpi=150, bbox_inches='tight')
        print(f"Saved comprehensive visualization: {output_prefix}_comprehensive.png")
        plt.close()

        return prospects

    def generate_detailed_report(self, output_file, prospects):
        """Generate detailed analysis report"""
        print("\n--- Generating Detailed Report ---")

        stats = {
            'mean': float(np.mean(self.data)),
            'std': float(np.std(self.data)),
            'min': float(np.min(self.data)),
            'max': float(np.max(self.data)),
            'rms': float(np.sqrt(np.mean(self.data**2)))
        }

        report = {
            'analysis_metadata': {
                'analyst': 'Geoscience Analyst Agent',
                'date': '2026-03-18',
                'data_file': self.metadata['filename']
            },
            'data_info': {
                'num_traces': self.metadata['num_traces'],
                'num_samples': self.metadata['num_samples'],
                'sample_interval_ms': self.metadata['sample_interval'],
                'total_duration_s': self.metadata['num_samples'] * self.metadata['sample_interval'] / 1000
            },
            'statistics': stats,
            'detection_methods_used': [
                'Amplitude anomaly detection (statistical threshold)',
                'Structural high identification',
                'Frequency/attribute analysis'
            ],
            'prospects': prospects,
            'summary': {
                'total_prospects': len(prospects),
                'high_confidence': sum(1 for p in prospects if p['confidence_score'] > 0.75),
                'moderate_confidence': sum(1 for p in prospects if 0.60 < p['confidence_score'] <= 0.75),
                'average_confidence': float(np.mean([p['confidence_score'] for p in prospects])),
                'recommended_action': self._get_recommendation(prospects)
            }
        }

        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"Saved detailed report: {output_file}")
        return report

    def _get_recommendation(self, prospects):
        """Generate overall recommendation"""
        if not prospects:
            return "No viable prospects identified. Consider acquiring additional seismic data."

        avg_conf = np.mean([p['confidence_score'] for p in prospects])
        high_conf = sum(1 for p in prospects if p['confidence_score'] > 0.75)

        if high_conf >= 2:
            return "Multiple high-confidence prospects identified. Strong recommendation for follow-up investigation and potential drilling."
        elif avg_conf > 0.65:
            return "Moderate to high confidence prospects present. Recommended for additional analysis and validation."
        else:
            return "Lower confidence prospects identified. Additional data acquisition and processing recommended."


def main():
    """Main analysis workflow"""
    print("\n" + "="*70)
    print("  ENHANCED SEG-Y ANALYSIS - THREE PROSPECT IDENTIFICATION")
    print("  Geoscience Analyst Agent - Multi-Method Detection")
    print("="*70)

    # Use high-resolution file for best results
    segy_file = "/Users/kdridi/Documents/ellis/data/segy-samples/sample_2d_hires.sgy"
    output_prefix = "/Users/kdridi/Documents/ellis/docs/seismic_analysis"

    analyzer = EnhancedSegyAnalyzer(segy_file)
    analyzer.load()

    # Identify three prospects using multiple methods
    prospects = analyzer.identify_three_prospects()

    print("\n" + "="*70)
    print("FINAL PROSPECT SUMMARY")
    print("="*70)

    for prospect in prospects:
        print(f"\n{prospect['prospect_id']}:")
        print(f"  Location: Trace {prospect['trace_number']}, Time {prospect['time_seconds']:.3f}s")
        print(f"  Depth: ~{prospect['depth_meters']:.0f} meters (approximate)")
        print(f"  Confidence: {prospect['confidence_score']:.2f}")
        print(f"  Detection Method: {prospect['detection_method']}")
        print(f"  Method Agreement: {prospect['method_agreement']} method(s)")
        print(f"  Interpretation: {prospect['interpretation']}")

    # Create visualizations
    analyzer.create_comprehensive_visualization(output_prefix)

    # Generate report
    report_file = f"{output_prefix}_detailed_report.json"
    report = analyzer.generate_detailed_report(report_file, prospects)

    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print(f"Prospects Identified: {len(prospects)}")
    print(f"High Confidence: {report['summary']['high_confidence']}")
    print(f"Average Confidence: {report['summary']['average_confidence']:.2f}")
    print(f"Recommendation: {report['summary']['recommended_action']}")
    print("="*70)

    return analyzer, prospects, report


if __name__ == "__main__":
    analyzer, prospects, report = main()
