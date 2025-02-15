# --------------------------------------------------------
# Pytorch Multi-GPU Faster R-CNN
# Licensed under The MIT License [see LICENSE for details]
# Written by Jiasen Lu, Jianwei Yang, based on code from Ross Girshick
# --------------------------------------------------------
from __future__ import absolute_import, division, print_function

import os
import pdb
import pickle
import pprint
import sys
import time

import _init_paths
import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from model.faster_rcnn.resnet      import resnet
from model.faster_rcnn.vgg16       import vgg16
# from model.nms.nms_wrapper       import nms
from model.roi_layers              import nms
from model.rpn.bbox_transform      import bbox_transform_inv, clip_boxes
from model.utils.config            import cfg, cfg_from_file, cfg_from_list, get_output_dir
from model.utils.net_utils         import save_net, load_net, vis_detections
from parse                         import parse_args_test
from roi_data_layer.roibatchLoader import roibatchLoader
from roi_data_layer.roidb          import combined_roidb
from torch.autograd                import Variable

try:
	xrange          # Python 2
except NameError:
	xrange = range  # Python 3


lr           = cfg.TRAIN.LEARNING_RATE
momentum     = cfg.TRAIN.MOMENTUM
weight_decay = cfg.TRAIN.WEIGHT_DECAY


if __name__ == '__main__':
	# torch.set_num_threads(1)
	args = parse_args_test()

	print('Called with args:')
	print(args)

	if args.dataset == "cityscape":
		args.t_imdbtest_name = "cityscape_2007_test"
		args.set_cfgs = [
			"ANCHOR_SCALES",
			"[8,16,32]",
			"ANCHOR_RATIOS",
			"[0.5,1,2]",
			"MAX_NUM_GT_BOXES",
			"30",
		]
	elif args.dataset == "clipart":
		args.t_imdbtest_name = "clipart_trainval"
		args.set_cfgs = [
			"ANCHOR_SCALES",
			"[8,16,32]",
			"ANCHOR_RATIOS",
			"[0.5,1,2]",
			"MAX_NUM_GT_BOXES",
			"20",
		]
	if args.dataset == "kitti2cityscape":
		args.t_imdbtest_name = "cityscape_car_2007_test_s"
		args.set_cfgs = [
			"ANCHOR_SCALES",
			"[8,16,32]",
			"ANCHOR_RATIOS",
			"[0.5,1,2]",
			"MAX_NUM_GT_BOXES",
			"20",
		]
	elif args.dataset == "wolves":
		args.t_imdbtest_name = "park2_test"
		args.set_cfgs = [
			"ANCHOR_SCALES",
			"[8, 16, 32]",
			"ANCHOR_RATIOS",
			"[0.5,1,2]",
			"MAX_NUM_GT_BOXES",
			"2",
		]
	else:
		print('Undefined Dataset')

	args.cfg_file = (
		"cfgs/{}_ls.yml".format(args.net)
		if args.large_scale
		else "cfgs/{}.yml".format(args.net)
	)

	if args.cfg_file is not None:
		cfg_from_file(args.cfg_file)
	if args.set_cfgs is not None:
		cfg_from_list(args.set_cfgs)

	print('Using config:')
	pprint.pprint(cfg)
	np.random.seed(cfg.RNG_SEED)

	if torch.cuda.is_available() and not args.cuda:
		print("WARNING: You have a CUDA device, so you should probably run with --cuda")

	cfg.TRAIN.USE_FLIPPED = False
	imdb, roidb, ratio_list, ratio_index = combined_roidb(args.t_imdbtest_name, False)
	imdb.competition_mode(on=True)
	print(f'{len(roidb)} roidb entries')

	load_name = args.model_dir

	# initilize the network here.
	if args.net == 'vgg16':
		fasterRCNN = vgg16(
			imdb.classes, 
			pretrained=False,
			class_agnostic=args.class_agnostic,
			context=args.context,
			num_aux1=args.num_aux1, num_aux2=args.num_aux2)
	elif args.net == 'res101':
		fasterRCNN = resnet(imdb.classes, 101, pretrained=True,
							class_agnostic=args.class_agnostic,
							context=args.context,
							num_aux1=args.num_aux1, num_aux2=args.num_aux2)
	else:
		print('Undefined Network')

	fasterRCNN.create_architecture()

	print(f"load checkpoint {load_name}")
	checkpoint = torch.load(load_name)
	fasterRCNN.load_state_dict(       
		{k: v for k, v in checkpoint["model"].items() if k in fasterRCNN.state_dict()},
		strict=False
	)
	# fasterRCNN.load_state_dict(checkpoint['model'])
	if 'pooling_mode' in checkpoint.keys():
		cfg.POOLING_MODE = checkpoint['pooling_mode']

	print('load model successfully!')
	# initilize the tensor holder here.
	im_data = torch.FloatTensor(1)
	im_info = torch.FloatTensor(1)
	num_boxes = torch.LongTensor(1)
	gt_boxes = torch.FloatTensor(1)

	# ship to cuda
	if args.cuda:
		im_data = im_data.cuda()
		im_info = im_info.cuda()
		num_boxes = num_boxes.cuda()
		gt_boxes = gt_boxes.cuda()

	# make variable
	im_data = Variable(im_data)
	im_info = Variable(im_info)
	num_boxes = Variable(num_boxes)
	gt_boxes = Variable(gt_boxes)

	if args.cuda:
		cfg.CUDA = True

	if args.cuda:
		fasterRCNN.cuda()

	start = time.time()
	max_per_image = 100

	vis = True

	if vis:
		thresh = 0.05
	else:
		thresh = -0.1
	thresh = 0.0
	save_name = args.model_dir.split("/")[-1]
	num_images = len(imdb.image_index)
	all_boxes = [[[] for _ in xrange(num_images)] for _ in xrange(imdb.num_classes)]

	output_dir = get_output_dir(imdb, save_name)
	dataset = roibatchLoader(
		roidb, 
		ratio_list, 
		ratio_index, 
		1,
		imdb.num_classes, 
		training=False, 
		normalize=False
	)

	dataloader = torch.utils.data.DataLoader(
		dataset, 
		batch_size=1,
		shuffle=False, 
		num_workers=0,
		pin_memory=True
	)

	data_iter = iter(dataloader)

	_t = {'im_detect': time.time(), 'misc': time.time()}
	det_file = os.path.join(output_dir, 'detections.pkl')

	fasterRCNN.eval()
	empty_array = np.transpose(np.array([[], [], [], [], []]), (1, 0))
	for i in range(num_images):

		data = next(data_iter)
		with torch.no_grad():
			im_data.resize_(data[0].size()).copy_(data[0])
			im_info.resize_(data[1].size()).copy_(data[1])
			gt_boxes.resize_(data[2].size()).copy_(data[2])
			num_boxes.resize_(data[3].size()).copy_(data[3])

		det_tic = time.time()
		(
			rois,
			cls_prob,
			bbox_pred,
			rpn_loss_cls,
			rpn_loss_box,
			RCNN_loss_cls,
			RCNN_loss_bbox, _, _, _, _, _, _, _
		) = fasterRCNN(im_data, im_info, gt_boxes, num_boxes)
		scores = cls_prob.data
		boxes = rois.data[:, :, 1:5]
		if cfg.TEST.BBOX_REG:
			# Apply bounding-box regression deltas
			box_deltas = bbox_pred.data
			if cfg.TRAIN.BBOX_NORMALIZE_TARGETS_PRECOMPUTED:
				# Optionally normalize targets by a precomputed mean and stdev
				if args.class_agnostic:
					box_deltas = (
						box_deltas.view(-1, 4)
						* torch.FloatTensor(cfg.TRAIN.BBOX_NORMALIZE_STDS).cuda()
						+ torch.FloatTensor(cfg.TRAIN.BBOX_NORMALIZE_MEANS).cuda()
					)
					box_deltas = box_deltas.view(1, -1, 4)
				else:
					box_deltas = (
						box_deltas.view(-1, 4)
						* torch.FloatTensor(cfg.TRAIN.BBOX_NORMALIZE_STDS).cuda()
						+ torch.FloatTensor(cfg.TRAIN.BBOX_NORMALIZE_MEANS).cuda()
					)
					box_deltas = box_deltas.view(1, -1, 4 * len(imdb.classes))

			pred_boxes = bbox_transform_inv(boxes, box_deltas, 1)
			pred_boxes = clip_boxes(pred_boxes, im_info.data, 1)
		else:
			# Simply repeat the boxes, once for each class
			pred_boxes = np.tile(boxes, (1, scores.shape[1]))

		pred_boxes /= data[1][0][2].item()

		scores = scores.squeeze()
		pred_boxes = pred_boxes.squeeze()
		det_toc = time.time()
		detect_time = det_toc - det_tic
		misc_tic = time.time()
		if vis:
			im = cv2.imread(imdb.image_path_at(i))
			im2show = np.copy(im)
		for j in xrange(1, imdb.num_classes):
			inds = torch.nonzero(scores[:, j] >= 0).view(-1)
			print(inds.shape)
			# if there is det
			if inds.numel() >= 0:
				cls_scores = scores[:, j][inds]
				print(cls_scores.shape)
				_, order = torch.sort(cls_scores, 0, True)
				if args.class_agnostic:
					cls_boxes = pred_boxes[inds, :]
				else:
					cls_boxes = pred_boxes[inds][:, j * 4:(j + 1) * 4]

				cls_dets = torch.cat((cls_boxes, cls_scores.unsqueeze(1)), 1)
				# cls_dets = torch.cat((cls_boxes, cls_scores), 1)
				cls_dets = cls_dets[order]
				keep = nms(cls_boxes[order, :], cls_scores[order], 1)
				cls_dets = cls_dets[keep.view(-1).long()]
				print(cls_dets.shape)
				print(imdb.classes[j])
				if vis:
					im2show = vis_detections(
						im2show, imdb.classes[j], cls_dets.cpu().numpy(), 0.0
					)
				all_boxes[j][i] = cls_dets.cpu().numpy()
			else:
				all_boxes[j][i] = empty_array

		# Limit to max_per_image detections *over all classes*
		max_per_image=301
		if max_per_image > 0:
			image_scores = np.hstack(
				[all_boxes[j][i][:, -1] for j in xrange(1, imdb.num_classes)]
			)
			if len(image_scores) > max_per_image:
				image_thresh = np.sort(image_scores)[-max_per_image]
				for j in xrange(1, imdb.num_classes):
					keep = np.where(all_boxes[j][i][:, -1] >= image_thresh)[0]
					all_boxes[j][i] = all_boxes[j][i][keep, :]

		misc_toc = time.time()
		nms_time = misc_toc - misc_tic

		sys.stdout.write(
			"im_detect: {:d}/{:d} {:.3f}s {:.3f}s   \r".format(
				i + 1, num_images, detect_time, nms_time
			)
		)
		sys.stdout.flush()

		if vis:
			cv2.imwrite('output/images/result' + str(i) + '.png', im2show)
			# pdb.set_trace()
			# cv2.imshow('test', im2show)
			# cv2.waitKey(0)

	with open(det_file, 'wb') as f:
		pickle.dump(all_boxes, f, pickle.HIGHEST_PROTOCOL)

	print('Evaluating detections')
	imdb.evaluate_detections(all_boxes, output_dir)

	end = time.time()
	print("test time: %0.4fs" % (end - start))
