import collections
import json
import os
import pickle
import re
import warnings

import geopandas
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


class MapData:
    """
    Maps FIM MIP & BLE XS datasets to relevant IDs & categorize by HUC.

    At this time, ensure FIM datasets are saved to local disk.
    """

    def __init__(self, data_dir: str, subfolder_key_prefix: str) -> None:
        self.data_dir = data_dir
        self.subfolder_key_prefix = subfolder_key_prefix

        # Parent directory of the FIM files.
        # Note: All the jsons & geopackages are relevant
        # to map the files to IDs.
        self.fim_data_dirs: list[str] = []

        # List of directories associated with each file type of
        # the FIM data sample (e.g. geopackage of a given model @ HUC#, json,
        # source_models.gpkg, ripple.gpkg)
        self.model_gpkg_dirs: list[str] = []
        self.src_models_gpkg_dirs: list[str] = []
        self.rip_gpkg_dirs: list[str] = []
        self.gpkg_dirs: list[str] = []
        self.json_dirs: list[str] = []
        self.xs_df_list: list[geopandas.GeoDataFrame] = []

        # Variables to be used later
        self.model_gpkg_tablenames: list[str] = []
        self.src_models_gpkg_tablenames: list[str] = []
        self.rip_gpkg_tablenames: list[str] = []
        self.gpkg_tablenames: list[str] = []
        self.json_tablenames: list[str] = []

        self.id2json: dict = collections.defaultdict(dict)
        self.model_id2gpkg: dict = collections.defaultdict(dict)
        self.us_ref_dict: dict = collections.defaultdict(dict)
        self.ds_ref_dict: dict = collections.defaultdict(dict)
        self.rip_huc2gpkg: dict = collections.defaultdict(dict)
        self.groupbyriver_dict: dict = collections.defaultdict(dict)
        self.crs_dict: dict = collections.defaultdict(dict)
        self.consolidated_id2xs: geopandas.GeoDataFrame = geopandas.GeoDataFrame()

        self.read_data_dirs()
        self.cat_data_dirs(self.subfolder_key_prefix)
        self.map_model2huc()
        self.filter_model2huc_map(
            keys_to_drop={"metrics", "low_flow", "high_flow", "eclipsed", "lengths", "coverage"}
        )

        # Generate maps of model_id & HUC # to xs (for both us & ds cross-section)
        # to reach ID & "network_to_id" from each model @ HUC's json file
        self.map_modelhuc_xs2ids()

        # Generate maps of model_id & HUC # to gpkg from each model @ HUC's geopackage
        self.map_model2huc_gpkg()

        # Generate maps of HUC # to ripple gpkg
        self.map_huc2ripple_gpkg()

        # Map IDs to each model's cross-section instance
        self.map_model_xs2ids()

        # [Optional: Per HUC, save each river's set of XS data as geoparquetss & geopackages]
        # self.save_xs_data()

        # Save map of inherited CRS to HUC, model_id, river name
        self.save_crs_map()

        # Consolidated all HEC RAS models' cross-sections featuring IDs
        self.consolidate_id2xs_dfs()

        # Save HEC RAS models' cross-sections consolidated by HUC as geoparquets & geopackages
        # TODO: does this need to be called with a `xs_data_type` ?
        self.save_xsbyhuc_data()

    def read_data_dirs(self) -> None:
        """
        Extract the list of FIM data sample's directories.

        Args:
            None

        Return (list): List of directories associated with each file type of
        the FIM data sample.

        """
        for folder, _subfolders, files in os.walk(self.data_dir):
            if folder != self.data_dir:
                for file in files:
                    self.fim_data_dirs.append(f"{folder}/{file}")

        return

    def cat_data_dirs(self, subfolder_key_prefix: str) -> None:
        """
        Categorize FIM data sample files.

        Args:
            subfolder_key_prefix (str): Prefix of the FIM subfolder's data of interest
                                        Options: 'mip' or 'ble'

        Return: None

        """
        # Extract a list of directories corresponding to each set of files
        for x in self.fim_data_dirs:
            # Covers all HEC-RAS models gpkg featuring 1D model flowlines per HUC (contains reach_id & nwm_to_id
            # for network layer & reaches layer. The rating curves layer only has reach_id. The models layer
            # contains collection_id & model_id)
            if re.search("ripple.gpkg", x):
                self.rip_gpkg_dirs.append(x)
                t = re.search(f"/{subfolder_key_prefix}(.*)", x)
                rip_gpkg_tblname = t.group()  # type: ignore[union-attr]
                self.rip_gpkg_tablenames.append(rip_gpkg_tblname.lstrip("/").replace("/", "_"))

            # Covers all HEC-RAS models gpkg featuring XS per HUC (contains model_id)
            elif (
                not x.endswith("source_models.gpkg")
                and not x.endswith(".json")
                and not re.search("ripple.gpkg", x)
            ):
                self.model_gpkg_dirs.append(x)
                t = re.search(f"/{subfolder_key_prefix}(.*)", x)
                model_gpkg_tblname = t.group()  # type: ignore[union-attr]
                self.model_gpkg_tablenames.append(model_gpkg_tblname.lstrip("/").replace("/", "_"))

            # Covers all HEC-RAS models gpkg featuring 1D model flowlines per HUC (contains model_id & their HEC-RAS 1D model flowlines)
            elif x.endswith("source_models.gpkg"):
                self.src_models_gpkg_dirs.append(x)
                t = re.search(f"/{subfolder_key_prefix}(.*)", x)
                src_models_gpkg_tblname = t.group()  # type: ignore[union-attr]
                self.src_models_gpkg_tablenames.append(src_models_gpkg_tblname.lstrip("/").replace("/", "_"))

            # Covers all HEC-RAS models + Ripple gpkg per HUC
            if x.endswith(".gpkg"):
                self.gpkg_dirs.append(x)
                t = re.search(f"/{subfolder_key_prefix}(.*)", x)
                gpkg_tblname = t.group()  # type: ignore[union-attr]
                self.gpkg_tablenames.append(gpkg_tblname.lstrip("/").replace("/", "_"))

            # Covers each HEC-RAS models' result of conflating its model w/ the NWM network
            elif x.endswith(".json"):
                self.json_dirs.append(x)
                t = re.search(f"/{subfolder_key_prefix}(.*)", x)
                json_tblname = t.group()  # type: ignore[union-attr]
                self.json_tablenames.append(json_tblname.lstrip("/").replace("/", "_"))

        return

    def drop_nested_keys(self, map_dict: dict, keys_to_drop: dict) -> dict | list:
        """
        Drop keys irrelevant for linking each XS to IDs

        Args:
            map_dict (dict): Dictionary to filter

            keys_to_drop (dict): List of keys irrelevant for linking each XS to IDs.

        Return: None

        """
        if isinstance(map_dict, dict):
            return {
                k: self.drop_nested_keys(v, keys_to_drop)
                for k, v in map_dict.items()
                if k not in keys_to_drop
            }
        elif isinstance(map_dict, list):
            return [self.drop_nested_keys(i, keys_to_drop) for i in map_dict]
        else:
            return map_dict

    def map_model2huc(self) -> None:
        """
        Map each conflation json file to their corresponding model ID & HUC #.

        Args:
            None

        Return: None

        """
        for x in self.json_dirs:
            # Note: model_ids found in each src source_models.gpkg is featured is declared as
            # sub-foldername of where model gpkg file resides
            model_id = x.split("/")[-2]
            huc_num = x.split("/")[-4].split("_")[1]
            self.id2json[model_id][huc_num] = {}
            try:
                with open(x) as f:
                    json2dict = json.loads(f.read())
                    self.id2json[model_id][huc_num].update(json2dict)
            except:
                pass

        return

    def filter_model2huc_map(self, keys_to_drop: dict) -> None:
        """
        Extract only relevant keys from model2huc map for linking each XS to a feature ID.

        Args:
            keys_to_drop (dict): List of keys irrelevant for linking each XS to IDs.
                                 (e.g. {'metrics','low_flow', 'high_flow', 'eclipsed',
                                'lengths', 'coverage'})

        Return: None

        """
        self.id2json = self.drop_nested_keys(self.id2json, keys_to_drop)

        return

    def map_modelhuc_xs2ids(self) -> None:
        """
        Parse JSONs & map model_id & HUC # to xs to reach ID & "network_to_id"

        Args:
            None

        Return: None

        Note: Per model @ HUC cross-section layer, the attribute of interest is "river_reach_rs"
        in order to link the IDs to each individual cross-section & their associated xs_id.

        To map each cross-section of a model @ HUC#, there has to be a shared attribute between a
        model @ HUC#'s cross section w/in its XS layer & the details provided within a model @ HUC#'s
        conflation json file.

        - Each conflation json file reveals ...
            -  Per reach, there is a set of cross-sections.
            -  Within each model's cross-section (XS) layers, there are a set of cross-section
            instances - each instance featuring a unique "thalweg" (aka "min_elevation"),
            "xs_max_elevation" (aka "max_elevation"), "reach_id" ("reaches"), & "river_station" (aka "xs_id")

        - Each model @ HUC#'s XS layer contains a collection of cross-section instancees.
        Thus, each unique cross-section w/in a given model @ HUC#'s XS layer will need to be mapped in
        such a way to allow each cross-section to be associated with a feature ID (aka "reach_id" and/or
        "network_to_id").

        - "river_reach_rs" is formatted differently across models' XS layers, however multplie keys
        referenced in the conflation jsons can be referenced to obtain the "river_reach_rs" from the jsons
        As a result, the mapping of IDs to each model's cross-section instance will be based on the info.
        extracted from a model @ HUC#'s conflation.json

        - There can be multiple reach_ids tied to same nwm_to_id (aka "network_to_id).

        """
        # Keys to join values from that makes up the 'river_reach_rs' reflected in each model's XS layer
        keys_to_join = ["river", "reach", "xs_id"]
        for model_id, huc_dict in self.id2json.items():
            for huc_num, reach_dict in huc_dict.items():
                for reach_id, v_dict in reach_dict["reaches"].items():
                    # Joining the attribute because each model's xs layer features three atttrib concat (to be used as reference)
                    if "us_xs" in v_dict:
                        usxs_joined_values = " ".join(str(v_dict["us_xs"][key]) for key in keys_to_join)
                        if "min_elevation" in v_dict["us_xs"]:
                            us_xs_min_elev = v_dict["us_xs"]["min_elevation"]
                        if "max_elevation" in v_dict["us_xs"]:
                            us_xs_max_elev = v_dict["us_xs"]["max_elevation"]

                    if "ds_xs" in v_dict:
                        dsxs_joined_values = " ".join(str(v_dict["ds_xs"][key]) for key in keys_to_join)
                        if "min_elevation" in v_dict["ds_xs"]:
                            ds_xs_min_elev = v_dict["ds_xs"]["min_elevation"]
                        if "max_elevation" in v_dict["ds_xs"]:
                            ds_xs_max_elev = v_dict["ds_xs"]["max_elevation"]

                    if "network_to_id" in v_dict:
                        nwm2id = v_dict["network_to_id"]

                    # Generated maps of model_id & HUC # to xs (for both us & ds cross-section)
                    # to reach ID & "network_to_id"
                    self.us_ref_dict[(model_id, huc_num)].update(
                        {(usxs_joined_values, us_xs_min_elev, us_xs_max_elev): [reach_id, nwm2id]}
                    )
                    self.ds_ref_dict[(model_id, huc_num)].update(
                        {(dsxs_joined_values, ds_xs_min_elev, ds_xs_max_elev): [reach_id, nwm2id]}
                    )

        return

    def map_model2huc_gpkg(self) -> None:
        """
        Map model ID & HUC # to each HEC-RAS model's geopackage.

        Args:
            None

        Return: None

        Note: model_ids found in each source_models.gpkg is featured in last
        sub-foldername of where model gpkg file resides

        """
        # Each HEC-RAS model gpkg per model per HUC
        for x in self.model_gpkg_dirs:
            model_id = x.split("/")[-2]
            huc_num = x.split("/")[-4].split("_")[1]
            self.model_id2gpkg[(model_id, huc_num)] = {"XS": None}
            self.model_id2gpkg[(model_id, huc_num)] = {"XS concave hull": None}
            self.model_id2gpkg[(model_id, huc_num)] = {"River": None}

            try:
                self.model_id2gpkg[(model_id, huc_num)].update(
                    {"XS": geopandas.read_file(x, engine="pyogrio", use_arrow=True, layer="XS")}
                )

                self.model_id2gpkg[(model_id, huc_num)].update(
                    {"River": geopandas.read_file(x, engine="pyogrio", use_arrow=True, layer="River")}
                )
                self.model_id2gpkg[(model_id, huc_num)].update(
                    {
                        "XS concave hull": geopandas.read_file(
                            x, engine="pyogrio", use_arrow=True, layer="XS concave hull"
                        )
                    }
                )
            except:
                pass

        return

    def map_huc2ripple_gpkg(self) -> None:
        """
        Map HUC # to ripple geopackage (features HEC RAS 1D model flowlines).

        Args:
            None

        Return: None

        Note: ripple.gpkg features the HEC RAS 1D model flowlines categorized by HUC #.

        """
        for x in self.rip_gpkg_dirs:
            huc_num = x.split("/")[-2].split("_")[1]
            self.rip_huc2gpkg[huc_num] = {"reaches": None}
            self.rip_huc2gpkg[huc_num] = {"rating curves": None}
            self.rip_huc2gpkg[huc_num] = {"network": None}
            self.rip_huc2gpkg[huc_num] = {"models": None}
            self.rip_huc2gpkg[huc_num] = {"metadata": None}
            self.rip_huc2gpkg[huc_num] = {"rating_curves_no_map": None}
            self.rip_huc2gpkg[huc_num] = {"processing": None}

            try:
                self.rip_huc2gpkg[huc_num].update(
                    {"reaches": geopandas.read_file(x, engine="pyogrio", use_arrow=True, layer="reaches")}
                )
                self.rip_huc2gpkg[huc_num].update(
                    {
                        "rating_curves": geopandas.read_file(
                            x, engine="pyogrio", use_arrow=True, layer="rating_curves"
                        )
                    }
                )
                self.rip_huc2gpkg[huc_num].update(
                    {"network": geopandas.read_file(x, engine="pyogrio", use_arrow=True, layer="network")}
                )
                self.rip_huc2gpkg[huc_num].update(
                    {"models": geopandas.read_file(x, engine="pyogrio", use_arrow=True, layer="models")}
                )
                self.rip_huc2gpkg[huc_num].update(
                    {"metadata": geopandas.read_file(x, engine="pyogrio", use_arrow=True, layer="metadata")}
                )
                self.rip_huc2gpkg[huc_num].update(
                    {
                        "rating_curves_no_map": geopandas.read_file(
                            x, engine="pyogrio", use_arrow=True, layer="rating_curves_no_map"
                        )
                    }
                )
                self.rip_huc2gpkg[huc_num].update(
                    {
                        "processing": geopandas.read_file(
                            x, engine="pyogrio", use_arrow=True, layer="processing"
                        )
                    }
                )
            except:
                pass
        return

    def map_model_xs2ids(self) -> None:
        """
        Map each cross-section instance featured in HEC-RAS model's cross-section layer to their corresponding IDs.

        Args:
            None

        Return: None

        """
        for (model_id, huc_num), model_gpkg_dict in self.model_id2gpkg.items():
            df = model_gpkg_dict["XS"]
            df["huc"] = huc_num
            df["model_id"] = model_id
            array_of_lists = [[None, None] for _ in range(len(df))]
            df["us_ids"] = pd.DataFrame([array_of_lists]).T
            df["ds_ids"] = pd.DataFrame([array_of_lists]).T

            # Covers us_xs
            if (model_id, huc_num) in self.us_ref_dict:
                df["us_ids"] = df.set_index(["river_reach_rs", "thalweg", "xs_max_elevation"]).index.map(
                    self.us_ref_dict[(model_id, huc_num)].get
                )
            else:
                print(
                    f"The model_id @ HUC# ({(model_id, huc_num)}) IS NOT featured in current model @ HUC's conflation json file."
                )
                continue

            # Covers ds_xs
            if (model_id, huc_num) in self.ds_ref_dict:
                df["ds_ids"] = df.set_index(["river_reach_rs", "thalweg", "xs_max_elevation"]).index.map(
                    self.ds_ref_dict[(model_id, huc_num)].get
                )
            else:
                print(
                    f"The model_id @ HUC# ({(model_id, huc_num)}) IS NOT featured in current model @ HUC's conflation json file."
                )
                continue

            # Extracts & appends reach_id & network_to_id to each model @ HUC's unique XS
            # Should the ids not be available in the conflation, must initialize columns
            us_id_df = df["us_ids"].apply(pd.Series)
            if us_id_df.shape[1] == 0:
                us_id_df = pd.DataFrame(np.nan, index=range(us_id_df.shape[0]), columns=[0, 1])
            us_id_df.columns = ["us_reach_id", "us_network_to_id"]

            # Should the ids not be available in the conflation, must initialize columns
            ds_id_df = df["ds_ids"].apply(pd.Series)
            if ds_id_df.shape[1] == 0:
                ds_id_df = pd.DataFrame(np.nan, index=range(ds_id_df.shape[0]), columns=[0, 1])
            ds_id_df.columns = ["ds_reach_id", "ds_network_to_id"]

            # Fill any nan to string
            us_id_df[["us_reach_id", "us_network_to_id"]] = us_id_df[
                ["us_reach_id", "us_network_to_id"]
            ].fillna("None")
            ds_id_df[["ds_reach_id", "ds_network_to_id"]] = ds_id_df[
                ["ds_reach_id", "ds_network_to_id"]
            ].fillna("None")
            df = df.fillna("None")
            df = pd.concat([df, us_id_df, ds_id_df], axis=1)
            df = df.drop(["us_ids", "ds_ids"], axis=1)

            model_gpkg_dict["XS"] = df
            self.xs_df_list.append(model_gpkg_dict["XS"])

        return

    def save_xs_data(self) -> None:
        """
        Consolidate HEC-RAS models cross-sections based on HUC & river & save to storage

        Args:
            None

        Return: None

        Note: These saved parquet files will preserve each river @ HUC's inherited CRS.

        """
        for (model_id, huc_num), _model_gpkg_dict in self.model_id2gpkg.items():
            # Generate data folder per HUC
            if not os.path.exists(f"{os.getcwd()}/xs_data/huc_{huc_num}"):
                os.makedirs(f"{os.getcwd()}/xs_data/huc_{huc_num}")

            # Save each river's geopandas as a geoparquet & geopackage under each HUC folder
            grouped_xslayers = self.model_id2gpkg[(model_id, huc_num)]["XS"].groupby(["river"])
            for river_name in set(self.model_id2gpkg[(model_id, huc_num)]["XS"]["river"]):
                filterbyriver = grouped_xslayers.get_group(river_name)

                # Generate map of each river's set of XS to HUC & model ID to be used as a
                # look-up reference
                self.groupbyriver_dict[huc_num].update({model_id: filterbyriver})

                # Save XS as geoparquet per river per HUC
                filterbyriver.to_parquet(
                    f"{os.getcwd()}/xs_data/huc_{huc_num}/{river_name}.parquet", engine="pyarrow"
                )

                # Save XS as geopackage per river per HUC
                filterbyriver.to_file(f"{os.getcwd()}/xs_data/huc_{huc_num}/{river_name}.gpkg", driver="GPKG")

        return

    def save_crs_map(self) -> None:
        """
        Consolidate HEC-RAS models cross-sections based on HUC & river & save to storage

        Args:
            None

        Return: None

        Note: This saved pickle file will map each river @ HUC's inherited CRS for one to
        analyze & reference.

        """
        for (model_id, huc_num), _model_gpkg_dict in self.model_id2gpkg.items():
            # Generate data folder per HUC
            if not os.path.exists(f"{os.getcwd()}/xs_data/crs_map"):
                os.makedirs(f"{os.getcwd()}/xs_data/crs_map")

            # Generate map of the CRS to each river's geopandas per HUC
            grouped_xslayers = self.model_id2gpkg[(model_id, huc_num)]["XS"].groupby(["river"])
            for river_name in set(self.model_id2gpkg[(model_id, huc_num)]["XS"]["river"]):
                filterbyriver = grouped_xslayers.get_group(river_name)
                self.crs_dict[(huc_num, model_id)].update(
                    {
                        river_name: (
                            f"""ESPG: {
                                str(filterbyriver.crs.to_epsg()) if filterbyriver.crs.to_epsg() else None
                            }, {filterbyriver.crs.name},"""
                        )
                    }
                )

        # Save map of inherited CRS to HUC, model_id, river name
        with open(f"{os.getcwd()}/xs_data/crs_map/crs_mapping.pickle", "wb") as handle:
            pickle.dump(self.crs_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

        return

    def consolidate_id2xs_dfs(self) -> None:
        """
        Consolidate HEC-RAS models cross-sections featuring their corresponding IDs.

        Args:
            None

        Return: None

        Note: A set CRS standard is needed in order to consolidates all XS layers of all models
        under a single dataframe to maintain a consistent CRS. This consolidation will check if the XS
        dataframes have a consistent CRS if it does not then it will not consolidate the XS dataframes.
        As of 05/14/25, only CRS in this condition is considering the
        NAD83, but additional CRS can be added to this methods as new findings are made.

        """
        crs_list = []
        for xs_df in self.xs_df_list:
            if "NAD83" in xs_df.crs.name or "NAD_1983" in xs_df.crs.name:
                # Convert all GeoDataFrames in the list to the target CRS
                crs_list.append("EPSG:5070")
            else:
                print(False)

        #  Will consolidate ONLY if the CRS is consistent across XS geodpandas dataframes
        if len(set(crs_list)) == 1:
            target_crs = str(np.unique(crs_list)[0])
            self.consolidated_id2xs = geopandas.GeoDataFrame(
                pd.concat([xs_df.to_crs(target_crs) for xs_df in self.xs_df_list], ignore_index=True)
            )
            print(
                f"The consolidated XS geopandas dataframes now has a standardized CRS of:\n{self.consolidated_id2xs.crs.name}"
            )
        else:
            print(
                "Cannot consolidate XS geodpandas dataframes because the CRS is inconsistent across XS geodpandas dataframes."
            )

        return

    def save_xsbyhuc_data(self, xs_data_type: str) -> None:
        """
        Consolidate HEC-RAS models cross-sections based on HUC & save to storage

        Args:
            xs_data_type (str): Cross-section data type to be saved either 'mip' or 'ble' cross-section type.
                                Options: 'mip' or 'ble'

        Return: None

        Note: These saved parquet files will be the transformed CRS of all XS per HUC to ensure
        a consistent standardized CRS.

        """
        unique_huc_nums = set(self.consolidated_id2xs["huc"])
        for huc_num in unique_huc_nums:
            # Generate data folder per HUC
            if not os.path.exists(f"{os.getcwd()}/xs_data/{xs_data_type}_{huc_num}"):
                os.makedirs(f"{os.getcwd()}/xs_data/{xs_data_type}_{huc_num}")

            # Filter consolidated XS geopanda dataframe by HUC
            filterbyhuc = self.consolidated_id2xs[self.consolidated_id2xs["huc"] == huc_num]

            # Save XS as geoparquet per HUC
            filterbyhuc["thalweg"] = filterbyhuc["thalweg"].astype(str)
            filterbyhuc["xs_max_elevation"] = filterbyhuc["xs_max_elevation"].astype(str)
            filterbyhuc.to_parquet(
                f"{os.getcwd()}/xs_data/{xs_data_type}_{huc_num}/huc_{huc_num}.parquet", engine="pyarrow"
            )

            # Save XS as geopackage per HUC
            filterbyhuc.to_file(
                f"{os.getcwd()}/xs_data/{xs_data_type}_{huc_num}/huc_{huc_num}.gpkg", driver="GPKG"
            )

            print(f"{xs_data_type}_{huc_num}")

        return
