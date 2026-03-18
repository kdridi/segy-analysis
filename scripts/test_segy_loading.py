#!/usr/bin/env python3
"""
SEG-Y Data Loading Test
Demonstrates loading and basic processing of SEG-Y files using segyio and xarray.
"""

import numpy as np
import segyio
import xarray as xr
import os
from pathlib import Path


class SegyLoader:
    """SEG-Y file loader with xarray integration."""

    def __init__(self, filepath):
        """
        Initialize SEG-Y loader.

        Parameters:
        -----------
        filepath : str or Path
            Path to SEG-Y file
        """
        self.filepath = Path(filepath)
        self.data = None
        self.metadata = {}
        self.xr_dataset = None

    def load_with_segyio(self):
        """Load SEG-Y file using segyio."""
        print(f"\nLoading {self.filepath.name} with segyio...")

        # Open with strict geometry disabled for 2D lines
        with segyio.open(self.filepath, 'r', strict=False) as f:
            # Extract metadata
            self.metadata = {
                'n_traces': f.tracecount,
                'n_samples': len(f.samples),
                'sample_interval': f.bin[segyio.BinField.Interval],
                'format': f.bin[segyio.BinField.Format],
                'samples': list(f.samples),
            }

            print(f"  Traces: {self.metadata['n_traces']}")
            print(f"  Samples: {self.metadata['n_samples']}")
            print(f"  Sample interval: {self.metadata['sample_interval']} µs")
            print(f"  Format: {self.metadata['format']}")

            # Load all traces (shape: n_traces x n_samples)
            self.data = np.stack([f.trace[i] for i in range(f.tracecount)])

            # Extract header information
            self.metadata['headers'] = []
            for i in range(min(5, f.tracecount)):  # First 5 traces for demo
                header = {
                    'trace_number': i + 1,
                    'cdp': f.header[i][segyio.TraceField.CDP_TRACE],
                    'source_x': f.header[i][segyio.TraceField.SourceX],
                    'source_y': f.header[i][segyio.TraceField.SourceY],
                    'group_x': f.header[i][segyio.TraceField.GroupX],
                    'group_y': f.header[i][segyio.TraceField.GroupY],
                }
                self.metadata['headers'].append(header)

        print(f"  ✓ Data loaded successfully: {self.data.shape}")
        return self.data, self.metadata

    def to_xarray(self):
        """Convert loaded data to xarray Dataset."""
        if self.data is None:
            raise ValueError("No data loaded. Call load_with_segyio() first.")

        print(f"\nConverting to xarray Dataset...")

        # Create coordinates
        traces = np.arange(self.metadata['n_traces'])
        samples = np.arange(self.metadata['n_samples'])
        time_seconds = samples * self.metadata['sample_interval'] / 1e6

        # Create xarray Dataset with proper indexes
        self.xr_dataset = xr.Dataset(
            {
                'amplitude': (['trace', 'sample'], self.data),
            },
            coords={
                'trace': traces,
                'sample': samples,
            },
            attrs={
                'sample_interval_us': self.metadata['sample_interval'],
                'n_traces': self.metadata['n_traces'],
                'source_file': str(self.filepath),
            }
        )

        # Add time as a non-dimension coordinate (variable)
        self.xr_dataset.coords['time'] = ('sample', time_seconds)

        print(f"  ✓ xarray Dataset created")
        print(f"    Dimensions: {dict(self.xr_dataset.sizes)}")
        print(f"    Coordinates: {list(self.xr_dataset.coords.keys())}")

        return self.xr_dataset

    def print_statistics(self):
        """Print basic statistics about loaded data."""
        if self.data is None:
            print("No data loaded.")
            return

        print(f"\nStatistics for {self.filepath.name}:")
        print(f"  Shape: {self.data.shape}")
        print(f"  Min: {np.min(self.data):.6f}")
        print(f"  Max: {np.max(self.data):.6f}")
        print(f"  Mean: {np.mean(self.data):.6f}")
        print(f"  Std: {np.std(self.data):.6f}")

    def plot_section(self, output_path=None):
        """Plot seismic section (optional, requires matplotlib)."""
        try:
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(10, 6))

            # Plot using imshow
            extent = [
                0, self.metadata['n_traces'],
                self.metadata['n_samples'] * self.metadata['sample_interval'] / 1e6,
                0,
            ]
            im = ax.imshow(self.data.T, aspect='auto', extent=extent, cmap='seismic')

            ax.set_xlabel('Trace Number')
            ax.set_ylabel('Time (s)')
            ax.set_title(f'{self.filepath.name}')

            plt.colorbar(im, ax=ax, label='Amplitude')
            plt.tight_layout()

            if output_path:
                plt.savefig(output_path, dpi=150, bbox_inches='tight')
                print(f"  ✓ Plot saved to: {output_path}")
            else:
                plt.show()

        except ImportError:
            print("  Note: matplotlib not available for plotting")


def test_all_samples():
    """Test loading all sample SEG-Y files."""
    samples_dir = Path("data/segy-samples")

    if not samples_dir.exists():
        print(f"Error: Directory {samples_dir} not found")
        return

    segy_files = sorted(samples_dir.glob("*.sgy"))
    if not segy_files:
        print(f"No SEG-Y files found in {samples_dir}")
        return

    print(f"Found {len(segy_files)} SEG-Y file(s)")
    print("=" * 60)

    for filepath in segy_files:
        loader = SegyLoader(filepath)

        # Load with segyio
        data, metadata = loader.load_with_segyio()

        # Convert to xarray
        xr_dataset = loader.to_xarray()

        # Print statistics
        loader.print_statistics()

        # Perform xarray operations demo
        print(f"\nxarray operations demo:")
        print(f"  Mean amplitude per trace: {xr_dataset['amplitude'].mean(dim='sample').values[:3]}...")
        print(f"  Sample slice at index 500 (1.0s):")
        sample_idx = int(1.0 / (metadata['sample_interval'] / 1e6))
        if sample_idx < metadata['n_samples']:
            sample_slice = xr_dataset['amplitude'].isel(sample=sample_idx)
            print(f"    Shape: {sample_slice.shape}")
            print(f"    Values: {sample_slice.values[:3]}...")

        print("\n" + "=" * 60)


def test_single_file(filepath):
    """Test a single SEG-Y file."""
    loader = SegyLoader(filepath)
    loader.load_with_segyio()
    loader.to_xarray()
    loader.print_statistics()


if __name__ == "__main__":
    # Test all sample files
    test_all_samples()

    # Optionally test a specific file
    # test_single_file("data/segy-samples/sample_2d_medium.sgy")
