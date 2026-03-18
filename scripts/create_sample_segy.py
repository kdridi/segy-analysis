#!/usr/bin/env python3
"""
Create sample SEG-Y files for testing and development.
Uses obspy for more robust SEG-Y file creation.
"""

import numpy as np
from obspy import Stream, Trace, UTCDateTime
from obspy.core.trace import Stats
import os


def create_sample_segy_with_obspy(output_path, n_samples=1000, n_traces=50, sample_interval=0.002):
    """
    Create a synthetic SEG-Y file using ObsPy.

    Parameters:
    -----------
    output_path : str
        Path where the SEG-Y file will be saved
    n_samples : int
        Number of samples per trace
    n_traces : int
        Number of traces
    sample_interval : float
        Sample interval in seconds (default 0.002 = 2ms)
    """
    # Create a stream with multiple traces
    stream = Stream()

    for i in range(n_traces):
        # Create synthetic seismic data
        data = np.zeros(n_samples, dtype=np.float32)

        # Time axis
        t = np.arange(n_samples) * sample_interval
        offset = i * 50  # Offset in meters

        # Add synthetic hyperbolic event (simulating a reflection)
        t0 = 1.0  # Zero-offset time in seconds
        v = 2000  # Velocity in m/s
        t_hyperbola = np.sqrt(t0**2 + (offset / v)**2)

        # Create a wavelet around the hyperbolic time
        for j, time_val in enumerate(t):
            if abs(time_val - t_hyperbola) < 0.05:
                data[j] = np.exp(-100 * (time_val - t_hyperbola)**2)

        # Add random noise
        data += 0.05 * np.random.randn(n_samples)

        # Create trace with metadata
        trace = Trace(data=data)
        trace.stats.delta = sample_interval
        trace.stats.starttime = UTCDateTime(0)
        trace.stats.network = "XX"
        trace.stats.station = f"ST{i:03d}"
        trace.stats.channel = "HHZ"
        trace.stats.location = ""

        # Add custom seismic attributes
        trace.stats.segy = {
            'trace_header': {
                'trace_number': i + 1,
                'cdp_number': i + 1,
                'source_coordinate_x': i * 50,
                'source_coordinate_y': 0,
                'group_coordinate_x': i * 50 + 100,
                'group_coordinate_y': 0,
            }
        }

        stream += trace

    # Write to SEG-Y file
    stream.write(output_path, format="SEGY")

    print(f"Created SEG-Y file: {output_path}")
    print(f"  Traces: {n_traces}")
    print(f"  Samples: {n_samples}")
    print(f"  Sample interval: {sample_interval*1e6:.0f} µs")
    return output_path


def create_multiple_samples(output_dir):
    """Create multiple sample SEG-Y files with different characteristics."""
    os.makedirs(output_dir, exist_ok=True)

    # Sample 1: Small 2D line
    create_sample_segy_with_obspy(
        os.path.join(output_dir, "sample_2d_small.sgy"),
        n_samples=500,
        n_traces=30,
        sample_interval=0.002
    )

    # Sample 2: Medium 2D line
    create_sample_segy_with_obspy(
        os.path.join(output_dir, "sample_2d_medium.sgy"),
        n_samples=1000,
        n_traces=100,
        sample_interval=0.002
    )

    # Sample 3: High-resolution
    create_sample_segy_with_obspy(
        os.path.join(output_dir, "sample_2d_hires.sgy"),
        n_samples=2000,
        n_traces=50,
        sample_interval=0.001
    )

    print(f"\nAll sample files created in: {output_dir}")


if __name__ == "__main__":
    output_dir = "data/segy-samples"
    create_multiple_samples(output_dir)
