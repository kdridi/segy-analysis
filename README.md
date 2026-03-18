# SEG-Y Analysis Tools

Professional browser-based tools for SEG-Y seismic data visualization and processing.

## 🌐 Live Demo

Visit our landing page at: [https://kdridi.github.io/segy-analysis](https://kdridi.github.io/segy-analysis)

## ✨ Features

- **Web Viewer**: Interactive SEG-Y visualization in your browser
- **No Installation**: Works directly in modern web browsers
- **Real-time Processing**: Adjust gain, clipping, and color maps interactively
- **Multiple Display Modes**: Wiggle traces, variable area, and heatmap
- **Sample Data**: Generate synthetic seismic data for testing
- **Privacy First**: All processing happens locally in your browser

## 🚀 Quick Start

1. Visit the web viewer: Open `segy-viewer.html` in your browser
2. Click "Load Sample Data" to see a demo
3. Or upload your own .sgy/.segy files

## 📚 Documentation

**New to seismic analysis?** Start here:

- **📖 [Quick Start Guide](docs/QUICK_START.md)** - Get started in 5 minutes
- **📚 [User Guide](docs/USER_GUIDE.md)** - Comprehensive beginner-friendly guide
- **📊 [Understanding Results](docs/UNDERSTANDING_RESULTS.md)** - Interpret analysis reports

**For developers and researchers:**

- **🛠️ [CLI Tool Documentation](docs/CLI_TOOL_DOCUMENTATION.md)** - Python command-line tools
- **🔬 [Seismic Pipeline Guide](docs/SEISMIC_PIPELINE_GUIDE.md)** - Processing workflows
- **📖 [SEG-Y Processing Knowledge Base](docs/seg-y-processing-knowledge-base.md)** - Technical reference
- **🎯 [Seismic Interpretation Framework](docs/seismic-interpretation-framework.md)** - Analysis methods

## 📁 Files

- `index.html` - Landing page with information about SEG-Y tools
- `segy-viewer.html` - Interactive SEG-Y web viewer

## 🛠️ Technology

- Pure HTML5/Canvas for maximum compatibility
- No external dependencies or frameworks
- SEG-Y Rev 2 specification support
- IEEE floating point format
- EBCDIC and ASCII header decoding

## 📚 Use Cases

- Oil & Gas Exploration
- Mineral Exploration
- Geothermal Energy
- Geotechnical Studies
- Research & Education

## 🤝 Contributing

We welcome contributions from developers, geophysicists, and researchers! Here's how you can help:

### For Developers

**Bug Reports:**
- Open an issue with a clear title and description
- Include steps to reproduce and expected behavior
- Add screenshots if relevant

**Feature Requests:**
- Open an issue describing the feature and use case
- Explain why it would be valuable

**Pull Requests:**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with clear commit messages
4. Test thoroughly (try all sample files!)
5. Submit a pull request with a description of changes

**Code Style:**
- Keep it simple and maintainable
- Add comments for complex logic
- Test across different browsers

### For Geophysicists & Researchers

We need your expertise! Help us by:
- Testing with real SEG-Y files from your projects
- Reporting format incompatibilities
- Suggesting geophysical features
- Improving documentation

### Sample Data

We include sample SEG-Y files for testing:
- `sample_2d_small.sgy` (72KB) - Quick tests
- `sample_2d_medium.sgy` (420KB) - Standard demo
- `sample_2d_hires.sgy` (408KB) - High-resolution

Feel free to contribute additional sample files with different characteristics!

## 📄 License

Open source and available for research and commercial use.

## 📧 Contact

For collaborations or inquiries about seismic interpretation services, please reach out.

---

**Note**: This is a browser-based tool. For advanced processing, check out our Python analysis scripts (available separately).
