#!/usr/bin/env python3
import cv2, json, numpy as np, argparse
from pathlib import Path

def main():
    a=argparse.ArgumentParser(); a.add_argument("--trail5",required=True); a.add_argument("--trail14",required=True); a.add_argument("--output",required=True); x=a.parse_args()
    im5=cv2.imread(x.trail5,0); im14=cv2.imread(x.trail14,0)
    sift=cv2.SIFT_create(nfeatures=8000)
    k5,d5=sift.detectAndCompute(im5,None); k14,d14=sift.detectAndCompute(im14,None)
    m=cv2.BFMatcher().knnMatch(d14,d5,k=2)
    good=[p for p,q in m if p.distance < .70*q.distance]
    src=np.float32([k14[z.queryIdx].pt for z in good]).reshape(-1,1,2)
    dst=np.float32([k5[z.trainIdx].pt for z in good]).reshape(-1,1,2)
    H,mask=cv2.findHomography(src,dst,cv2.RANSAC,3.0)
    inl=int(mask.sum()) if mask is not None else 0
    errs=[]
    if H is not None:
      pred=cv2.perspectiveTransform(src,H)
      errs=np.sqrt(((pred-dst)**2).sum(axis=2)).reshape(-1)
      errs=errs[mask.reshape(-1).astype(bool)]
    out={"trail14_to_trail5_homography":H.tolist() if H is not None else None,
         "sift_keypoints":{"trail5":len(k5),"trail14":len(k14)},
         "ratio_test_matches":len(good),"ransac_inliers":inl,
         "inlier_ratio":inl/max(1,len(good)),
         "reprojection_px":{"median":float(np.median(errs)) if len(errs) else None,"p95":float(np.percentile(errs,95)) if len(errs) else None}}
    Path(x.output).write_text(json.dumps(out,indent=2)+"\n"); print(json.dumps(out,indent=2))
if __name__=="__main__": main()
