import os
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
import webknossos as wk
import h5py
import numpy as np
from tqdm import tqdm
import zarr
import time
import cv2


def read_h5_data(path):
    filename = sorted(os.listdir(path))
    N = len(filename)
    with h5py.File(os.path.join(path, filename[-1]), 'r') as f:
        for key in f.keys():
            img = np.array(f[key])
            h, w = img.shape
            id_max = int(np.max(img))
            # print(type(id_max))
            print(id_max)
    
    time_1 = time.perf_counter()
    print("#####creat empty data and read data#####")
    volume_stack = zarr.zeros((w, h, N), chunks=(-1, -1, 1), dtype=np.uint32)
    print(volume_stack.dtype)
    print(volume_stack.chunks)
    for i, name in tqdm(enumerate(filename)):
        with h5py.File(os.path.join(path, name), 'r') as f:
            for key in f.keys():
                img = np.array(f[key]).astype(np.uint32)
                volume_stack[:, :, i] = img.T
    time_2 = time.perf_counter()
    print("data read time:", time_2-time_1)
    return volume_stack, id_max, np.uint32


def read_png_data(path):
    filename = sorted(os.listdir(path))
    N = len(filename)
    img = Image.open(os.path.join(path, filename[-1]))
    w, h = img.size
    id_max = int(np.max(np.asarray(img)))
     
    time_1 = time.perf_counter()
    print("#####creat empty data and read data#####")
    volume_stack = zarr.zeros((w, h, N), chunks=(-1, -1, 1), dtype=np.uint16)
    print(volume_stack.dtype)
    print(volume_stack.chunks)
    for i, name in tqdm(enumerate(filename)):
        img = cv2.imread(os.path.join(path, name), -1)
        volume_stack[:, :, i] = img.T
    time_2 = time.perf_counter()
    print("data read time:", time_2-time_1)
    return volume_stack, id_max, np.uint16     


def read_rawtif_data(path):
    filename = sorted(os.listdir(path))
    N = len(filename)
    img = Image.open(os.path.join(path, filename[-1]))
    w, h = img.size
    id_max = int(np.max(np.asarray(img)))
     
    time_1 = time.perf_counter()
    print("#####creat empty data and read data#####")
    volume_stack = zarr.zeros((w, h, N), chunks=(-1, -1, 1), dtype=np.uint8)
    print(volume_stack.dtype)
    print(volume_stack.chunks)
    for i, name in tqdm(enumerate(filename)):
        img = cv2.imread(os.path.join(path, name), -1)
        volume_stack[:, :, i] = img.T
    time_2 = time.perf_counter()
    print("data read time:", time_2-time_1)
    return volume_stack, id_max, np.uint8


def data_generate_wk(path, save_path, voxel_size, offset, whether_h5=True, whether_segmentation=True):
    os.makedirs(save_path, exist_ok=True)
    if whether_segmentation is True:
        if whether_h5 is True:
            volume_stack, id_max, data_type = read_h5_data(path)
        else:
            volume_stack, id_max, data_type = read_png_data(path)
    else:
        volume_stack, id_max, data_type = read_rawtif_data(path)
    time_1 = time.perf_counter()
    print("#####start wk#####")
    dataset = wk.Dataset(os.path.join(save_path, "my_dataset"), voxel_size=voxel_size)
    # dataset = wk.Dataset.open("existing_dataset")
    if whether_segmentation is True:
        layer = dataset.add_layer("segmentation", wk.SEGMENTATION_CATEGORY, dtype_per_channel=data_type, largest_segment_id=id_max)
    else:
        layer = dataset.add_layer("color", wk.COLOR_CATEGORY, dtype_per_channel=data_type)
    mag1 = layer.add_mag("1", compress=True)
    mag1.write(absolute_offset=offset, data=volume_stack)
    time_2 = time.perf_counter()
    print("wk time:", time_2-time_1)
    layer.downsample(sampling_mode='anisotropic')


if __name__ == "__main__":
    path = ""  # serial images path
    save_path = ""  # wk save path
    whether_h5 = False  # h5 == True, png == False
    whether_segmentation = True  # segmentaion == True, color == False
    voxel_size = (12, 12, 50)  # voxel size
    offset = (0, 0, 0)  # position(coordinate) of dataset in webknossos
    data_generate_wk(path, save_path, voxel_size, offset, whether_h5, whether_segmentation)