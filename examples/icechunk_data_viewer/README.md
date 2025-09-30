# Topobathy Data Viewer
The purpose of this data viewer is to visualize version-controlled tif files hosted by the NGWPC program. The data viewer can be run either on pre-processed tiles, or by creating said tiles on an end-to-end full workflow. Details on how to run each are below
## If tiles are pre-created and stored on s3:
1. Move to icechunk_data-viewer folder:

    `cd examples/icechunk_data_viewer`
2. Export AWS data account credentials to your environment and run in CLI:

    `aws s3 sync s3://hydrofabric-data/surface/nws-topobathy/tiles ./martin/tiles`

3. Start martin tile server:

    `cd martin`

    `docker compose -f compose.martin.yaml up`

4. Tile server is now running. Confirm by checking `localhost:3000/catalog`. You should see a list of tile sources. Debug logs should be populating in console.
5. Open a new terminal and move to  `icechunk_data_viewer` root

    `cd examples/icechunk_data_viewer`
6. Start jupyter lab in activated icefabric virtual environment. This will start the jupyter server at `localhost:8888/lab`

    `jupyter lab`

7. Open `viewer.ipynb` in Jupyter Lab
8.  Execute cells in `viewer.ipynb`. The map should show the tiles served from Martin.


## Full Pipeline - from creating tiles to viewing
1. __In icefabric repo__: Export topobathy from icechunk to TIFF using `icefabric_tools/icechunk/topobathy_ic_to_tif.py`. These will be stored locally.

    __NOTE__: Some files may require more memory than average desktop. If 'killed', move to a cluster with more memory.

2. Clone hydrofabric-ui-tools
3. __In hydrofabric-ui-tools repo__: Copy saved icechunk TIFs to `data` folder in `hydrofabric-ui-tools`
5. Create or modify `config` files to match TIF
6. Run `build_topobathy_tiles.py` using docker or local environment as described in `README.md`. Some regions may require more memory than average desktop.
7. Tiles will be uploaded to s3 if specified in config.
8. __Return to icefabric repo__
9. Sync from s3 or paste `.pmtiles` files into

    `icefabric/examples/icechunk_data_viewer/martin/tiles`

AWS option with data account credentials in env vars.

    cd examples/icechunk_data_viewer
    aws s3 sync s3://hydrofabric-data/surface/nws-topobathy/tiles ./martin/tiles

10. Open `martin_config.yaml`

    `icefabric/examples/icechunk_data_viewer/martin/martin_config.yaml`

11. Match tile names in `tiles` folders to source name if not correct. Source name will be the URI for tile serving.

12. Start martin tile server. This must be done in the `martin` working directory to copy the files correctly.
    ```
    cd examples/icechunk_data_viewer/martin
    docker compose -f compose.martin.yaml up
    ```

13. Tile server is now running. Confirm by checking `localhost:3000/catalog`. You should see a list of tile sources.
14.  Open a new terminal and move to  `icechunk_data_viewer` root

    `cd examples/icechunk_data_viewer`
15. Start jupyter lab in activated icefabric virtual environment. This will start the jupyter server at `localhost:8888/lab`

    `jupyter lab`

16. Open `viewer.ipynb` in Jupyter Lab
17. Execute cells in `viewer.ipynb`. The map should show the tiles served from Martin.
