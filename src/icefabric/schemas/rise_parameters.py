from pydantic import BaseModel

# Conversion dict for python-incompatible names found in the RISE API
PARAM_CONV = {
    "orderUpdateDate": "order[updateDate]",
    "orderRecordTitle": "order[recordTitle]",
    "orderLocationName": "order[locationName]",
    "orderId": "order[id]",
    "orderFulltext": "order[fulltext]",
    "orderLikematch": "order[likematch]",
    "orderDateTime": "order[dateTime]",
    "updateDateBefore": "updateDate[before]",
    "updateDateStrictlyBefore": "updateDate[strictly_before]",
    "updateDateAfter": "updateDate[after]",
    "updateDateStrictlyAfter": "updateDate[strictly_after]",
    "dateTimeBefore": "dateTime[before]",
    "dateTimeStrictlyBefore": "dateTime[strictly_before]",
    "dateTimeAfter": "dateTime[after]",
    "dateTimeStrictlyAfter": "dateTime[strictly_after]",
    "catalogItemIsModeled": "catalogItem.isModeled",
}


class CatItemParams(BaseModel):
    """Parameters for the catalog-item resource"""

    page: int | None = 1
    itemsPerPage: int | None = 25
    id: str | None = None
    hasItemStructure: bool | None = None


class CatRecParams(BaseModel):
    """Parameters for the catalog-record resource"""

    page: int | None = 1
    itemsPerPage: int | None = 25
    updateDateBefore: str | None = None
    updateDateStrictlyBefore: str | None = None
    updateDateAfter: str | None = None
    updateDateStrictlyAfter: str | None = None
    id: str | None = None
    stateId: str | None = None
    regionId: str | None = None
    unifiedRegionId: str | None = None
    locationTypeId: str | None = None
    themeId: str | None = None
    itemStructureId: str | None = None
    generationEffortId: str | None = None
    search: str | None = None
    hasItemStructure: bool | None = None
    hasCatalogItems: bool | None = None
    orderUpdateDate: str | None = None
    orderRecordTitle: str | None = None
    orderId: str | None = None
    orderFulltext: str | None = None
    orderLikematch: str | None = None


class LocItemParams(BaseModel):
    """Parameters for the location resource"""

    page: int | None = 1
    itemsPerPage: int | None = 25
    id: str | None = None
    stateId: str | None = None
    regionId: str | None = None
    locationTypeId: str | None = None
    themeId: str | None = None
    parameterId: str | None = None
    parameterTimestepId: str | None = None
    parameterGroupId: str | None = None
    itemStructureId: str | None = None
    unifiedRegionId: str | None = None
    generationEffortId: str | None = None
    search: str | None = None
    catalogItemsIsModeled: bool | None = None
    hasItemStructure: bool | None = None
    hasCatalogItems: bool | None = None
    orderUpdateDate: str | None = None
    orderLocationName: str | None = None
    orderId: str | None = None
    orderFulltext: str | None = None
    orderLikematch: str | None = None


class ResParams(BaseModel):
    """Parameters for the result resource"""

    page: int | None = 1
    itemsPerPage: int | None = 25
    id: str | None = None
    itemId: str | None = None
    modelRunId: str | None = None
    locationId: str | None = None
    parameterId: str | None = None
    dateTimeBefore: str | None = None
    dateTimeStrictlyBefore: str | None = None
    dateTimeAfter: str | None = None
    dateTimeStrictlyAfter: str | None = None
    orderDateTime: str | None = None
    orderId: str | None = None
    catalogItemIsModeled: bool | None = None
