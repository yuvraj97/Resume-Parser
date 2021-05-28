from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.layout import LAParams
from pdfminer.converter import PDFPageAggregator
from math import floor
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
                if isinstance(o, pdfminer.layout.LTTextLine):
                    text = o.get_text()
                    l.append([o.bbox, o.height, o.width, o.get_text()])
                    if int(o.y0) not in x0:
                        x0[int(o.y0)] = {}
                    if int(o.x0) not in x0[int(o.y0)]:
                        x0[int(o.y0)][int(o.x0)] = {}
                    if text not in x0[int(o.y0)][int(o.x0)]:
                        x0[int(o.y0)][int(o.x0)][text] = {}
                    x0[int(o.y0)][int(o.x0)][text]["bbox"] = o.bbox
                    x0[int(o.y0)][int(o.x0)][text]["height"] = floor(o.height)
                    x0[int(o.y0)][int(o.x0)][text]["width"] = o.width
                    x0[int(o.y0)][int(o.x0)][text]["text"] = o.get_text()
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

heights = set()
based_on_heights = {}
for k1 in reversed(sorted(x0.keys())):
    d[k1] = {}
    for k2 in sorted(x0[k1].keys()):
        d[k1][k2] = x0[k1][k2]
        for texts in d[k1][k2].keys():
            h = floor(d[k1][k2][texts]["height"])
            heights.add(h)
            if h not in based_on_heights:
                based_on_heights[h] = {}
            if k1 not in based_on_heights[h]:
                based_on_heights[h][k1] = {}
            based_on_heights[h][k1][k2] = d[k1][k2]

based_on_heights_d = {}
for h in reversed(sorted(based_on_heights.keys())):
    based_on_heights_d[h] = based_on_heights[h]

import json
print(json.dumps(based_on_heights_d, indent=4))
print(heights)

f = open("temp.json", 'w')
f.write(json.dumps(based_on_heights_d, indent=4))
f.close()