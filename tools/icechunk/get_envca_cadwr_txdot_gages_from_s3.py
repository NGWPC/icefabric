import os
import shutil
import subprocess

import pandas as pd

GAGE_TYPE_CORRELATION = {"ENVCA": "ENVCA", "CADWR": "CADWR", "USGS": "TXDOT"}

if __name__ == "__main__":
    # This path is in the NGWPC AWS Data account
    conus_root_path = "s3://ngwpc-hydrofabric/2.1/CONUS"
    gage_collection_dir = "data/gage_data/"
    hourly_discharge_final_collection = "data/gage_csv_files"
    if not os.path.exists(gage_collection_dir):
        os.makedirs(gage_collection_dir)
        print("Downloading ENVCA/CADWR/TXDOT gages...")
        with open("data/envca_cadwr_txdot_gages.txt") as file:
            for line in file:
                gage_id = line.strip().split()[0]
                gage_type = line.strip().split()[1]
                print(f"Collecting: {gage_id} ({gage_type})")
                s3_dir_path = f"2.1/CONUS/{gage_id}/*"
                command = [
                    "aws",
                    "s3",
                    "cp",
                    f"{conus_root_path}/{gage_id}",
                    gage_collection_dir,
                    "--recursive",
                ]
                print(" ".join(map(str, command)))
                subprocess.call(command)
    else:
        print("Skipping data retrieval...")
    if not os.path.exists(hourly_discharge_final_collection):
        os.makedirs(hourly_discharge_final_collection)
        print(
            "Collecting list of hourly discharge CSV files - only collecting the latest if there are multiples"
        )
        gage_file_dict = {}
        for root, dirs, files in os.walk(gage_collection_dir):
            dirs.sort()
            for file in files:
                gage_type_fp_portion = root.split("/")[-2]
                gage_type = GAGE_TYPE_CORRELATION[gage_type_fp_portion]
                if file in gage_file_dict:
                    print(f"Found more recent gage collection file: {os.path.join(root, file)}")
                    gage_file_dict.pop(file)
                gage_file_dict[file] = (os.path.join(root, file), gage_type)

        for file, (fp, g_type) in gage_file_dict.items():
            new_file_name = f"{g_type}_{file}"
            shutil.copy(fp, os.path.join(hourly_discharge_final_collection, new_file_name))
    else:
        print("Skipping data consolidation...")
    if not os.path.exists("envca_cadwr_txdot.zarr"):
        csv_files = [file for file in os.listdir(hourly_discharge_final_collection) if file.endswith(".csv")]

        # Read and concatenate all CSV files into a single DataFrame
        dataframes = []
        for file in csv_files:
            gage_type, gage_id = file.split("_")[0], file.split("_")[1]
            df = pd.read_csv(os.path.join(hourly_discharge_final_collection, file), header=0).assign(
                id=gage_id, gage_type=gage_type
            )
            dataframes.append(df)
        combined_df = pd.concat(dataframes, ignore_index=True, axis=0)
        combined_df["dateTime"] = pd.to_datetime(
            combined_df["dateTime"], format="mixed", utc=True
        ).dt.tz_localize(None)
        combined_df.rename(columns={"dateTime": "time"}, inplace=True)
        combined_df.set_index(["id", "time"], inplace=True)

        print("Converting to xarray dataset...")
        dataset = combined_df.to_xarray()
        dataset.coords["id"] = dataset.coords["id"].astype(str)
        dataset["gage_type"] = dataset["gage_type"].astype(str)

        print("Saving to zarr store...")
        dataset.to_zarr("envca_cadwr_txdot.zarr", mode="w")

        print("CSV files have been successfully combined into a Zarr store!")
    else:
        print("Zarr store already exists - skipping CSV consolidation/conversion...")
