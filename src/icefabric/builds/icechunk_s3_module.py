"""
NGWPC Icechunk interface module

Module containing classes/methods pertaining
to S3 pathing and Icechunk repos
"""

import subprocess
import warnings
from pathlib import Path
from typing import Any

import icechunk as ic
import xarray as xr
from icechunk.xarray import to_icechunk


class S3Path:
    """
    Class representing an S3 path.

    Corresponds to an S3 bucket, prefix and region

    Parameters
    ----------
    bucket: str
        The bucket of the S3 path.
    prefix: str
        The S3 path (minus the bucket).
    region: str
        The S3 region the bucket/path belongs to. Defaults to 'us-east-1'.
    """

    bucket: str
    prefix: str
    region: str

    def __init__(self, bucket: str, prefix: str, region: str | None = "us-east-1"):
        self.bucket = bucket
        self.prefix = prefix
        self.region = region  # type: ignore

    def __str__(self):
        """Returns the full S3 path"""
        return f"s3://{self.bucket}/{self.prefix}"

    def partial_path(self):
        """Returns the S3 path without the 'S3://' prefix"""
        return f"{self.bucket}/{self.prefix}"


class IcechunkRepo:
    """
    Class representing an S3 bucket or local icechunk store

    Parameters
    ----------
    location: S3Path | Path
        The S3Path or local path of the repo.
    repo: ic.Repository
        The icechunk repo, derived from the bucket, prefix, and region. S3
        credentials are provided from the environment.
    virtual_chunks: list[ic.VirtualChunkContainer] | None
        A list of virtual chunk containers corresponding to reference data
        for virtualized stores. Allows icechunk to reference S3 locations
        in virtualized datasets.
    """

    location: S3Path | Path
    repo: ic.Repository
    virtual_chunks: list[ic.VirtualChunkContainer] | None

    def __init__(self, location: S3Path | Path, virtual_chunk_mapping: list[dict[str, str]] | None = None):
        self.location = location
        self.virtual_chunks = self.gen_virtual_chunk_containers(virtual_chunk_mapping)
        self.repo = self.open_repo()

    def open_repo(self) -> ic.Repository:
        """
        Opens an icechunk repo

        Using the class instance parameters, open and assign an icechunk repo corresponding
        to the setup (bucket, prefix, region, etc.)

        Returns
        -------
        ic.Repository
            Icechunk repo corresponding to the S3 bucket path defined in the instance
        """
        if isinstance(self.location, S3Path):
            storage_config = ic.s3_storage(
                bucket=self.location.bucket,
                prefix=self.location.prefix,
                region=self.location.region,
                from_env=True,
            )
            credentials = ic.containers_credentials({self.location.bucket: ic.s3_credentials(from_env=True)})
            config = ic.RepositoryConfig.default()
            if self.virtual_chunks:
                for vcc in self.virtual_chunks:
                    config.set_virtual_chunk_container(vcc)
        else:
            # self.location is a Path
            storage_config = ic.local_filesystem_storage(str(self.location))
            credentials = None
            config = None

        repo = ic.Repository.open_or_create(storage_config, config, credentials)
        return repo

    def delete_repo(self, quiet: bool | None = False):
        """
        Deletes the entire icechunk repo from S3.

        Parameters
        ----------
        quiet : bool | None, optional
            Suppresses AWS CLI output. By default False
        """
        del_command = ["aws", "s3", "rm", str(self.location), "--recursive"]
        if quiet:
            del_command.append("--quiet")
        subprocess.call(del_command)
        print(f"Icechunk repo @ {str(self.location)} in its entirety was successfully deleted.")

    def gen_virtual_chunk_containers(
        self, virtual_chunk_mapping: list[dict[str, str]] | None = None
    ) -> list[ic.VirtualChunkContainer]:
        """
        Create a list of virtual chunk containers

        Given a list of dictionaries mapping out virtual chunks, generate
        and return a list of VirtualChunkContainers

        Parameters
        ----------
        virtual_chunk_mapping : list[dict[str, str]] | None, optional
            A list of dictionaries, each entry mapping out a single
            virtual chunk definition. Should include a bucket and region.
            By default None

        Returns
        -------
        list[ic.VirtualChunkContainer]
            A list of VirtualChunkContainers corresponding to the list of passed-in
            dict mappings.
        """
        v_chunks = None
        if virtual_chunk_mapping:
            v_chunks = [
                self.set_up_virtual_chunk_container(vc["bucket"], vc["region"])
                for vc in virtual_chunk_mapping
            ]
        return v_chunks

    def create_session(
        self, read_only: bool | None = True, snap_id: str | None = None, branch: str | None = "main"
    ) -> ic.Session:
        """
        Open a session under the repo defined by an instance of IcechunkS3Repo

        Parameters
        ----------
        read_only : bool | None, optional
            Denotes if the session will be read-only or writable. By default True
        snap_id: str | None, optional
            The Snapshot ID of a specific commit to base the session on. Leave out if you want the
            latest. By default None
        branch : str | None, optional
            Icechunk repo branch to be opened. By default "main"

        Returns
        -------
        ic.Session
            Icechunk repo session. Writable or read-only based on parameters. Branch
            can be configured.
        """
        if read_only:
            if snap_id:
                return self.repo.readonly_session(snapshot_id=snap_id)
            else:
                return self.repo.readonly_session(branch)
        return self.repo.writable_session(branch)

    def retrieve_dataset(self, branch: str | None = "main", snap_id: str | None = None) -> xr.Dataset:
        """
        Returns the repo's store contents as an Xarray dataset

        Parameters
        ----------
        branch : str | None, optional
            Icechunk repo branch to be opened, by default "main"
        snap_id : str | None, optional
            The Snapshot ID of a specific commit you want to retrieve. Leave out if you want the
            latest. By default None.

        Returns
        -------
        xr.Dataset
            Xarray dataset representation of the Icechunk store
        """
        if snap_id:
            session = self.create_session(read_only=True, branch=branch, snap_id=snap_id)
        else:
            session = self.create_session(read_only=True, branch=branch)
        ds = xr.open_zarr(session.store, consolidated=False, chunks={})

        # geotiff rasters saved in zarr need to be convereted to spatial-aware xarray with rioxarray
        if "spatial_ref" in ds.data_vars:
            ds.rio.write_crs(ds.spatial_ref.spatial_ref, inplace=True)

        return ds

    def retrieve_rollback_to_snapshot(self, snap_id: str, branch: str | None = "main") -> xr.Dataset:
        """Retrieves the repo data a specific snapshot ID"""
        return self.retrieve_dataset(branch=branch, snap_id=snap_id)

    def retrieve_rollback_n_snapshots(self, n: int, branch: str | None = "main") -> xr.Dataset:
        """Retrieves the repo data from <n> snapshot(s) ago"""
        try:
            snap_id = list(self.repo.ancestry(branch=branch))[n].id
        except IndexError:
            print(f"Rolled back too far! Branch ({branch}) has fewer previous commits than was specified")
        return self.retrieve_rollback_to_snapshot(snap_id, branch=branch)

    def retrieve_prev_snapshot(self, branch: str | None = "main") -> xr.Dataset:
        """Retrieves the repo data one snapshot ago"""
        return self.retrieve_rollback_n_snapshots(n=1, branch=branch)

    def write_dataset(
        self, ds: xr.Dataset, commit: str, virtualized: bool | None = False, branch: str | None = "main"
    ):
        """
        Given a dataset, push a new commit alongisde the data to the icechunk store

        Parameters
        ----------
        ds : xr.Dataset
            Dataset to be commited to the icechunk store.
        commit : str
            Commit message that will accompany the dataset push.
        virtualized : bool | None, optional
            Designates if the dataset to be written is virtualized. Affects
            how it's written to icechunk. By default False
        branch : str | None, optional
            Icechunk repo branch to be pushed. By default "main".
        """
        session = self.create_session(read_only=False, branch=branch)
        if virtualized:
            ds.virtualize.to_icechunk(session.store)
        else:
            to_icechunk(ds, session)
        snapshot = session.commit(commit)
        print(f"Dataset is uploaded. Commit: {snapshot}")

    def append_virt_data_to_store(
        self, vds: xr.Dataset, append_dim: str, commit: str, branch: str | None = "main"
    ):
        """
        Add new data to the store

        Given a virtualized dataset, push a new commit to append
        data to an existing icechunk store. The data will be
        appended on a specified dimension.

        Parameters
        ----------
        vds : xr.Dataset
            The virtualized dataset to be appended to the
            existing icechunk store.
        append_dim : str
            What dimension the dataset will be appended on. Likely
            time or year, etc.
        commit : str
            Commit message that will accompany the dataset addition.
        branch : str | None, optional
            Icechunk repo branch to be pushed. By default "main".
        """
        session = self.create_session(read_only=False, branch=branch)
        vds.virtualize.to_icechunk(session.store, append_dim=append_dim)
        snapshot = session.commit(commit)
        print(f"Dataset has been appended on the {append_dim} dimension. Commit: {snapshot}")

    def create_new_branch_from_snapshot(self, name: str, snap_id: str):
        """Create a new branch that is based on a specific snapshot ID"""
        self.repo.create_branch(name, snapshot_id=snap_id)

    def create_new_branch(self, name: str, origin: str | None = "main"):
        """Create a new branch that is based on the most recent snapshot on a given branch"""
        branch_latest_snap_id = self.repo.lookup_branch(origin)
        self.create_new_branch_from_snapshot(name, snap_id=branch_latest_snap_id)

    def print_history(self, branch: str | None = "main"):
        """
        Prints a nicely-formatted summary of the history of the icechunk repo branch.

        Parameters
        ----------
        branch : str | None, optional
            The branch whose history will be printed. By default "main"
        """
        for ancestor in self.repo.ancestry(branch=branch):
            print(f"Snapshot ID:\t{ancestor.id}")
            print(f"Timestamp:\t{ancestor.written_at}")
            print(f"Message:\t{ancestor.message}\n")

    def retrieve_and_convert_to_tif(
        self,
        dest: str | Path,
        var_name: str = None,
        branch: str | None = "main",
        compress: str = "lzw",
        tiled: bool = True,
        minx: float | None = None,
        miny: float | None = None,
        maxx: float | None = None,
        maxy: float | None = None,
        profile_kwargs: dict[Any, Any] = None,
    ) -> None:
        """A function to retrieve a raster icechunk dataset and download as a tif.

        Parameters
        ----------
        dest : str | Path
            Destination file path for tiff
        var_name : str, optional
            Name of xarray variable to be used for raster data, by default None
        branch : str | None, optional
            Icechunk repo branch to be opened, by default "main"
        compress : str, optional
            Specify a compression type for raster, by default "lzw"
        tiled : bool, optional
           Specify if raster should be tiled or not. Cloud-Optimized Geotiffs (COG) must be tiled, by default True
        minx : float | None, optional
            Specify a bounding box minimum x. Must have all [minx, miny, maxx, maxy] specified, by default None
        miny : float | None, optional
           Specify a bounding box minimum y. Must have all [minx, miny, maxx, maxy] specified, by default None
        maxx : float | None, optional
           Specify a bounding box maximum x. Must have all [minx, miny, maxx, maxy] specified, by default None
        maxy : float | None, optional
            Specify a bounding box maximum x. Must have all [minx, miny, maxx, maxy] specified, by default None
        profile_kwargs : dict[Any, Any], optional
            Any additional profile keywords accepted by GDAL geotiff driver
            (https://gdal.org/en/stable/drivers/raster/gtiff.html#creation-options), by default None


        Raises
        ------
        AttributeError
            If an xarray dataset does not have a "band" attribute in coordinates, the file is not deemed a raster
            and will raise error.
        """
        ds = self.retrieve_dataset(branch=branch)

        if "band" not in ds.coords.dims:
            raise AttributeError("Dataset needs a 'band' coordinate to export geotiff")

        # infer variable name if none provided - MAY HAVE UNEXPECTED RESULTS
        if not var_name:
            var_name = self._infer_var_name_for_geotiff(list(ds.data_vars.variables))

        # initialize keywords dict if none
        profile_kwargs = {} if not profile_kwargs else profile_kwargs

        # clip to window
        if minx and miny and maxx and maxy:
            subset = ds.rio.clip_box(minx=minx, miny=miny, maxx=maxx, maxy=maxy)
            subset[var_name].rio.to_raster(dest, compress=compress, tiled=tiled, **profile_kwargs)
            del subset
            print(f"Saved clipped window to {dest}")

        else:
            ds[var_name].rio.to_raster(dest, compress=compress, tiled=tiled, **profile_kwargs)
            del ds
            print(f"Saved dataset to {dest}")

    def _infer_var_name_for_geotiff(self, variable_list: list) -> str:
        """Infer a variable name for saving a geotiff from xarray variables

        Picks the first variable that isn't 'spatial_ref'. In zarr, 'spatial_ref' from CRS is moved
        from coordinates to variables. We want a variable that is not it.
        This arbitarily picks the first variable.

        Parameters
        ----------
        variable_list : list
            Output of list(ds.data_vars.variables)

        Returns
        -------
        str
            Variable name to use for geotif generation
        """
        if "spatial_ref" in variable_list:
            variable_list.remove("spatial_ref")
        var_name = variable_list[0]
        warnings.warn(
            UserWarning,
            f"Inferring xarray variable name {var_name} for raster data. This may have unintended consequences."
            "Open dataset separately to check variable names to insure correct output.",
            stacklevel=2,
        )
        return var_name

    @staticmethod
    def create_local_virtual_chunk_container(path: str) -> ic.VirtualChunkContainer:
        """
        Create a virtual chunk container from a mapping for local files.

        Parameters
        ----------
        path : str
            The local path to the files which need to be virtualized

        Returns
        -------
        ic.VirtualChunkContainer
            A definition of a virtual chunk that the icechunk repo
            uses to define access to virtualized data.
        """
        abs_path = str(Path(path).resolve())
        store_config = ic.local_filesystem_store(abs_path)
        return ic.VirtualChunkContainer(f"file://{abs_path}", store_config)

    @staticmethod
    def set_up_virtual_chunk_container(bucket: str, region: str) -> ic.VirtualChunkContainer:
        """
        Create a virtual chunk container from a mapping

        Given an S3 bucket/region, generate and return a VirtualChunkContainer
        so Icechunk can point to virtualized data inside S3 buckets.

        Parameters
        ----------
        bucket : str
            The S3 bucket the virtual chunk points to.
        region : str
            The region of the S3 bucket.

        Returns
        -------
        ic.VirtualChunkContainer
            A definition of a virtual chunk that the icechunk repo
            uses to define access to virtualized data.
        """
        return ic.VirtualChunkContainer(
            name=bucket, url_prefix=f"s3://{bucket}/", store=ic.s3_store(region=region)
        )
