_base_ = ["mmpose::_base_/default_runtime.py"]
work_dir = "runs/CV_split0/hrnetw48_udp_b16_lr5e-4-210e_CV_split0_256x192"

# runtime
train_cfg = dict(max_epochs=210, val_interval=1)

# optimizer
optim_wrapper = dict(
    optimizer=dict(
        type="Adam",
        lr=5e-4,
    )
)

# learning policy
param_scheduler = [
    dict(
        type="LinearLR", begin=0, end=500, start_factor=0.001, by_epoch=False
    ),  # warm-up
    dict(
        type="MultiStepLR",
        begin=0,
        end=210,
        milestones=[170, 200],
        gamma=0.1,
        by_epoch=True,
    ),
]

visualizer = dict(
    vis_backends=[
        dict(type="LocalVisBackend"),
        dict(type="TensorboardVisBackend"),
    ]
)

# automatically scaling LR based on the actual training batch size
auto_scale_lr = dict(base_batch_size=512)

# hooks
default_hooks = dict(
    checkpoint=dict(save_best="coco/AP", rule="greater", interval=1, max_keep_ckpts=3)
)

# codec settings
codec = dict(type="UDPHeatmap", input_size=(192, 256), heatmap_size=(48, 64), sigma=2)

# model settings
model = dict(
    type="TopdownPoseEstimator",
    data_preprocessor=dict(
        type="PoseDataPreprocessor",
        mean=[123.675, 116.28, 103.53],
        std=[58.395, 57.12, 57.375],
        bgr_to_rgb=True,
    ),
    backbone=dict(
        type="HRNet",
        in_channels=3,
        extra=dict(
            stage1=dict(
                num_modules=1,
                num_branches=1,
                block="BOTTLENECK",
                num_blocks=(4,),
                num_channels=(64,),
            ),
            stage2=dict(
                num_modules=1,
                num_branches=2,
                block="BASIC",
                num_blocks=(4, 4),
                num_channels=(48, 96),
            ),
            stage3=dict(
                num_modules=4,
                num_branches=3,
                block="BASIC",
                num_blocks=(4, 4, 4),
                num_channels=(48, 96, 192),
            ),
            stage4=dict(
                num_modules=3,
                num_branches=4,
                block="BASIC",
                num_blocks=(4, 4, 4, 4),
                num_channels=(48, 96, 192, 384),
            ),
        ),
        init_cfg=dict(
            type="Pretrained",
            checkpoint="https://download.openmmlab.com/mmpose/"
            "pretrain_models/hrnet_w48-8ef0771d.pth",
        ),
    ),
    head=dict(
        type="HeatmapHead",
        in_channels=48,
        out_channels=17,
        deconv_out_channels=None,
        loss=dict(type="KeypointMSELoss", use_target_weight=True),
        decoder=codec,
    ),
    test_cfg=dict(
        flip_test=True,
        flip_mode="heatmap",
        shift_heatmap=False,
    ),
)

# base dataset settings
dataset_type = "PoseTrack18Dataset"
data_mode = "topdown"
data_root = "data/"

# pipelines
train_pipeline = [
    dict(type="LoadImage"),
    dict(type="GetBBoxCenterScale"),
    dict(type="RandomFlip", direction="horizontal"),
    dict(type="RandomHalfBody"),
    dict(type="RandomBBoxTransform"),
    dict(type="TopdownAffine", input_size=codec["input_size"], use_udp=True),
    dict(type="GenerateTarget", encoder=codec),
    dict(type="PackPoseInputs"),
]
val_pipeline = [
    dict(type="LoadImage"),
    dict(type="GetBBoxCenterScale"),
    dict(type="TopdownAffine", input_size=codec["input_size"], use_udp=True),
    dict(type="PackPoseInputs"),
]

# data loaders
train_dataloader = dict(
    batch_size=16,
    num_workers=2,
    persistent_workers=True,
    sampler=dict(type="DefaultSampler", shuffle=True),
    dataset=dict(
        type=dataset_type,
        data_root=data_root,
        data_mode=data_mode,
        ann_file="annotations/CV/split0/train_split0.json",
        data_prefix=dict(img=""),
        pipeline=train_pipeline,
    ),
)
val_dataloader = dict(
    batch_size=16,
    num_workers=2,
    persistent_workers=True,
    drop_last=False,
    sampler=dict(type="DefaultSampler", shuffle=False, round_up=False),
    dataset=dict(
        type=dataset_type,
        data_root=data_root,
        data_mode=data_mode,
        # ann_file="annotations/CV/split0/test_split0.json",
        # since we don't have test annotation at this time, use train instead.
        ann_file="annotations/CV/split0/train_split0.json",
        data_prefix=dict(img=""),
        test_mode=True,
        pipeline=val_pipeline,
    ),
)
test_dataloader = val_dataloader

# evaluators
# val_evaluator = dict(type="CocoMetric", ann_file=data_root + "annotations/CV/split0/test_split0.json", iou_type = "keypoints")
# since we don't have test annotation at this time, use train instead.
val_evaluator = dict(
    type="CocoMetric",
    ann_file=data_root + "annotations/CV/split0/train_split0.json",
    iou_type="keypoints",
)
test_evaluator = val_evaluator
