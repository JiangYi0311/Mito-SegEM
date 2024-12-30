import numpy as np
from tqdm import tqdm
import fastremap
import os, h5py
import pandas as pd
from collections import Counter



def dict_merge(dict1, dict2):
    return dict(Counter(dict1) + Counter(dict2))


def h5_to_csv(path, save_path, voxel_size_in_um3):
    filename = sorted(os.listdir(path))
    dict_id_count = {}
    for name in tqdm(filename):
        f = h5py.File(os.path.join(path, name), 'r')
        slice_data = f['data'][:]
        id_counts_per = {}
        uniques, counts = fastremap.unique(slice_data, return_counts=True)
        for _id, count in zip(uniques, counts):
            if _id == 0:
                continue
            id_counts_per[_id] = count
        dict_id_count = dict_merge(dict_id_count, id_counts_per)
    for key in dict_id_count:
        dict_id_count[key] *= voxel_size_in_um3
    print("mito number:", len(dict_id_count))
    df_0 = pd.DataFrame(dict_id_count.items(), columns=["id", "volume(um3)"])
    df_0.to_csv(save_path, index=False)


if __name__ == "__main__":

    # all h5 file to acquire id and volume #####
    path = ""  # serail h5 file
    save_path = ""
    os.makedirs(save_path, exist_ok=True)
    save_path_csv = os.path.join(save_path, 'mito_id_volume_Ribbon.csv')
    voxel_size = [12, 12, 50]
    voxel_size_in_um3 = np.prod(voxel_size)/(1000**3)  # nm --> um
    h5_to_csv(path, save_path_csv, voxel_size_in_um3)
