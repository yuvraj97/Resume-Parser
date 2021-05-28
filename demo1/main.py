from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.layout import LAParams
from pdfminer.converter import PDFPageAggregator
from math import *
import pdfminer
import numpy as np
import json
 
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
    js = {}
    for obj in objs:
        if isinstance(obj, pdfminer.layout.LTTextBox):
            for o in obj._objs:
                if isinstance(o, pdfminer.layout.LTTextLine):
                    text = o.get_text()
                    if text.replace("\n", "").replace(" ", "") == "": continue
                    text = text.strip()
                    x0, y0 = int(o.x0), int(o.y0)
                    min_val = None
                    min_params = []
                    for _y0 in js.keys():
                        for _x0 in js[_y0].keys():
                            for _text in js[_y0][_x0]:
                                if _y0 - o.y1 < 0: continue
                                if js[_y0][_x0][_text]["height"] != int(o.height): continue
                                if min_val is None or _y0 - o.y1 < min_val:
                                    min_val = _y0 - o.y1
                                    min_params = [_x0, _y0, _text]
                    if min_val is not None and min_val < 3:
                        _x0, _y0, _text = min_params
                        # print((_text, text))
                        js[_y0][_x0][_text]["text"] = _text + " " + text
                        js[_y0][_x0][_text + " " + text] = js[_y0][_x0][_text]
                        del js[_y0][_x0][_text]
                        continue

                    # print(text)
                    l.append([o.bbox, o.height, o.width, o.get_text()])
                    if y0 not in js:
                        js[y0] = {}
                    if x0 not in js[y0]:
                        js[y0][x0] = {}
                    if text not in js[y0][x0]:
                        js[y0][x0][text] = {}
                    js[y0][x0][text]["bbox"] = o.bbox
                    js[y0][x0][text]["height"] = floor(o.height)
                    js[y0][x0][text]["width"] = o.width
                    js[y0][x0][text]["text"] = o.get_text()
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

    return l, js

def find_coordinates(d, side_by_side, layout):
    bboxes = []
    x0, y0, x1, y1 = [], [], [], []
    text = []
    for _y0 in d.keys():
        for _x0 in d[_y0].keys():
            for _text in d[_y0][_x0].keys():
                __x0, __y0, __x1, __y1 = d[_y0][_x0][_text]["bbox"]
                x0.append(int(__x0))
                y0.append(int(__y0))
                x1.append(int(__x1))
                y1.append(int(__y1))
                text.append(_text)
                # bboxes.append((d[_y0][_x0][text]["bbox"], text))
    # x0, y0, x1, y1 = np.array(x0), np.array(y0), np.array(x1), np.array(y1)
        
    if side_by_side:
        
        d = {}
        
        left = []
        right = []
        l_text = []
        r_text = []
        
        divider = None
        for i, _x0 in enumerate(x0):
            if _x0 > layout.width/2:
                if divider is None or _x0 < divider:
                    divider = _x0
                right.append([x0[i], x1[i], y0[i], y0[i]])
                r_text.append(text[i])
            else:
                left.append([x0[i], x1[i], y0[i], y0[i]])
                l_text.append(text[i])
        
        # print(f"divider: {divider}")
        # print(f"left: {left}")
        # print(f"right: {right}")
        # print(f"l_text: {l_text}")
        # print(f"r_text: {r_text}")
        
        left, right = np.array(left), np.array(right)

        indices = list(reversed(np.argsort(left[:, 2])))
        # print(indices)
        for i in range(len(indices)):
            if i == len(indices) - 1: break
            d[l_text[indices[i]]] = {}
            d[l_text[indices[i]]]["y-coord"] = (left[indices[i]][2] - 3, left[indices[i+1]][2] + 3)
        d[l_text[indices[-1]]] = {}
        d[l_text[indices[-1]]]["y-coord"] = (left[indices[-1]][2] - 3, 0)

        for t in l_text:
            d[t]["x-coord"] = (0, divider)

        indices = list(reversed(np.argsort(right[:, 2])))
        # print(indices)
        for i in range(len(indices)):
            if i == len(indices) - 1: break
            d[r_text[indices[i]]] = {}
            d[r_text[indices[i]]]["y-coord"] = (right[indices[i]][2] - 3, right[indices[i+1]][2] + 3)
        d[r_text[indices[-1]]] = {}
        d[r_text[indices[-1]]]["y-coord"] = (right[indices[-1]][2] - 3, 0)


        for t in r_text:
            d[t]["x-coord"] = (divider - 5, layout.width)
            
        # print(d)
        
    else:
        d = {}
        # print(f"y0: {y0}")
        # print(f"text: {text}")
        indices = list(reversed(np.argsort(y0)))
        # print(indices)
        for i in range(len(indices)):
            if i == len(indices) - 1: break
            d[text[indices[i]]] = {}
            d[text[indices[i]]]["y-coord"] = (y0[indices[i]], y0[indices[i+1]])
        d[text[indices[-1]]] = {}
        d[text[indices[-1]]]["y-coord"] = (y0[indices[-1]], 0)

        for k in d.keys():
            d[k]["x-coord"] = (0, layout.width)
    
    return d
       
def get_data_within_box(data, properties):
    # print(properties)
    y_min, y_max = min(properties["y-coord"]), max(properties["y-coord"])
    x_min, x_max = min(properties["x-coord"]), max(properties["x-coord"])
    d = {}
    for y0 in data:
        for x0 in data[y0]:
            for text in data[y0][x0]:
                _x0, _y0, _x1, _y1 = data[y0][x0][text]["bbox"]
                if _y0 > y_min + 1 and _y1 < y_max - 1 and _x0 > x_min + 1 and _x1 < x_max - 1:
                    d[text] = data[y0][x0][text]
    # print(json.dumps(d, indent=4))
    return d

def get_data(data, coords):
    d = {}
    for k in coords.keys():
        # print(k)
        d[k] = get_data_within_box(data, coords[k])
        # print(json.dumps(d[k], indent=4))
        # d = {**d, **get_data_within_box(data, coords[k])}
    return d
 
def featch_insighted_at_once(data):
    heights = set()
    for text in data.keys():
        # print(text)
        heights.add(data[text]["height"])
    height = max(heights)
    
    d = {}
    for text in data.keys():
        d[text] = data[text]

    # print(json.dumps(d, indent=4))

    # print(d)
    
    return d
        
    

def featch_insighted(data):
    d = {}
    for k in data.keys():
        # if k == "INVESTOR RELATIONS, FUND STRUCTURING, CONTROLLERSHIP & COMPLIANCE": continue
        # if k == "EDUCATION": continue
        # if k == "SKILLS": continue
        # if k == "PROJECTS": continue
        # if k == "EXPERIENCE": continue
        # print(k)
        # print(data[k])
        # print()
        d[k] = featch_insighted_at_once(data[k])
        # print()
        # print()
        # print()
        # break
    return d


document = createPDFDoc("../resume-rahul-prajapati.pdf")
device, interpreter = createDeviceInterpreter()
pages = PDFPage.create_pages(document)
interpreter.process_page(next(pages))
layout = device.get_result()
l, js = parse_obj(layout._objs)

max_widths = None
for k1 in js.keys():
    for k2 in js[k1].keys():
        for text in js[k1][k2].keys():
            if max_widths is None or max_widths < js[k1][k2][text]["width"]:
                max_widths = js[k1][k2][text]["width"]
                # print(text)
# print(max_widths)

side_by_side = False
if max_widths < layout.width * 0.75:
    side_by_side = True

# print(f"side_by_side: {side_by_side}")

d = {}

f_heights = set()
based_on_heights = {}
for k1 in reversed(sorted(js.keys())):
    d[k1] = {}
    for k2 in sorted(js[k1].keys()):
        d[k1][k2] = js[k1][k2]
        for texts in d[k1][k2].keys():
            h = floor(d[k1][k2][texts]["height"])
            f_heights.add(h)
            if h not in based_on_heights:
                based_on_heights[h] = {}
            if k1 not in based_on_heights[h]:
                based_on_heights[h][k1] = {}
            based_on_heights[h][k1][k2] = d[k1][k2]

f_heights = list(reversed(sorted(f_heights)))

name = based_on_heights[f_heights[0]]
special_features = {}
features = based_on_heights[f_heights[1]]
if len(features) == 1:
    special_features = features
    features = based_on_heights[f_heights[2]]
coords = find_coordinates({**special_features, **features}, side_by_side, layout)


segmented_data = get_data(d, coords)
# print(json.dumps(segmented_data, indent=4))

data = featch_insighted(segmented_data)

d = {}
for k in data:
    d[k] = []
    # print(k)
    for text in data[k]:
        # print(f"\t {text}")
        d[k].append(text)
print(json.dumps(d, indent=4))

# for y0 in based_on_heights[f_heights[1]].keys():
#     for x0 in based_on_heights[f_heights[1]][y0].keys():
#         for text in based_on_heights[f_heights[1]][y0][x0].keys():
#             print(text)

based_on_heights_d = {}
for h in reversed(sorted(based_on_heights.keys())):
    based_on_heights_d[h] = based_on_heights[h]

# print(json.dumps(based_on_heights_d, indent=4))
# print(f_heights)

f = open("temp.json", 'w')
f.write(json.dumps(d, indent=4))
f.close()

f = open("based_on_heights.json", 'w')
f.write(json.dumps(based_on_heights_d, indent=4))
f.close()

f = open("segmented_data.json", 'w')
f.write(json.dumps(segmented_data, indent=4))
f.close()

