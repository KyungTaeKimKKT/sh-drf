import os
import cv2
import glob
import shutil
from sklearn.model_selection import train_test_split
import random

# 경로 설정
YOLO_CROPS_DIR = "/home/kkt/development/proj/intranet_sh/shapi/media/yolo/crops"  # YOLO로 crop한 이미지 폴더
CNN_IMG_RGB_DIR = "/home/kkt/development/proj/intranet_sh/shapi/media/cnn/images_rgb"
CNN_IMG_GRAY_DIR = "/home/kkt/development/proj/intranet_sh/shapi/media/cnn/images_gray"
CNN_LBL_RGB_DIR = "/home/kkt/development/proj/intranet_sh/shapi/media/cnn/labels_rgb"
CNN_LBL_GRAY_DIR = "/home/kkt/development/proj/intranet_sh/shapi/media/cnn/labels_gray"

os.makedirs(CNN_IMG_RGB_DIR, exist_ok=True)
os.makedirs(CNN_IMG_GRAY_DIR, exist_ok=True)
os.makedirs(CNN_LBL_RGB_DIR, exist_ok=True)
os.makedirs(CNN_LBL_GRAY_DIR, exist_ok=True)

TARGET_SIZE = (64, 64)  # CNN 입력 크기
MAX_PER_DIGIT = 1000

def pipeline_yolo_to_cnn_with_rgb():
    # YOLO crop 이미지 예: 2_0001_20250826_123456.jpg
    img_files = glob.glob(os.path.join(YOLO_CROPS_DIR, "*.jpg"))
    digit_map = {}
    for img_path in img_files:
        filename = os.path.basename(img_path)
        # digit 확인
        digit = filename.split("_")[0]
        digit_map.setdefault(digit, []).append(img_path)

    # digit별 최대 1000개만 선택
    final_list = []
    for digit, imgs in digit_map.items():
        if len(imgs) > MAX_PER_DIGIT:
            imgs = random.sample(imgs, MAX_PER_DIGIT)
        final_list.extend(imgs)

    for img_path in final_list:
        filename = os.path.basename(img_path)
        digit = filename.split("_")[0]

        img = cv2.imread(img_path)
        if img is None:
            print(f"[WARN] Cannot read {img_path}")
            continue

        img_resized = cv2.resize(img, TARGET_SIZE)

        # RGB로 저장
        new_img_name = f"{digit}_{filename}"
        cv2.imwrite(os.path.join(CNN_IMG_RGB_DIR, new_img_name), img_resized)

        # 라벨 저장
        with open(os.path.join(CNN_LBL_RGB_DIR, new_img_name.replace(".jpg", ".txt")), "w") as f:
            f.write(f"{digit}\n")

    print(f"[DONE] CNN dataset created: {len(final_list)} images")


def pipeline_yolo_to_cnn_with_gray():
    # YOLO crop 이미지 예: 2_0001_20250826_123456.jpg
    img_files = glob.glob(os.path.join(YOLO_CROPS_DIR, "*.jpg"))
    digit_map = {}
    for img_path in img_files:
        filename = os.path.basename(img_path)
        # digit 확인
        digit = filename.split("_")[0]
        digit_map.setdefault(digit, []).append(img_path)

    # digit별 최대 1000개만 선택
    final_list = []
    for digit, imgs in digit_map.items():
        if len(imgs) > MAX_PER_DIGIT:
            imgs = random.sample(imgs, MAX_PER_DIGIT)
        final_list.extend(imgs)

    for img_path in final_list:
        filename = os.path.basename(img_path)
        digit = filename.split("_")[0]

        img = image_처리_bgr_to_gray(cv2.imread(img_path))
        if img is None:
            print(f"[WARN] Cannot read {img_path}")
            continue

        img_resized = cv2.resize(img, TARGET_SIZE)

        # RGB로 저장
        new_img_name = f"{digit}_{filename}"
        cv2.imwrite(os.path.join(CNN_IMG_GRAY_DIR, new_img_name), img_resized)

        # 라벨 저장
        with open(os.path.join(CNN_LBL_GRAY_DIR, new_img_name.replace(".jpg", ".txt")), "w") as f:
            f.write(f"{digit}\n")

    print(f"[DONE] CNN dataset created: {len(final_list)} images")

def image_처리_bgr_to_gray( image):
    설정_gaussianBlur =(15,15)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, 설정_gaussianBlur, 0)
    thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY| cv2.THRESH_OTSU )[1]

    # thresh = cv2.threshold(warped, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (1, 5))
    final_image = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    return final_image


import cv2
import numpy as np
import random
import shutil
import os

AUG_PER_IMAGE = 2  # 원본 1장당 몇 장 증강할지

def augment_gray_image(img):
    """Gray 이미지 증강"""
    # 1. 랜덤 회전 -5~5도
    angle = random.uniform(-5, 5)
    h, w = img.shape
    M = cv2.getRotationMatrix2D((w/2, h/2), angle, 1.0)
    img = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REPLICATE)

    # 2. 랜덤 밝기 / 대비 조정
    alpha = random.uniform(0.9, 1.1)  # 대비
    beta = random.randint(-10, 10)    # 밝기
    img = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)

    # 3. 가우시안 노이즈 추가
    noise = np.random.normal(0, 5, img.shape).astype(np.uint8)
    img = cv2.add(img, noise)

    return img

def pipeline_gray_augment(
    original_dir:str = CNN_IMG_GRAY_DIR, 
    save_dir:str = CNN_IMG_GRAY_DIR, 
    lbl_dir:str = CNN_LBL_GRAY_DIR
):
    img_files = glob.glob(os.path.join(original_dir, "*.jpg"))
    print(f"[INFO] Found {len(img_files)} images")

    for img_path in img_files:
        filename = os.path.basename(img_path)
        digit = filename.split("_")[0]

        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            print(f"[WARN] Cannot read {img_path}")
            continue

        # 원본 다시 저장 (덮어쓰기)
        cv2.imwrite(os.path.join(save_dir, filename), img)

        # 증강본 생성
        for i in range(AUG_PER_IMAGE):
            aug_img = augment_gray_image(img)
            aug_name = filename.replace(".jpg", f"_aug{i}.jpg")
            cv2.imwrite(os.path.join(save_dir, aug_name), aug_img)

            # 라벨 파일 그대로 복사
            label_src = os.path.join(lbl_dir, filename.replace(".jpg", ".txt"))
            label_dst = os.path.join(lbl_dir, aug_name.replace(".jpg", ".txt"))
            shutil.copy(label_src, label_dst)

    print("[DONE] augmentation finished.")

def pipeline_gray_5_9_augment_new(
    original_dir:str = CNN_IMG_GRAY_DIR, 
    save_dir:str = CNN_IMG_GRAY_DIR, 
    lbl_dir:str = CNN_LBL_GRAY_DIR, 
    qty:int = 2
):
    """5,9 선택적 증강 + segment 강조"""
    img_files = glob.glob(os.path.join(original_dir, "*.jpg"))
    target_digits = ["5", "9"]

    # 기존 증강본 제거
    for f in img_files:
        if "_aug" in f:
            os.remove(f)
            lbl_file = os.path.join(lbl_dir, os.path.basename(f).replace(".jpg", ".txt"))
            if os.path.exists(lbl_file):
                os.remove(lbl_file)

    # 새 증강
    img_files = [f for f in glob.glob(os.path.join(original_dir, "*.jpg"))
                 if os.path.basename(f).split("_")[0] in target_digits]

    for img_path in img_files:
        filename = os.path.basename(img_path)
        digit = filename.split("_")[0]

        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            print(f"[WARN] Cannot read {img_path}")
            continue

        for i in range(qty):
            aug_img = augment_gray_image_5_9(img, digit)
            aug_name = filename.replace(".jpg", f"_aug{i}.jpg")
            cv2.imwrite(os.path.join(save_dir, aug_name), aug_img)

            # 라벨 파일 복사
            label_src = os.path.join(lbl_dir, filename.replace(".jpg", ".txt"))
            label_dst = os.path.join(lbl_dir, aug_name.replace(".jpg", ".txt"))
            shutil.copy(label_src, label_dst)

    print(f"[DONE] 5 & 9 augmentation finished, {qty} per original image.")

def augment_gray_image_5_9(img, digit:str):
    """Gray 이미지 증강"""
    # 1. 랜덤 회전 -5~5도
    angle = random.uniform(-5, 5)
    h, w = img.shape
    M = cv2.getRotationMatrix2D((w/2, h/2), angle, 1.0)
    img = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REPLICATE)

    # 2. 랜덤 밝기 / 대비 조정
    alpha = random.uniform(0.9, 1.1)  # 대비
    beta = random.randint(-10, 10)    # 밝기
    img = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)

    # 3. 가우시안 노이즈 추가
    noise = np.random.normal(0, 5, img.shape).astype(np.uint8)
    img = cv2.add(img, noise)


    SEGMENT_MASKS = {
        "5": (slice(32, 64), slice(0, 16)),  # 왼쪽 하단 영역
        "9": (slice(32, 64), slice(0, 16)),
    }
    ### 왼쪽 하단 segment 강조
    mask_slice = SEGMENT_MASKS.get(digit)
    if mask_slice is None:
        return img.copy()
    
    img_aug = img.copy()
    y_slice, x_slice = mask_slice
    img_aug[y_slice, x_slice] = np.clip(img_aug[y_slice, x_slice] + 60, 0, 255)
    return img_aug



#### from scheduler_job.jobs.CNN_pipeline import pipeline_yolo_to_cnn_with_rgb, pipeline_yolo_to_cnn_with_gray