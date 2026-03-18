#!/usr/bin/env python3
"""
Generate PDF Report for Non-Experts
Geoscience Analyst Agent
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import json
from pathlib import Path

class SeismicReportGenerator:
    def __init__(self, report_data_file, image_file, output_file):
        self.report_data_file = report_data_file
        self.image_file = image_file
        self.output_file = output_file

        # Load report data
        with open(report_data_file, 'r') as f:
            self.data = json.load(f)

        # Create PDF
        self.doc = SimpleDocTemplate(
            output_file,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Container for PDF elements
        self.elements = []

        # Styles
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""

        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=HexColor('#2E5090'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=HexColor('#2E5090'),
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold'
        ))

        # Body text style
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=11,
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        ))

        # Highlight box style
        self.styles.add(ParagraphStyle(
            name='HighlightBox',
            parent=self.styles['BodyText'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_LEFT,
            fontName='Helvetica',
            leftIndent=20,
            backColor=HexColor('#F0F4FF')
        ))

    def add_title_page(self):
        """Add title page"""

        # Main title
        title = Paragraph("Seismic Data Analysis Report", self.styles['CustomTitle'])
        self.elements.append(title)
        self.elements.append(Spacer(1, 0.3*inch))

        # Subtitle
        subtitle = Paragraph("Resource Prospect Identification", self.styles['Heading2'])
        self.elements.append(subtitle)
        self.elements.append(Spacer(1, 0.3*inch))

        # Report info
        info_data = [
            ['Prepared by:', 'Geoscience Analyst Agent'],
            ['Date:', 'March 18, 2026'],
            ['Data Source:', self.data['data_info']['num_traces']],
            ['Analysis Type:', 'Multi-Method Detection'],
        ]

        info_table = Table(info_data, colWidths=[2*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#2E5090')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))

        self.elements.append(info_table)
        self.elements.append(Spacer(1, 0.5*inch))

        # Executive summary box
        summary_text = f"""
        <b>EXECUTIVE SUMMARY</b><br/>
        <br/>
        This analysis identified <b>{len(self.data['prospects'])} potential resource prospects</b>
        in the seismic data. The prospects were detected using three independent methods:
        amplitude anomaly analysis, structural feature identification, and frequency analysis.
        <br/><br/>
        <b>Key Findings:</b><br/>
        • Total prospects identified: {len(self.data['prospects'])}<br/>
        • Average confidence score: {self.data['summary']['average_confidence']:.2f}<br/>
        • Recommended action: {self.data['summary']['recommended_action']}
        """

        summary = Paragraph(summary_text, self.styles['HighlightBox'])
        self.elements.append(summary)
        self.elements.append(PageBreak())

    def add_introduction(self):
        """Add introduction section"""

        title = Paragraph("1. Introduction", self.styles['CustomSubtitle'])
        self.elements.append(title)

        intro_text = """
        This report presents the results of a seismic data analysis conducted to identify
        potential resource prospects. Seismic exploration is a method used to investigate
        the Earth's subsurface geology and can help identify various resources including
        hydrocarbons, minerals, and groundwater.

        <b><i>What is Seismic Data?</i></b><br/>
        Seismic data is created by sending sound waves into the ground and measuring how
        they bounce back. Different rock types and resources reflect these waves differently,
        allowing us to create underground maps. Think of it like an ultrasound for the Earth!

        <b><i>Why This Matters:</i></b><br/>
        Understanding what lies beneath the surface is crucial for resource exploration.
        This analysis helps identify locations that warrant further investigation, potentially
        saving significant time and resources in exploration efforts.
        """

        intro = Paragraph(intro_text, self.styles['CustomBody'])
        self.elements.append(intro)
        self.elements.append(Spacer(1, 0.3*inch))

    def add_methodology(self):
        """Add methodology section"""

        title = Paragraph("2. How We Analyzed the Data", self.styles['CustomSubtitle'])
        self.elements.append(title)

        methods_text = """
        We used <b>three different methods</b> to find potential prospects, ensuring more
        reliable results:

        <b>Method 1: Amplitude Anomaly Detection</b><br/>
        This method looks for unusually strong or weak reflections in the seismic data.
        Think of it like finding a shiny object in a pile of rocks - the unusual
        reflection might indicate something different underground, like oil or gas.

        <b>Method 2: Structural Feature Identification</b><br/>
        This identifies shapes in the underground rock layers that could trap resources.
        Imagine underground domes or folds that could hold oil like a bowl holds water.

        <b>Method 3: Frequency Analysis</b><br/>
        This analyzes how the sound waves change as they travel through different materials.
        Different materials affect sound waves differently, helping us identify what might
        be underground.

        <b><i>Why Three Methods?</i></b><br/>
        Using multiple methods is like getting second and third opinions. When different
        methods agree on a location, we can be much more confident that it's worth
        investigating further.
        """

        methods = Paragraph(methods_text, self.styles['CustomBody'])
        self.elements.append(methods)
        self.elements.append(Spacer(1, 0.3*inch))

    def add_prospects(self):
        """Add detailed prospects section"""

        title = Paragraph("3. Identified Prospects", self.styles['CustomSubtitle'])
        self.elements.append(title)

        intro = Paragraph(
            "Below are the three most promising locations identified in this analysis:",
            self.styles['CustomBody']
        )
        self.elements.append(intro)
        self.elements.append(Spacer(1, 0.2*inch))

        for prospect in self.data['prospects']:
            # Prospect header
            prospect_title = Paragraph(
                f"<b>{prospect['prospect_id']}</b> - Confidence Score: {prospect['confidence_score']:.2f}/1.00",
                self.styles['Heading3']
            )
            self.elements.append(prospect_title)

            # Prospect details table
            details_data = [
                ['<b>Location</b>', f"Trace {prospect['trace_number']}, Time {prospect['time_seconds']:.3f} seconds"],
                ['<b>Approximate Depth</b>', f"{prospect['depth_meters']:.0f} meters below surface"],
                ['<b>Detection Method</b>', prospect['detection_method'].replace('_', ' ').title()],
                ['<b>Method Agreement</b>', f"{prospect['method_agreement']} method(s) confirmed this find"],
            ]

            details_table = Table(details_data, colWidths=[2.5*inch, 3.5*inch])
            details_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ]))

            self.elements.append(details_table)
            self.elements.append(Spacer(1, 0.1*inch))

            # Interpretation
            interpretation = Paragraph(
                f"<i>Interpretation:</i> {prospect['interpretation']}",
                ParagraphStyle(
                    'Interpretation',
                    parent=self.styles['CustomBody'],
                    leftIndent=20,
                    fontSize=10,
                    textColor=HexColor('#555555')
                )
            )
            self.elements.append(interpretation)
            self.elements.append(Spacer(1, 0.3*inch))

    def add_visualization(self):
        """Add visualization section"""

        title = Paragraph("4. Visual Analysis", self.styles['CustomSubtitle'])
        self.elements.append(title)

        viz_intro = Paragraph(
            "The following image shows the seismic data with identified prospects marked. "
            "The colored circles indicate the location and confidence level of each prospect.",
            self.styles['CustomBody']
        )
        self.elements.append(viz_intro)
        self.elements.append(Spacer(1, 0.2*inch))

        # Add image
        if Path(self.image_file).exists():
            img = Image(self.image_file, width=6*inch, height=4.5*inch)
            self.elements.append(img)
            self.elements.append(Spacer(1, 0.2*inch))

            caption = Paragraph(
                "<i>Figure 1: Seismic section with identified prospects highlighted.</i>",
                ParagraphStyle('Caption', parent=self.styles['CustomBody'], fontSize=9, alignment=TA_CENTER)
            )
            self.elements.append(caption)
        else:
            not_found = Paragraph(
                f"<i>Note: Visualization image not found at {self.image_file}</i>",
                self.styles['CustomBody']
            )
            self.elements.append(not_found)

        self.elements.append(Spacer(1, 0.3*inch))

    def add_recommendations(self):
        """Add recommendations section"""

        title = Paragraph("5. Recommendations", self.styles['CustomSubtitle'])
        self.elements.append(title)

        # Create recommendation based on confidence levels
        high_conf = self.data['summary']['high_confidence']
        mod_conf = self.data['summary']['moderate_confidence']
        avg_conf = self.data['summary']['average_confidence']

        if high_conf >= 2:
            rec_text = """
            <b>Strong Recommendation for Follow-Up:</b><br/><br/>
            The analysis identified multiple high-confidence prospects. We recommend:<br/>
            • Prioritize these locations for immediate investigation<br/>
            • Consider acquiring additional seismic data to refine targets<br/>
            • Evaluate feasibility of ground-truthing (physical investigation)<br/>
            • Assess economic viability of resource extraction
            """
        elif avg_conf > 0.65:
            rec_text = """
            <b>Moderate Recommendation:</b><br/><br/>
            The analysis identified several moderate-confidence prospects. We recommend:<br/>
            • Conduct additional analysis to increase confidence<br/>
            • Compare with existing geological data<br/>
            • Consider targeted data acquisition<br/>
            • Maintain these prospects in the exploration portfolio
            """
        else:
            rec_text = """
            <b>Cautious Recommendation:</b><br/><br/>
            The analysis identified lower-confidence prospects. We recommend:<br/>
            • Acquire additional seismic data to improve analysis<br/>
            • Refine processing parameters<br/>
            • Compare with regional geological context<br/>
            • Consider these locations as secondary targets
            """

        recommendations = Paragraph(rec_text, self.styles['CustomBody'])
        self.elements.append(recommendations)
        self.elements.append(Spacer(1, 0.3*inch))

    def add_glossary(self):
        """Add glossary section"""

        title = Paragraph("6. Glossary of Terms", self.styles['CustomSubtitle'])
        self.elements.append(title)

        glossary_terms = [
            ("<b>Amplitude</b>", "The strength of a seismic signal. Stronger or weaker amplitudes can indicate different underground materials."),
            ("<b>Confidence Score</b>", "A rating from 0 to 1 indicating how certain we are about a prospect. Higher scores mean greater certainty."),
            ("<b>Trace</b>", "A single measurement line in seismic data, like one pixel line in a photo."),
            ("<b>Depth</b>", "How far underground a feature is located, measured in meters or feet."),
            ("<b>Structural Feature</b>", "A shape or formation in underground rock layers that could trap resources."),
            ("<b>Frequency Analysis</b>", "Studying how fast sound waves vibrate to understand underground materials."),
            ("<b>Prospect</b>", "A location identified as potentially containing resources and worth investigating."),
        ]

        for term, definition in glossary_terms:
            term_paragraph = Paragraph(f"{term}: {definition}", self.styles['CustomBody'])
            self.elements.append(term_paragraph)
            self.elements.append(Spacer(1, 0.1*inch))

    def add_disclaimer(self):
        """Add disclaimer"""

        self.elements.append(PageBreak())

        disclaimer = Paragraph(
            "<b>Important Disclaimer</b><br/><br/>"
            "This report is based on seismic data analysis using automated methods. "
            "The identified prospects should be considered as preliminary findings only. "
            "Further investigation, including additional data acquisition and expert review, "
            "is recommended before making any exploration or investment decisions. "
            "The confidence scores provided are statistical estimates and do not guarantee "
            "the presence of resources.",
            ParagraphStyle(
                'Disclaimer',
                parent=self.styles['CustomBody'],
                fontSize=9,
                textColor=HexColor('#666666'),
                leftIndent=20,
                rightIndent=20
            )
        )
        self.elements.append(disclaimer)

    def generate(self):
        """Generate the complete PDF report"""

        # Add all sections
        self.add_title_page()
        self.add_introduction()
        self.add_methodology()
        self.add_prospects()
        self.add_visualization()
        self.add_recommendations()
        self.add_glossary()
        self.add_disclaimer()

        # Build PDF
        self.doc.build(self.elements)
        print(f"PDF report generated: {self.output_file}")

        return self.output_file


def main():
    """Main function to generate PDF report"""

    print("="*70)
    print("  Generating PDF Report for Non-Experts")
    print("="*70)

    # File paths
    report_data = "/Users/kdridi/Documents/ellis/docs/seismic_analysis_detailed_report.json"
    image_file = "/Users/kdridi/Documents/ellis/docs/seismic_analysis_comprehensive.png"
    output_file = "/Users/kdridi/Documents/ellis/docs/Seismic_Analysis_Report.pdf"

    # Generate report
    generator = SeismicReportGenerator(report_data, image_file, output_file)
    generator.generate()

    print("="*70)
    print("  PDF Report Generation Complete")
    print("="*70)
    print(f"Output file: {output_file}")
    print(f"File size: {Path(output_file).stat().st_size / 1024:.1f} KB")
    print("="*70)


if __name__ == "__main__":
    main()
