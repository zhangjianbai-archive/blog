"""Import catalogued DOCX ranges, checking text and images against each source.

Usage: python import_docx.py <directory containing the original 12 DOCX files>
Existing published articles are preserved. All catalog boundaries, including
already published articles, participate in range calculation.
"""
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from zipfile import ZipFile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
NS = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'a':'http://schemas.openxmlformats.org/drawingml/2006/main',
      'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
      'v':'urn:schemas-microsoft-com:vml'}
def text(node):
    return ''.join(n.text or '' for n in node.findall('.//w:t',NS))
def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()
def save(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def run(source_dir):
    catalog=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf-8'))
    articles=json.loads((ROOT/'content/articles.json').read_text(encoding='utf-8'))
    report=[]
    for filename in dict.fromkeys(a['source']['document'] for a in catalog):
        entries=sorted([a for a in catalog if a['source']['document']==filename],key=lambda a:a['source']['titleParagraphs'][0])
        with ZipFile(source_dir/filename) as z:
            body=ET.fromstring(z.read('word/document.xml')).find('w:body',NS)
            paragraphs=body.findall('w:p',NS)
            rels={r.attrib['Id']:r.attrib for r in ET.fromstring(z.read('word/_rels/document.xml.rels'))}
            indexed=[]; index=-1
            for block in body:
                if block.tag==f'{{{NS["w"]}}}p': index+=1
                indexed.append((index,block))
            for pos,item in enumerate(entries):
                if item.get('article'):continue
                ids=item['source']['titleParagraphs']; start=ids[0]
                end=entries[pos+1]['source']['titleParagraphs'][0] if pos+1<len(entries) else len(paragraphs)
                assert [text(paragraphs[i]).strip() for i in ids]==item['source']['rawTitle'],item['slug']
                blocks=[b for i,b in indexed if start<=i<end and not (i in ids and b.tag==f'{{{NS["w"]}}}p')]
                expected=[]; actual=[]; sections=[{'heading':'','paragraphs':[]}]; images=0; tables=0
                for block in blocks:
                    if block.tag==f'{{{NS["w"]}}}sectPr':continue
                    value=text(block)
                    if block.tag==f'{{{NS["w"]}}}tbl':
                        rows=[[text(cell) for cell in row.findall('w:tc',NS)] for row in block.findall('w:tr',NS)]
                        assert ''.join(''.join(row) for row in rows)==value,'Nested table needs manual review'
                        sections[-1]['paragraphs'].append({'table':rows});tables+=1
                        expected.append(value);actual.append(''.join(''.join(row) for row in rows))
                    elif value.strip():
                        expected.append(value)
                        style=block.find('w:pPr/w:pStyle',NS)
                        heading=style is not None and style.get(f'{{{NS["w"]}}}val') in {'2','3','Heading1','Heading2','Heading3'} and len(value)<120
                        if heading:sections.append({'heading':value,'paragraphs':[]})
                        else:sections[-1]['paragraphs'].append(value)
                        actual.append(value)
                    embeds=[n.get(f'{{{NS["r"]}}}embed') for n in block.findall('.//a:blip',NS)]
                    # Word can include empty VML fallback shapes without image data.
                    embeds += [n.get(f'{{{NS["r"]}}}id') for n in block.findall('.//v:imagedata',NS) if n.get(f'{{{NS["r"]}}}id')]
                    for rid in embeds:
                        assert rid and rid in rels,'Unresolved image'
                        rel=rels[rid];assert rel.get('TargetMode')!='External','External image needs review'
                        target=rel['Target']; member=target.lstrip('/') if target.startswith('/') else str(PurePosixPath('word')/target)
                        data=z.read(member); suffix=Path(member).suffix.lower()
                        assert suffix in {'.png','.jpeg','.jpg','.webp'},suffix
                        suffix='.jpg' if suffix=='.jpeg' else suffix
                        image_path='assets/articles/docx/'+hashlib.sha256(data).hexdigest()[:24]+suffix
                        dst=ROOT/'docs'/image_path;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data)
                        assert hashlib.sha256(dst.read_bytes()).digest()==hashlib.sha256(data).digest()
                        sections[-1]['paragraphs'].append({'image':image_path,'alt':f'{item["title"]}：原文配图 {images+1}'})
                        images+=1
                assert expected==actual,item['slug']
                assert actual or images,'Empty article requires review'
                # Preserve body exactly; only shorten the separate homepage excerpt.
                candidates=[p for s in sections for p in s['paragraphs'] if isinstance(p,str) and len(p)>65 and not re.match(r'^(作者|编辑于|发布于|http)',p)]
                excerpt=(candidates[0][:160]+'…' if len(candidates[0])>160 else candidates[0]) if candidates else ''
                article={k:item[k] for k in ('slug','title','author','category','tags')}
                article.update(source=filename,sections=sections,excerpt=[excerpt] if excerpt else [])
                articles.append(article);item['article']=item['slug']
                report.append({'slug':item['slug'],'source':filename,'startParagraph':start,'endParagraphExclusive':end,
                               'textBlocks':len(actual),'images':images,'tables':tables,'sourceTextSHA256':digest('\n'.join(expected)),
                               'outputTextSHA256':digest('\n'.join(actual))})
    if not report:
        print('No unpublished entries; preserved the existing import audit.')
        return
    save(ROOT/'content/articles.json',articles);save(ROOT/'content/catalog.json',catalog)
    save(ROOT/'content/import-audit.json',report)
    print(f'Imported {len(report)} articles; verified {sum(r["textBlocks"] for r in report)} text blocks and {sum(r["images"] for r in report)} image references.')
if __name__=='__main__':run(Path(sys.argv[1]))
