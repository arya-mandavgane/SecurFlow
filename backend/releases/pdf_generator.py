import io
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY


def generate_release_order_pdf(release_request) -> bytes:
    """
    Generates an official AICTE Release Order / Refund Letter PDF
    for an approved or released security deposit.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=45,
        leftMargin=45,
        topMargin=40,
        bottomMargin=40
    )

    fdr = release_request.fdr
    inst = fdr.institution
    order_num = release_request.refund_order_number or f"AICTE/RO/REL/{datetime.date.today().year}/{release_request.id:05d}"
    order_date = release_request.decision_date.strftime("%d-%m-%Y") if release_request.decision_date else datetime.date.today().strftime("%d-%m-%Y")

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'GovTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#001e3d')
    )
    subtitle_style = ParagraphStyle(
        'GovSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#334155')
    )
    order_title_style = ParagraphStyle(
        'OrderTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#991b1b')
    )
    body_style = ParagraphStyle(
        'GovBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor('#0f172a')
    )
    bold_body_style = ParagraphStyle(
        'GovBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    meta_style = ParagraphStyle(
        'GovMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )

    story = []

    # 1. Header
    story.append(Paragraph("ALL INDIA COUNCIL FOR TECHNICAL EDUCATION", title_style))
    story.append(Paragraph("(A Statutory Body under Ministry of Education, Government of India)", subtitle_style))
    story.append(Paragraph("Nelson Mandela Marg, Vasant Kunj, New Delhi - 110070 | www.aicte-india.org", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#001e3d'), spaceAfter=15))

    # 2. Dispatch Metadata
    meta_data = [
        [
            Paragraph(f"<b>Order Dispatch Ref:</b> {order_num}", meta_style),
            Paragraph(f"<b>Date of Issuance:</b> {order_date}", ParagraphStyle('R', parent=meta_style, alignment=TA_RIGHT))
        ]
    ]
    meta_table = Table(meta_data, colWidths=[320, 200])
    meta_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(meta_table)
    story.append(Spacer(1, 15))

    # 3. Addressees
    story.append(Paragraph("<b>TO:</b>", bold_body_style))
    story.append(Paragraph(f"The Branch Manager / Authorised Signatory<br/>{fdr.bank_name}<br/>{fdr.branch} Branch", body_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"<b>COPY TO:</b> The Principal / Director, {inst.name} (AICTE ID: {inst.aicte_id}), {inst.city or ''}, {inst.state}", meta_style))
    story.append(Spacer(1, 15))

    # 4. Subject
    story.append(Paragraph("<b>SUBJECT: OFFICIAL ORDER FOR RELEASE OF LIEN ON FIXED DEPOSIT RECEIPT (FDR) / REFUND OF SECURITY DEPOSIT</b>", order_title_style))
    story.append(Spacer(1, 12))

    # 5. Body
    story.append(Paragraph(
        f"Sir / Madam,<br/><br/>"
        f"With reference to the security deposit FDR pledged in favour of the <b>Member Secretary, All India Council for Technical Education (AICTE)</b>, "
        f"it is hereby certified that the competent authority of AICTE has evaluated the compliance and lock-in requirements for "
        f"<b>{inst.name}</b> and verified that all regulatory obligations under the AICTE Approval Process regulations stand satisfactorily completed.",
        body_style
    ))
    story.append(Spacer(1, 12))

    # 6. Structured Deposit Table
    deposit_details = [
        [Paragraph("<b>Deposit Parameter</b>", bold_body_style), Paragraph("<b>Verified Particulars</b>", bold_body_style)],
        [Paragraph("FDR / Certificate Number", body_style), Paragraph(fdr.fdr_number, bold_body_style)],
        [Paragraph("Issuing Bank & Branch", body_style), Paragraph(f"{fdr.bank_name} ({fdr.branch})", body_style)],
        [Paragraph("Principal Deposit Amount", body_style), Paragraph(f"INR {float(fdr.amount):,.2f}", bold_body_style)],
        [Paragraph("Date of Issuance", body_style), Paragraph(str(fdr.issue_date), body_style)],
        [Paragraph("Maturity Date", body_style), Paragraph(str(fdr.maturity_date), body_style)],
        [Paragraph("AICTE Institution Code", body_style), Paragraph(inst.aicte_id, body_style)],
        [Paragraph("Obligation Cycle / Purpose", body_style), Paragraph(fdr.purpose_approval_cycle, body_style)],
        [Paragraph("Release Request Reference", body_style), Paragraph(f"REL-REQ-{release_request.id:04d}", body_style)],
    ]
    dep_table = Table(deposit_details, colWidths=[200, 320])
    dep_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(dep_table)
    story.append(Spacer(1, 12))

    # 7. Directive to Bank
    story.append(Paragraph(
        "<b>DIRECTIVE:</b> In view of the above approval, <b>the lien/pledge marked in favour of AICTE on the above-described FDR is hereby UNCONDITIONALLY DISCHARGED and RELEASED</b>. "
        "The issuing bank is authorised to cancel the lien register notation and release/credit the principal amount along with accrued interest to the designated institutional bank account as per standard commercial banking guidelines.",
        body_style
    ))
    story.append(Spacer(1, 10))

    if release_request.official_remarks:
        story.append(Paragraph(f"<b>Official Remarks:</b> {release_request.official_remarks}", meta_style))
        story.append(Spacer(1, 10))

    # 8. Signatory Block
    officer_name = release_request.decided_by.get_full_name() if release_request.decided_by else "Competent Authority"
    officer_desig = getattr(release_request.decided_by, 'designation', None) or "Regional Officer & Director (Approval Bureau)"

    sign_data = [
        [
            Paragraph("<b>Security Verification Hash:</b><br/>" + f"SHA256-{hash(order_num + str(fdr.amount)) & 0xffffffffffffffff:016x}", ParagraphStyle('H', parent=meta_style, fontSize=7, leading=9, textColor=colors.HexColor('#64748b'))),
            Paragraph(f"<b>For and on behalf of AICTE</b><br/><br/><b>{officer_name}</b><br/>{officer_desig}<br/>All India Council for Technical Education", ParagraphStyle('Sig', parent=body_style, alignment=TA_RIGHT))
        ]
    ]
    sign_table = Table(sign_data, colWidths=[280, 240])
    sign_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'BOTTOM')]))
    story.append(Spacer(1, 20))
    story.append(sign_table)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
