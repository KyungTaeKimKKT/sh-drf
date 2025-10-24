import os
import glob
import cv2
import random
import shutil

# CNN gray dataset root
CNN_DATASET_ROOT = "/home/kkt/development/proj/intranet_sh/shapi/media/ai/cnn_gray"
YOLO_DATASET_ROOT = "/home/kkt/development/proj/intranet_sh/shapi/media/ai/yolo_gray"

IMG_DIR = os.path.join(YOLO_DATASET_ROOT, "images/train")
LBL_DIR = os.path.join(YOLO_DATASET_ROOT, "labels/train")

os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(LBL_DIR, exist_ok=True)

# YOLO format: class x_center y_center width height (normalized)
def convert_cnn_to_yolo():
    digit_dirs = [d for d in os.listdir(CNN_DATASET_ROOT) if os.path.isdir(os.path.join(CNN_DATASET_ROOT, d))]

    for digit in digit_dirs:
        digit_path = os.path.join(CNN_DATASET_ROOT, digit)
        img_files = glob.glob(os.path.join(digit_path, "*.jpg"))

        for idx, img_path in enumerate(img_files):
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                print(f"[WARN] Cannot read {img_path}")
                continue

            # YOLO는 기본적으로 RGB 기대, gray -> 3채널 복제
            img_yolo = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

            h, w = img.shape
            # bounding box: 전체 이미지 영역
            x_center = 0.5
            y_center = 0.5
            width = 1.0
            height = 1.0

            # 저장할 파일 이름
            filename = f"{digit}_{idx:04d}.jpg"
            img_save_path = os.path.join(IMG_DIR, filename)
            lbl_save_path = os.path.join(LBL_DIR, filename.replace(".jpg", ".txt"))

            cv2.imwrite(img_save_path, img_yolo)

            with open(lbl_save_path, "w") as f:
                f.write(f"{digit} {x_center} {y_center} {width} {height}\n")

    print("[DONE] CNN gray dataset → YOLO format conversion finished.")


def auto_devide_to_val( dst_root:str=YOLO_DATASET_ROOT, ratio:float=0.2):
    """
    YOLO dataset (images/, labels/)을 train/val로 자동 분리
    src_img_dir: YOLO 변환된 이미지 디렉토리
    src_lbl_dir: YOLO 변환된 라벨 디렉토리
    dst_root: 저장될 YOLO dataset root (train/val 폴더 생성)
    ratio: val 비율 (default 0.2 → 8:2 split)
    """
    src_img_dir = os.path.join(dst_root, "images/src")
    src_lbl_dir = os.path.join(dst_root, "labels/src")

    img_train = os.path.join(dst_root, "images/train")
    img_val   = os.path.join(dst_root, "images/val")
    lbl_train = os.path.join(dst_root, "labels/train")
    lbl_val   = os.path.join(dst_root, "labels/val")

    for d in [img_train, img_val, lbl_train, lbl_val]:
        os.makedirs(d, exist_ok=True)

    img_files = glob.glob(os.path.join(src_img_dir, "*.jpg"))
    random.shuffle(img_files)

    val_size = int(len(img_files) * ratio)
    val_files = img_files[:val_size]
    train_files = img_files[val_size:]

    def copy_files(files, img_dst, lbl_dst):
        for img_path in files:
            base = os.path.basename(img_path)
            lbl_path = os.path.join(src_lbl_dir, base.replace(".jpg", ".txt"))
            if not os.path.exists(lbl_path):
                continue
            shutil.copy(img_path, os.path.join(img_dst, base))
            shutil.copy(lbl_path, os.path.join(lbl_dst, base.replace(".jpg", ".txt")))

    copy_files(train_files, img_train, lbl_train)
    copy_files(val_files, img_val, lbl_val)

    print(f"[DONE] Train: {len(train_files)}, Val: {len(val_files)}")

#### from scheduler_job.jobs.cnn_to_yolo_dataset import convert_cnn_to_yolo
#### convert_cnn_to_yolo()