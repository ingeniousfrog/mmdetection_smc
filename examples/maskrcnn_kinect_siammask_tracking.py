from __future__ import absolute_import

from __future__ import division

from __future__ import print_function

from __future__ import unicode_literals
import math
import traceback

import sys

sys.path.insert(0, '../pysot')

import os

import argparse

from PIL import Image

from matplotlib import pyplot as plt

import pycocotools.mask as maskUtils

import time

import numpy as np

import cv2

import threading

from scipy.interpolate import splprep, splev

from ctypes import cdll

import ctypes

from numpy.ctypeslib import ndpointer

import shutil

import mmcv

from mmdet.apis import init_detector, inference_detector

from mmcv.visualization.color import color_val

 

 

import os

import argparse

 

import cv2

import torch

import numpy as np

from glob import glob

 

from pysot.core.config import cfg

from pysot.models.model_builder import ModelBuilder

from pysot.tracker.tracker_builder import build_tracker

 

torch.set_num_threads(2)

 

 

i=0

depth_mem=None

first_flag=True

 

config_file = 'configs/cascade_mask_rcnn_x101_64x4d_fpn_1x.py'

checkpoint_file = 'checkpoints/cascade_mask_rcnn_x101_64x4d_fpn_20e_20181218-630773a7.pth'

model = init_detector(config_file, checkpoint_file)

class_names = model.CLASSES

score_thr=0.3

 

 

lib = cdll.LoadLibrary('./viewer_opengl.so')

st = lib.Foo_start

t0 = threading.Thread(target=st)

t0.start()

end = lib.Foo_end

dataread =lib.Foo_dataread

dataread_color =lib.Foo_dataread_color

dataread_depth =lib.Foo_dataread_depth

dataread_color_to_depth =lib.Foo_dataread_color_to_depth

dataread.restype = ndpointer(dtype=ctypes.c_uint8, shape=(720,1280,2))

dataread_color.restype = ndpointer(dtype=ctypes.c_uint8, shape=(720,1280,4))

dataread_depth.restype = ndpointer(dtype=ctypes.c_uint16, shape=(512,512))#ctypes.POINTE

dataread_color_to_depth.restype = ndpointer(dtype=ctypes.c_uint8, shape=(512,512,4))
convert_2d_3d = lib.Foo_convert_2d_3d
convert_2d_3d.restype = ndpointer(dtype=ctypes.c_float, shape=(3))#ctypes.POINTE
convert_2d_2d = lib.Foo_convert_2d_2d
convert_2d_2d.restype = ndpointer(dtype=ctypes.c_float, shape=(2))#ctypes.POINTE


 

classname = "test"

classname1 = classname

smooth_rate = 200

classnumber = 4

scale_factor = 1.1

home_path=os.getcwd() 

 

classname = classname+"_"

rgb_segmentation =1

darker = 0;

sensitivity = 245;

x= 0

y = 0

w = 0

h = 0

def adjust_gamma(image, gamma=1.0):

	# build a lookup table mapping the pixel values [0, 255] to

	# their adjusted gamma values

	invGamma = 1.0 / gamma

	table = np.array([((i / 255.0) ** invGamma) * 255

		for i in np.arange(0, 256)]).astype("uint8")

 

	# apply gamma correction using the lookup table

	return cv2.LUT(image, table)

color_img = np.zeros((1280,720,3),dtype = np.uint8)

result_mask_img =np.zeros((1280,720,3),dtype = np.uint8)

result_bbox_img =np.zeros((1280,720,3),dtype = np.uint8)

result_mask =np.zeros((1280,720),dtype = np.uint8)

pysot_img =np.zeros((1280,720,3),dtype = np.uint8)

mask_rcnn_flag = 0

pysot_mask=np.zeros((1280,720),dtype = np.uint8)

pysot_contour_img =np.zeros((1280,720,3),dtype = np.uint8)

 

cfg.merge_from_file('config.yaml')

cfg.CUDA = torch.cuda.is_available()

device = torch.device('cuda' if cfg.CUDA else 'cpu')

model_pysot = ModelBuilder()

tracker = build_tracker(model_pysot)

model_pysot.load_state_dict(torch.load('model.pth',map_location=lambda storage, loc: storage.cpu()))

model_pysot.eval().to(device)

def run_maskrcnn():

    global color_img

    global result_mask_img

    global result_bbox_img

    global result_mask

    global mask_rcnn_flag

    global inds_len

    while 1:

        mask_rcnn_flag=1
        start_time = time.time()
        result = inference_detector(model, color_img)
        print("--- maskrcnn %s seconds ---" % (time.time() - start_time))
        result_mask_img,result_bbox_img,result_mask = show_result(color_img, result, model.CLASSES)

        #print(result)

 

def show_result(img,result,class_names):

       global mask_rcnn_flag

       img_mask = img.copy()

       mask_temp = img.copy()

       bbox_result, segm_result = result

       bboxes = np.vstack(bbox_result)

       labels = [

           np.full(bbox.shape[0], i, dtype=np.int32)

           for i, bbox in enumerate(bbox_result)

       ]

 

       labels = np.concatenate(labels)

       bbox_color = 'green'

       text_color = 'green'

       thickness=1

       font_scale = 3

       show=True

       win_name=''

       wait_time = 0

       out_file = None

       assert bboxes.ndim == 2

       assert labels.ndim == 1

       assert bboxes.shape[0] == labels.shape[0]

       assert bboxes.shape[1] == 4 or bboxes.shape[1] == 5

 

       bbox_color = color_val(bbox_color)

       text_color = color_val(text_color)

 

       prev_point = [0,0]

 

       for i in range(0,len(bboxes)):

          label_text = class_names[labels[i]] if class_names is not None else 'cls {}'.format(labels[i])

          if len(bboxes[i]) > 4:

                  label_text += '|{:.02f}'.format(bboxes[i][-1])

          left_top = (int(bboxes[i][0]),int(bboxes[i][1]) )

          right_bottom = (int(bboxes[i][2]), int(bboxes[i][3]))

          if bboxes[i][-1]<0.5 :

              pass

          else :

              img = cv2.putText(img , str(label_text) , (int(bboxes[i][0]),int(bboxes[i][1])), cv2.FONT_HERSHEY_SIMPLEX, 0.5,(255,0,0) ,1)

              #print(bboxes[i])

              img = cv2.rectangle(img , (int(bboxes[i][0]),int(bboxes[i][1])),(int(bboxes[i][2]),int(bboxes[i][3])),(255,0,0) ,1)

       mask_temp=np.zeros((720,1280),dtype = np.uint8)

       if segm_result is not None:

           

           segms = mmcv.concat_list(segm_result)

           inds = np.where(bboxes[:, -1] > score_thr)[0]

           mask_temp = mask_temp*0

           inds_len = 0

           for i in inds:

               label_text = class_names[labels[i]] if class_names is not None else 'cls {}'.format(labels[i])
               #print(label_text)
               if label_text =='banana':

                  color_mask = np.random.randint(0, 256, (1, 3), dtype=np.uint8)

 

                  mask = maskUtils.decode(segms[i]).astype(np.bool)

 

                  mask_temp[mask] = 255

                  #print(color_mask.shape)

                  #print(color_mask)

                  img_mask[mask] = img_mask[mask] * 0.5 + color_mask * 0.5 

                  img_mask = cv2.putText(img_mask, str(label_text) , (int(bboxes[i][0]),int(bboxes[i][1])), cv2.FONT_HERSHEY_SIMPLEX, 1,(int(color_mask[0,0]),int(color_mask[0,1]),int(color_mask[0,2])) ,2)

                  init_rect = [int(bboxes[i][0]),int(bboxes[i][1]),int(bboxes[i][2])-int(bboxes[i][0]),int(bboxes[i][3])-int(bboxes[i][1])]

                  #print(init_rect)

                  tracker.init(color_img, init_rect)

                  inds_len = inds_len+1

                  #print("banana")

 

                  continue

               

       mask_rcnn_flag=0

       return (img_mask,img,mask_temp)
#--------indy-----------------
import sys
print('sys.argv length:',len(sys.argv))

for arg in sys.argv: 
    print('arg value = ', arg) 

from indydcp_client import IndyDCPClient
bind_ip = "192.168.0.6"   
server_ip = "192.168.0.7"
robot_name = "NRMK-Indy7"

indy = IndyDCPClient(bind_ip, server_ip, robot_name) 
indy.connect()
indy.set_task_boundary_level(9)
indy.set_task_blend_radius(200)
indy.task_move_to([0.5, 0, 0.5, -180 , 0 ,180 ])
#-------------------------
def calc():
   global error_x
   global error_y
   global convert_x
   global convert_y
   global convert_z
 
   convert_x = 0.0
   convert_y = 0.0
   convert_z = 0.0
   error_x = 0
   error_y = 0
   prev_error_x = 0
   prev_error_y = 0
   alpha = 0.5
   Kp = 0.007
   
   while 1: 
     convert_data_ = convert_2d_2d(640,320)
     convert_data=convert_2d_3d(int(convert_data_[0]),int(convert_data_[1]))
     center_x = -1*convert_data[0]/1000
     center_y = -1*convert_data[1]/1000
     center_z = convert_data[2]/1000
     error_x = convert_x - center_x
     error_y = convert_y - center_y
     error_z = (0.3-convert_z)*0.1
     #print("center : ",center_x,center_y,center_z)
     #print("convert: ",convert_x,convert_y,convert_z)
     #print("error : ",error_x,error_y,0) 

     if abs(error_x) < 0.01:
        error_x = 0
     if abs(error_y) < 0.01:
        error_y = 0
     Kp_x = 0.5
     Kp_y = 1
     move_x = Kp_x*error_x
     move_y = Kp_y*error_y
     if move_x > 0.05 :
       move_x = 0.05
     if move_y > 0.05 :
       move_y = 0.05
     #print(error_z)
     start_time = time.time()
     indy.task_move_by([move_y, move_x, 0, 0 , 0 ,0 ])
     print("--- indy move %s seconds ---" % (time.time() - start_time))
     prev_error_x = x
     prev_error_y = y
def detect_img():

    global color_img
    global error_x
    global error_y
    global result_mask_img

    global result_bbox_img

    global result_mask

    global pysot_img

    global pysot_contour_img

    global pysot_mask
    global center
    error_x = 0
    error_y = 0
    center = np.zeros(2,dtype=int)
    def nothing(x):

       pass

    cv2.namedWindow("rgb", cv2.WINDOW_NORMAL)

    cv2.resizeWindow("rgb", 1280,720)

    cv2.namedWindow("mask", cv2.WINDOW_NORMAL)

    cv2.resizeWindow("mask", 1280,720)

    cv2.namedWindow("depth", cv2.WINDOW_NORMAL)

    cv2.resizeWindow("depth", 1280,720)

    cv2.createTrackbar('W', 'rgb', 0, 100, nothing)

    cv2.createTrackbar('W2', 'mask', 0, 100, nothing)

    show_mask = np.zeros((1280,720,3))

    show_img = np.zeros((1280,720,3))
    n=0
    while 1:

      color_data = np.array(dataread_color(),dtype=np.uint8)

      color_img = color_data[:,:,0:3]
      cv2.imwrite('img_'+str(n)+'_.png',color_img)
      depth_to_color_data = np.array(dataread(),dtype=np.uint8)

      depth_to_color_img = depth_to_color_data[:,:,0]

      depth_img = depth_to_color_img.copy()

      w = cv2.getTrackbarPos('W','rgb')

      w2 = cv2.getTrackbarPos('W2','mask')

      temp_pysot_mask = cv2.cvtColor(np.uint8(pysot_mask),cv2.COLOR_GRAY2RGB)

      temp_pysot_mask[:,:,0]=0

      temp_pysot_mask[:,:,2]=0

 

      temp_result_mask = cv2.cvtColor(result_mask,cv2.COLOR_GRAY2RGB)

      try:       

        #print(type(pysot_contour_img))

        show_img = cv2.addWeighted(np.uint8(pysot_contour_img),float(100-w) * 0.01, np.array(result_mask_img),float(w) * 0.01,0)

 

 

        show_mask = cv2.addWeighted(temp_pysot_mask,float(100-w2) * 0.01, temp_result_mask,float(w2) * 0.01,0)

      except: 
        pass         
  #Exception:
        #print("MAIN ERROR:  "+traceback.format_exc())
        #show_mask = pysot_mask.copy()

      cv2.imshow("rgb",show_img)
      show_img_temp = cv2.circle(show_img.copy(),(int(center[0]),int(center[1])),10,(0,0,255),5)
      show_img_temp = cv2.line(show_img_temp,(640,360),(int(center[0]),int(center[1])),(255,0,0),1)
      cv2.imshow("depth",show_img_temp)

      cv2.imshow("mask",show_mask)

 

      k = cv2.waitKey(5) & 0xFF

      if k == ord('s'):

         cv2.destroyWindow("rgb")
    values = stop
    ser.write(values)
    end()

 



def run_pysot():

   global color_img

   global pysot_img

   global pysot_contour_img

   

   global pysot_mask

   global center

   global result_mask_img

   global inds_len
   global convert_x
   global convert_y
   global convert_z
 
   convert_x = 0.0
   convert_y = 0.0
   convert_z = 0.0
   prev_pysot_img = np.zeros((720,1280,3))

   prev_mask = np.zeros((720,1280))

   pysot_mask = np.zeros((720,1280))

   pysot_contour_img= np.zeros((720,1280,3))
   center = np.zeros(2,dtype=int)
   while 1:
     start_time = time.time()

     try:

       pysot_img = color_img.copy()

       #print("run pysot")

       outputs = tracker.track(color_img)

       pysot_mask = np.zeros((720,1280))

       if 'polygon' in outputs:

 

                color_mask = np.random.randint(0, 256, (1, 3), dtype=np.uint8)

                polygon = np.array(outputs['polygon']).astype(np.int32)

                cv2.polylines(pysot_img, [polygon.reshape((-1, 1, 2))],True, (0, 255, 0), 3)

 

                mask = ((outputs['mask'] > cfg.TRACK.MASK_THERSHOLD) * 255)

 

                #print(mask.max())

                mask = mask.astype(np.uint8)

                ret, img_binary = cv2.threshold(mask, 127, 255, 0)

                contours, color_hierachy =cv2.findContours(img_binary.copy(),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
                max_area = 0
                area_threshold = 5000
                max_cnt = 0
                for cnt in contours:
                   M = cv2.moments(cnt)
                   if max_area < M['m00']: 
                       max_area = M['m00']
                       max_cnt = cnt
                c0 = max_cnt
                c0 = np.reshape(max_cnt,(-1,2))
             
                c0_x= c0[:,0]

                c0_y= c0[:,1]
                #print(c0_x)
                center[0] = np.mean(c0_x)
                center[1] = np.mean(c0_y)

                convert_data_ = convert_2d_2d(int(center[0]),int(center[1]))
                convert_data=convert_2d_3d(int(convert_data_[0]),int(convert_data_[1]))
                convert_x = -1*convert_data[0]/1000
                convert_y = -1*convert_data[1]/1000
                convert_z = convert_data[2]/1000

                tck, u = splprep([c0_x,c0_y], s =0, per=True)

                u_new = np.linspace(u.min(), u.max(), 100)

                x_new, y_new = splev(u_new, tck)

                tck, u = splprep([x_new, y_new], s =0, per=True)

                u_new = np.linspace(u.min(), u.max(), 100)

                x_new, y_new = splev(u_new, tck)

                cx_new = np.mean(x_new)

                cy_new = np.mean(y_new)

                res_array =np.zeros((100,2),dtype=int)

                res_array[:,0] = np.array(np.transpose(x_new),dtype=int)

                res_array[:,1] = np.array(np.transpose(y_new),dtype=int)

                c0_=np.reshape(res_array,(1,-1,2))  

                pysot_contour_img = cv2.drawContours(color_img.copy(), c0_, -1, (0,255,0), 2)

 

                mask[mask == 255] = 1

 

                prev_mask = mask.copy()

                #print(mask.shape)

                pysot_img[mask>0] = pysot_img[mask>0] * 0.3 + color_mask * 0.7 

                pysot_mask[mask>0] = 255

 

 

              #pysot_img = cv2.addWeighted(pysot_img, 0.77, mask, 0.23, -1)

       else:

                bbox = list(map(int, outputs['bbox']))

 

                color_mask = np.random.randint(0, 256, (1, 3), dtype=np.uint8)

 

                pysot_img = pysot_img[prev_mask>0] = pysot_img[prev_mask>0] * 0.5 + color_mask * 0.5 

 

                cv2.rectangle(pysot_img, (bbox[0], bbox[1]),

                              (bbox[0]+bbox[2], bbox[1]+bbox[3]),

                              (0, 255, 0), 3)

                

       prev_pysot_img = pysot_img.copy()
       print("--- pysot %s seconds ---" % (time.time() - start_time))
       #print(outputs)

     except Exception:
       print('PYSOT  ERROR:  '+traceback.format_exc())     
       try:

         color_mask = np.random.randint(0, 256, (1, 3), dtype=np.uint8)

         pysot_img[prev_mask>0] = pysot_img[prev_mask>0] * 0.5 + color_mask * 0.5 


       except:

         pass
     

       time.sleep(0.01)

       print("no init")

if __name__ == '__main__':

    t1 = threading.Thread(target=detect_img)

    t1.start()

    t2 = threading.Thread(target=run_maskrcnn)

    t2.start()

    t3 = threading.Thread(target=run_pysot)

    t3.start()
    t4 = threading.Thread(target=calc)

    t4.start()
