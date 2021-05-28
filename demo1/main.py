from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.layout import LAParams
from pdfminer.converter import PDFPageAggregator
import pdfminer

def createPDFDoc(fpath):
    fp = open(fpath, 'rb')
    parser = PDFParser(fp)
    document = PDFDocument(parser, password='')
    # Check if the document allows text extraction. If not, abort.
    if not document.is_extractable:
        raise ValueError("Not extractable")
    else:
        return document


def createDeviceInterpreter():
    rsrcmgr = PDFResourceManager()
    laparams = LAParams()
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    return device, interpreter


def parse_obj(objs):
    l = []
    x0 = {}
    for obj in objs:
        if isinstance(obj, pdfminer.layout.LTTextBox):
            for o in obj._objs:
                if isinstance(o,pdfminer.layout.LTTextLine):
                    # print(text)
                    # print(f"X0:{o.x0}, X1{o.x1}, Y0:{o.y0}, Y1:{o.y1}")
                    # print(f"bbox: {o.bbox}")
                    # print(f"height: {o.height}, width:{o.width}, word_margin:{o.word_margin}")
                    text=o.get_text()
                    l.append([o.bbox, o.height, o.width, o.get_text()])
                    if int(o.x0) not in x0:
                        x0[int(o.x0)] = {}
                    if int(o.y0) not in x0[int(o.x0)]:
                        x0[int(o.x0)][int(o.y0)] = {}
                    if text not in x0[int(o.x0)][int(o.y0)]:
                        x0[int(o.x0)][int(o.y0)][text] = {}
                    x0[int(o.x0)][int(o.y0)][text]["bbox"] = o.bbox
                    x0[int(o.x0)][int(o.y0)][text]["height"] = o.height
                    x0[int(o.x0)][int(o.y0)][text]["width"] = o.width
                    x0[int(o.x0)][int(o.y0)][text]["text"] = o.get_text()
                        # x0[o.x0]["bbox"].append(o.bbox)
                        # x0[o.x0]["height"].append(o.height)
                        # x0[o.x0]["width"].append(o.width)
                        # x0[o.x0]["text"].append(o.get_text())
                    # print()
                    # if text.strip():
                    #     for c in  o._objs:
                    #         if isinstance(c, pdfminer.layout.LTChar):
                    #             # print("fontname %s"%c.fontname)\
                    #             print(dir(c))
                    #             pass

        # if it's a container, recurse
        elif isinstance(obj, pdfminer.layout.LTFigure):
            parse_obj(obj._objs)
        else:
            pass

    return l, x0

document = createPDFDoc("../resume.pdf")
device, interpreter = createDeviceInterpreter()
pages = PDFPage.create_pages(document)
# print(dir(pages))
interpreter.process_page(next(pages))
layout = device.get_result()
l, x0 = parse_obj(layout._objs)
# print(l)

d = {}

for k1 in sorted(x0.keys()):
    d[k1] = {}
    for k2 in reversed(sorted(x0[k1].keys())):
        d[k1][k2] = x0[k1][k2]

import json
print(json.dumps(d, indent=4))
