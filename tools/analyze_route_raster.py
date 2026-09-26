#!/usr/bin/env python3
import argparse, json, re
from pathlib import Path
import cv2
import numpy as np
import pytesseract

def ocr_region(img, x0,y0,x1,y1):
    crop=img[y0:y1,x0:x1]
    scale=cv2.resize(crop,None,fx=3,fy=3,interpolation=cv2.INTER_CUBIC)
    gray=cv2.cvtColor(scale,cv2.COLOR_BGR2GRAY)
    _,bw=cv2.threshold(gray,190,255,cv2.THRESH_BINARY)
    return pytesseract.image_to_string(bw,config="--psm 6").strip()

def analyze(path):
    img=cv2.imread(str(path))
    h,w=img.shape[:2]
    gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    # map body excludes title/border; keep broad enough for both maps
    x0,x1=int(w*.02),int(w*.98)
    y0,y1=int(h*.06),int(h*.90)
    roi=gray[y0:y1,x0:x1]
    dark=(roi<75).astype(np.uint8)*255
    kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))
    thick=cv2.morphologyEx(dark,cv2.MORPH_OPEN,kernel)
    n,labels,stats,cent=cv2.connectedComponentsWithStats(thick,8)
    comps=[]
    for i in range(1,n):
        x,y,cw,ch,area=stats[i]
        if area<20: continue
        comps.append({
            "area":int(area),"bbox":[int(x+x0),int(y+y0),int(cw),int(ch)],
            "centroid":[round(float(cent[i][0]+x0),1),round(float(cent[i][1]+y0),1)]
        })
    comps.sort(key=lambda z:z["area"],reverse=True)
    ocr={
      "top_right":ocr_region(img,int(w*.82),0,w,int(h*.14)),
      "right_edge":ocr_region(img,int(w*.93),0,w,h),
      "bottom_left":ocr_region(img,0,int(h*.78),int(w*.25),h),
      "left_edge":ocr_region(img,0,0,int(w*.08),h),
    }
    return {"file":str(path),"size_px":[w,h],"ocr":ocr,"largest_thick_dark_components":comps[:25]}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("images",nargs="+")
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    out=[analyze(Path(p)) for p in a.images]
    Path(a.output).write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
