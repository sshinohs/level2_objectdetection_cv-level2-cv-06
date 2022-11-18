import streamlit as st
import cv2
import json
import os
import numpy as np
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
from pycocotools.coco import COCO
from collections import defaultdict
from typing import List, Tuple

CLASSES = [
    "General trash",
    "Paper",
    "Paper pack",
    "Metal",
    "Glass",
    "Plastic",
    "Styrofoam",
    "Plastic bag",
    "Battery",
    "Clothing",
]
RED_COLOR = (255, 0, 0)
LINE_WEIGHT = 2


def set_data() -> pd.DataFrame:
    coco = COCO("../dataset/train.json")

    df = pd.DataFrame()

    image_ids = []
    class_name = []
    class_id = []
    x_min = []
    y_min = []
    x_max = []
    y_max = []

    for image_id in coco.getImgIds():

        image_info = coco.loadImgs(image_id)[0]
        ann_ids = coco.getAnnIds(imgIds=image_info["id"])
        anns = coco.loadAnns(ann_ids)

        file_name = image_info["file_name"]

        for ann in anns:
            image_ids.append(file_name)
            class_name.append(CLASSES[ann["category_id"]])
            class_id.append(ann["category_id"])
            x_min.append(float(ann["bbox"][0]))
            y_min.append(float(ann["bbox"][1]))
            x_max.append(float(ann["bbox"][0]) + float(ann["bbox"][2]))
            y_max.append(float(ann["bbox"][1]) + float(ann["bbox"][3]))

    df["image_id"] = image_ids
    df["class_name"] = class_name
    df["class_id"] = class_id
    df["x_min"] = x_min
    df["y_min"] = y_min
    df["x_max"] = x_max
    df["y_max"] = y_max
    return df


def make_checkbox(class_list: List[str], id_list: List[int]) -> List[bool]:
    check_boxes = st.columns(5)
    return_list = [False] * len(class_list)
    for idx, (class_name, class_id) in enumerate(zip(class_list, id_list)):
        with check_boxes[idx % 5]:
            check = st.checkbox(class_name, value=True)
        return_list[class_id] = check
    return return_list


def get_bbox(img_group: pd.DataFrame) -> List[list]:
    bboxes = []
    for idx, row in img_group.iterrows():
        c_id, x_min, y_min, x_max, y_max = (
            row.class_id,
            row.x_min,
            row.y_min,
            row.x_max,
            row.y_max,
        )
        bboxes.append([c_id, x_min, y_min, x_max, y_max])
    return bboxes


def draw_bbox(img: np.array, bboxes: List[list], check_list: List[bool]) -> np.array:
    for bbox in bboxes:
        c_id, x_min, y_min, x_max, y_max = map(int, bbox)
        if check_list[c_id]:
            img = cv2.rectangle(
                img, (x_min, y_min), (x_max, y_max), RED_COLOR, LINE_WEIGHT
            )
    return img


def make_vz_tab(df: pd.DataFrame):
    """
    사진 한 장씩 선택해서 원하는 카테고리의 bbox를 선택해서 볼 수 있는 탭
    """
    st.header("Data Analysis")

    group = df.groupby("image_id")
    img_paths = group.groups.keys()

    img_path = st.selectbox("choose image", img_paths)

    check_list = make_checkbox(
        class_list=df.class_name.unique().tolist(),
        id_list=df.class_id.unique().tolist(),
    )

    st.write(f"img_path: {img_path}")

    img = cv2.imread(os.path.join("../dataset/", img_path))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    bboxes = get_bbox(group.get_group(img_path))
    img = draw_bbox(img, bboxes, check_list)

    st.image(img)


def make_category_count_tab(df: pd.DataFrame):
    """
    카테고리 별 bbox 갯수 시각화
    """
    st.header("category_count")
    fig = plt.figure(figsize=(12, 8))
    sns.countplot(x=df.class_name)
    st.pyplot(fig)


def make_bbox_count_tab(df: pd.DataFrame):
    """
    이미지 별 bbox 갯수 시각화
    """

    coco = COCO("../dataset/train.json")
    nums = []
    max_bbox = 0
    max_img = 0
    for image_id in coco.getImgIds():
        image_info = coco.loadImgs(image_id)[0]
        ann_ids = coco.getAnnIds(imgIds=image_info["id"])
        anns = coco.loadAnns(ann_ids)
        if len(anns) > max_bbox:
            max_img = image_id
            max_bbox = len(anns)
        nums.append(len(anns))
    fig = plt.figure(figsize=(12, 8))
    plt.hist(nums, bins=70)
    plt.title("total_distribution")
    plt.xlabel("bbox_num")
    plt.ylabel("image_num")

    dic = dict()
    for num in nums:
        if num not in dic.keys():
            dic[num] = 1
        else:
            dic[num] += 1

    mode = sorted(dic.items(), key=lambda x: x[1])[-1][0]

    st.pyplot(fig)
    st.write(f"max_bbox_num: {max(nums)}")
    st.write(f"min_bbox_num: {min(nums)}")
    st.write(f"mode_bbox_num: {mode}")
    st.write(f"max_bbox_img: {max_img}")

    fig = plt.figure(figsize=(12, 8))
    plt.hist(nums, bins=20, range=(0, 21))
    plt.title("1~20_distribution")
    plt.xlabel("bbox_num")
    plt.ylabel("image_num")
    st.pyplot(fig)

    fig = plt.figure(figsize=(12, 8))
    plt.hist(nums, bins=50, range=(21, max(nums)))
    plt.title("over21_distribution")
    plt.xlabel("bbox_num")
    plt.ylabel("image_num")
    st.pyplot(fig)


# 박스 크기

# 사진별 카테고리 포함 여부 분포

#

# 실행 명령어 streamlit run data_vz.py  --server.fileWatcherType none --server.port 30004
st.title("Data Visualization")
vz_tab, count_tab, bbox_count_tab = st.tabs(["analysis", "count", "bbox_count"])
df = set_data()
with vz_tab:
    make_vz_tab(df)
with count_tab:
    make_category_count_tab(df)
with bbox_count_tab:
    make_bbox_count_tab(df)

# if __name__ == '__main__':
#     run()
