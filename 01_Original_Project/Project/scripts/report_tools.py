"""Shared, deterministic formatting for the research report."""
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]

class Report:
    def __init__(self):
        self.doc = Document()
        s = self.doc.sections[0]
        s.page_width, s.page_height = Inches(8.5), Inches(11)
        s.top_margin, s.bottom_margin = Inches(.78), Inches(.72)
        s.left_margin = s.right_margin = Inches(.78)
        s.header_distance = s.footer_distance = Inches(.3)
        styles = self.doc.styles
        for name in ['Normal','Title','Subtitle','Heading 1','Heading 2','Heading 3','Caption']:
            st=styles[name]
            st.font.name='Calibri'
            st.font.color.rgb=RGBColor(0,0,0)
            st.paragraph_format.space_after=Pt(7)
        styles['Normal'].font.size=Pt(11)
        styles['Normal'].paragraph_format.line_spacing=1.12
        styles['Normal'].paragraph_format.widow_control=True
        for name,size in [('Title',29),('Subtitle',15),('Heading 1',18),('Heading 2',13),('Heading 3',11.5)]:
            styles[name].font.size=Pt(size)
            styles[name].font.bold=name!='Subtitle'
            styles[name].paragraph_format.space_before=Pt(12)
            styles[name].paragraph_format.keep_with_next=True
        styles['Caption'].font.size=Pt(9)
        styles['Caption'].font.italic=False
        styles['Caption'].paragraph_format.space_before=Pt(4)
        styles['Caption'].paragraph_format.space_after=Pt(9)
        s.different_first_page_header_footer=True
        f=s.footer.paragraphs[0]
        f.alignment=WD_ALIGN_PARAGRAPH.RIGHT
        f.add_run('Banks and NBFCs in India  |  ').font.size=Pt(8)
        field=OxmlElement('w:fldSimple'); field.set(qn('w:instr'),'PAGE')
        f._p.append(field)
        self.doc.core_properties.title='Risk Return Analysis and Derivative Based Comparison of NBFCs and Commercial Banks in India'
        self.doc.core_properties.author='Sahitya Biswas; Subhajit Paul; Anirban Nayak'
        self.doc.core_properties.subject='Empirical equity and option analysis for 2021 to 2025'
        self.doc.core_properties.keywords='Banks, NBFCs, India, risk, return, portfolio, Black Scholes'
        self.figure_count=0
        self.table_count=0

    def p(self,text,style=None):
        return self.doc.add_paragraph(text,style)

    def heading(self,text,level=1,new_page=False):
        if new_page: self.doc.add_page_break()
        return self.doc.add_heading(text,level)

    def table(self,headers,rows,widths=None,caption=None,small=9.3):
        if caption:
            self.table_count+=1
            p=self.p(f'Table {self.table_count}  {caption}','Caption')
            p.paragraph_format.keep_with_next=True
        t=self.doc.add_table(rows=1, cols=len(headers))
        t.alignment=WD_TABLE_ALIGNMENT.CENTER
        t.autofit=False
        total=6.94
        widths=widths or [total/len(headers)]*len(headers)
        for col,w in zip(t.columns,widths): col.width=Inches(w)
        for i,h in enumerate(headers): t.rows[0].cells[i].text=str(h)
        for row in rows:
            c=t.add_row().cells
            for i,value in enumerate(row): c[i].text=str(value)
        for ri,row in enumerate(t.rows):
            pr=row._tr.get_or_add_trPr()
            cant=OxmlElement('w:cantSplit'); pr.append(cant)
            if ri==0:
                repeat=OxmlElement('w:tblHeader'); pr.append(repeat)
            for ci,cell in enumerate(row.cells):
                cell.width=Inches(widths[ci])
                cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                tcPr=cell._tc.get_or_add_tcPr()
                borders=OxmlElement('w:tcBorders')
                for edge in ['top','left','bottom','right']:
                    e=OxmlElement('w:'+edge); e.set(qn('w:val'),'single'); e.set(qn('w:sz'),'4'); e.set(qn('w:color'),'D9D9D9'); borders.append(e)
                tcPr.append(borders)
                mar=OxmlElement('w:tcMar')
                for edge,val in [('top',90),('bottom',90),('left',95),('right',95)]:
                    e=OxmlElement('w:'+edge); e.set(qn('w:w'),str(val)); e.set(qn('w:type'),'dxa'); mar.append(e)
                tcPr.append(mar)
                shade=OxmlElement('w:shd'); shade.set(qn('w:fill'),'203B55' if ri==0 else ('F1F5F8' if ri%2==0 else 'FFFFFF')); tcPr.append(shade)
                for p in cell.paragraphs:
                    p.paragraph_format.space_after=Pt(1)
                    p.paragraph_format.line_spacing=1.05
                    p.alignment=WD_ALIGN_PARAGRAPH.LEFT if ci==0 else WD_ALIGN_PARAGRAPH.CENTER
                    for run in p.runs:
                        run.font.size=Pt(small)
                        run.font.bold=(ri==0)
                        run.font.color.rgb=RGBColor.from_string('FFFFFF' if ri==0 else '000000')
        self.p('').paragraph_format.space_after=Pt(1)
        return t

    def figure(self,path,caption,width=6.75):
        path=ROOT/path
        if not path.exists(): raise FileNotFoundError(path)
        p=self.doc.add_paragraph()
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.keep_with_next=True
        run=p.add_run(); run.add_picture(str(path),width=Inches(width))
        docpr=run._r.xpath('.//wp:docPr')
        if docpr: docpr[0].set('descr',caption)
        self.figure_count+=1
        self.p(f'Figure {self.figure_count}  {caption}','Caption')

    def equation(self,path,width=5.5):
        p=self.doc.add_paragraph()
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(ROOT/path),width=Inches(width))

    def bullet(self,text): self.p(text,'List Bullet')

    def save(self,path):
        path=ROOT/path; path.parent.mkdir(parents=True,exist_ok=True)
        self.doc.save(path)
        return path
