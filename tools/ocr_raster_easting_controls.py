#!/usr/bin/env python3
import cv2,pytesseract,json,sys
from pathlib import Path
def read(strip):
 out=[]
 for rot in (cv2.ROTATE_90_CLOCKWISE,cv2.ROTATE_90_COUNTERCLOCKWISE):
  x=cv2.rotate(strip,rot); x=cv2.resize(x,None,fx=5,fy=5,interpolation=cv2.INTER_CUBIC)
  g=cv2.cvtColor(x,cv2.COLOR_BGR2GRAY)
  for t in (160,180,200,220):
   _,b=cv2.threshold(g,t,255,cv2.THRESH_BINARY)
   s=pytesseract.image_to_string(b,config="--psm 6 -c tessedit_char_whitelist=E0123456789").strip()
   out.append({"rotation":rot,"threshold":t,"text":s})
 return out
res={}
for p in sys.argv[1:-1]:
 im=cv2.imread(p);h,w=im.shape[:2]
 res[p]={"left":read(im[:,0:int(w*.12)]),"right":read(im[:,int(w*.88):w])}
Path(sys.argv[-1]).write_text(json.dumps(res,indent=2)+"\n")
print(json.dumps(res,indent=2))
