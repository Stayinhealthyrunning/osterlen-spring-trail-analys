#!/usr/bin/env python3
import argparse, json
from pathlib import Path
import cv2
import numpy as np
import pytesseract

def ocr(img, psm=6):
    scale=cv2.resize(img,None,fx=4,fy=4,interpolation=cv2.INTER_CUBIC)
    if len(scale.shape)==3: scale=cv2.cvtColor(scale,cv2.COLOR_BGR2GRAY)
    _,bw=cv2.threshold(scale,200,255,cv2.THRESH_BINARY)
    return pytesseract.image_to_string(bw,config=f"--psm {psm}").strip()

def components(mask, ox, oy, min_area=20):
    n,labels,stats,cent=cv2.connectedComponentsWithStats(mask,8)
    out=[]
    for i in range(1,n):
        x,y,w,h,area=map(int,stats[i])
        if area<min_area: continue
        out.append({"area":area,"bbox":[x+ox,y+oy,w,h],
                    "centroid":[round(float(cent[i][0]+ox),1),round(float(cent[i][1]+oy),1)]})
    return sorted(out,key=lambda z:z["area"],reverse=True)[:30]

def analyze(path):
    img=cv2.imread(str(path))
    h,w=img.shape[:2]
    gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    x0,x1=int(w*.02),int(w*.98)
    y0,y1=int(h*.06),int(h*.90)
    roi=gray[y0:y1,x0:x1]
    variants={}
    for t in (70,90,110,130,160):
        raw=(roi<t).astype(np.uint8)*255
        k3=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))
        op=cv2.morphologyEx(raw,cv2.MORPH_OPEN,k3)
        variants[str(t)]={"raw":components(raw,x0,y0,40),"open3":components(op,x0,y0,20)}
    right=img[:,int(w*.94):w]
    left=img[:,:int(w*.06)]
    ocrs={
      "top_right":ocr(img[0:int(h*.14),int(w*.80):w]),
      "bottom_left":ocr(img[int(h*.78):h,0:int(w*.28)]),
      "right_rot_cw":ocr(cv2.rotate(right,cv2.ROTATE_90_CLOCKWISE),7),
      "right_rot_ccw":ocr(cv2.rotate(right,cv2.ROTATE_90_COUNTERCLOCKWISE),7),
      "left_rot_cw":ocr(cv2.rotate(left,cv2.ROTATE_90_CLOCKWISE),7),
      "left_rot_ccw":ocr(cv2.rotate(left,cv2.ROTATE_90_COUNTERCLOCKWISE),7),
    }
    return {"file":str(path),"size_px":[w,h],"ocr":ocrs,
            "gray_percentiles":{str(p):float(np.percentile(roi,p)) for p in (1,2,5,10,25,50)},
            "components_by_threshold":variants}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("images",nargs="+"); ap.add_argument("--output",required=True)
    a=ap.parse_args(); out=[analyze(Path(p)) for p in a.images]
    Path(a.output).write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
