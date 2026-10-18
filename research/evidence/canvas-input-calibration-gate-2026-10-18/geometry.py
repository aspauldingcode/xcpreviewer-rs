"""Operator-supplied screenshot geometry; finite mapping safety, not live hit testing."""
import math

def need(v,m):
 if not v:raise ValueError(m)
def inside(point,box):return box[0]<point[0]<box[2] and box[1]<point[1]<box[3]
def calibrate(size,button,editor):
 for seq,n in [(size,2),(button,4),(editor,4)]:need(type(seq) is list and len(seq)==n and all(type(v) in (int,float) and math.isfinite(v) for v in seq),'numeric geometry')
 need(all(v>0 for v in size),'size');window=[0,0,*size]
 for box in [button,editor]:need(0<box[0]<box[2]<size[0] and 0<box[1]<box[3]<size[1],'interior box')
 center=[(button[0]+button[2])/2,(button[1]+button[3])/2];point=[round(x/2) for x in center];mapped=[2*x for x in point]
 need(inside(point,window) and inside(mapped,window),'candidate containment')
 need(inside(point,editor) and inside(mapped,button),'safe distinguishing targets')
 return {'raw_point':point,'factor1_destination':point,'factor2_destination':mapped,'mapping_assumed':False,'scope':'Only two declared factors with origin0; operator geometry and screenshot freshness are prerequisites. Native receipt distinguishes successful input; no general coordinate mapping claim.'}
