import sys

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from odoo.api import Environment
from odoo.exceptions import AccessError, MissingError, UserError, ValidationError

from odoo.addons.base.models.res_partner import Partner

from fastapi import APIRouter, Depends, HTTPException, status, Query

from odoo.addons.fastapi.dependencies import authenticated_partner, fastapi_endpoint, odoo_env
from odoo.addons.fastapi.models import FastapiEndpoint
from odoo.addons.fastapi.schemas import DemoEndpointAppInfo, DemoExceptionType, DemoUserInfo

import datetime
from typing import Any, List

from fastapi.responses import JSONResponse

router = APIRouter(tags=["bloomup_tyre"])

from pydantic import BaseModel, Field

class ResponseStandard(BaseModel):
    message: str
    result: bool
    
    class Config:
        schema_extra  = {
                "examples": [
                    {
                        "message": "Task updated.",
                        "result": True
                    }
                ]
            
        }

class ResponseTyre(BaseModel):
    message: str
    result: bool
    
    class Config:
        schema_extra  = {
                "examples": [
                    {
                        "message": "Tyre created.",
                        "result": True
                    }
                ]
            
        }

class ResponseError(BaseModel):
    message: str
    result: bool
    
    class Config:
        schema_extra  = {
                "examples": [
                    {
                        "message": "Generic Error.",
                        "result": False
                    }
                ]
            
        }    
    
class ConfirmAssemblyDate(BaseModel):
    OrderID: str = Field(description="TyreTeam OrderId")
    AssemblyTyreDateTime: str = Field(description="Confirm tyre assembly date. Format: '%Y-%m-%d %H:%M:%S'")
    
class ExpectedAssemblyDate(BaseModel):
    OrderID: str = Field(description="TyreTeam OrderId")
    ExpectedMountingTyreDateTime: str = Field(description="Expected tyre assembly date. Format: '%Y-%m-%d %H:%M:%S'")
    
class ChangeTyreRepairer(BaseModel):
    OrderID: str = Field(description="TyreTeam OrderId")
    CustomerCode: str = Field(description="Tyre Repaires Code (CustomerCode)")

@router.post("/confirm_assembly_date", responses={200: {"model": ResponseStandard}, 400: {"model": ResponseError}, 500: {"model": ResponseError}, 422: {"model": ResponseError}})
async def confirm_assembly_date(
    env: Annotated[Environment, Depends(odoo_env)],
    partner: Annotated[Partner, Depends(authenticated_partner)],
    params: ConfirmAssemblyDate
) -> ResponseStandard:
    """
    Updates the Assembly Datetime of tasks associated with a given `OrderID` with the provided `AssemblyTyreDateTime`.
    """
    if not params.OrderID or not params.AssemblyTyreDateTime:
        return JSONResponse(
            status_code=400, 
            content={'message':"OrderdId or AssemblyTyreDateTime missing.", 'result': False}
        )
    date_format = '%Y-%m-%d %H:%M:%S'
    try:
        date_obj = datetime.datetime.strptime(params.AssemblyTyreDateTime, date_format)
    except Exception as e:
        return JSONResponse(
            status_code=400, 
            content={'message':"AssemblyTyreDateTime: %s" % e, 'result': False}
        )
    try:
        res = env['project.task'].sudo()._confirm_assembly_date(params.OrderID, params.AssemblyTyreDateTime)
    except Exception as e:
        return JSONResponse(
            status_code=400, 
            content={'message':"Confirm Assembly Date: %s" % e, 'result': False}
        )
    if not res:
        return JSONResponse(
            status_code=500, 
            content={'message':"Generic Error.", 'result': False}
        )
    
    return ResponseStandard(
        message="Task updated.",
        result=True
    )

@router.post("/write_expected_assembly_date", responses={200: {"model": ResponseStandard}, 400: {"model": ResponseError}, 500: {"model": ResponseError}, 422: {"model": ResponseError}})
async def write_expected_assembly_date(
    env: Annotated[Environment, Depends(odoo_env)],
    partner: Annotated[Partner, Depends(authenticated_partner)],
    params: ExpectedAssemblyDate
) -> ResponseStandard:
    """ 
    Updates the Expected Assembly Datetime of tasks associated with a given `OrderID` with the provided `ExpectedMountingTyreDateTime`.
    """
    if not params.OrderID or not params.ExpectedMountingTyreDateTime:
        return JSONResponse(
            status_code=400, 
            content={'message':"OrderdId or ExpectedMountingTyreDateTime missing.", 'result': False}
        )
    date_format = '%Y-%m-%d %H:%M:%S'
    try:
        date_obj = datetime.datetime.strptime(params.ExpectedMountingTyreDateTime, date_format)
    except Exception as e:
        return JSONResponse(
            status_code=400, 
            content={'message':"ExpectedMountingTyreDateTime: %s" % e, 'result': False}
        )
    
    try:
        res = env['project.task'].sudo()._write_expected_assembly_date(params.OrderID, params.ExpectedMountingTyreDateTime)

    except Exception as e:
        return JSONResponse(
            status_code=400, 
            content={'message':"Write Expected Assembly Date: %s" % e, 'result': False}
    )

    
    if not res:
        return JSONResponse(
            status_code=500, 
            content={'message':"Generic Error.", 'result': False}
        )
    
    return ResponseStandard(
        message="Task updated.",
        result=True
    )
    
@router.post("/change_tyre_repairer",responses={200: {"model": ResponseStandard}, 400: {"model": ResponseError}, 500: {"model": ResponseError}, 422: {"model": ResponseError}})
async def change_tyre_repairer(
    env: Annotated[Environment, Depends(odoo_env)],
    partner: Annotated[Partner, Depends(authenticated_partner)],
    params: ChangeTyreRepairer
) -> ResponseStandard:
    """ 
    changes the selected tyre repairer for a given `OrderID` and sends a notification email to the repairer (`CustomerCode`).
    """
    if not params.OrderID or not params.CustomerCode:
        raise HTTPException(
            status_code=400, 
            detail="OrderdId or CustomerCode missing."
        )
    
    try:
        res = env['project.task'].sudo()._change_tyre_repairer(params.OrderID, params.CustomerCode)
    except Exception as e:
        return JSONResponse(
            status_code=400, 
            content={'message':"Change Tyre Repairer: %s" % e, 'result': False}
        )

    if not res:
        return JSONResponse(
            status_code=500, 
            content={'message':"Generic Error.", 'result': False}
        )
    
    return ResponseStandard(
        message="Repairer changed.",
        result=True
    )

class Tyre(BaseModel):
    Brand: str
    Model: str
    SupplierTireId: str
    SupplierCode: str
    ProducerCode: str
    Width: str
    Section: str
    Diameter: str
    LoadIndex: str
    SpeedIndex: str
    Season: str
    TyreTyre: str
    TyreTechnology: str
  
@router.post("/create_tires", status_code=201, responses={400: {"model": ResponseError}, 500: {"model": ResponseError}, 422: {"model": ResponseError}})
async def create_tires(
    env: Annotated[Environment, Depends(odoo_env)],
    partner: Annotated[Partner, Depends(authenticated_partner)],
    params: List[Tyre]
) -> ResponseStandard:
    """ 
    Create new tyre
    """
    
    for tire in params:
        if tire.Season not in ['I', 'E', '4']:
            return JSONResponse(
                status_code=400, 
                content={'message':"Unexpected 'Season' value for %s, only ['I', 'E', '4'] accepted." % tire.SupplierTireId, 'result':False}
            )
        if tire.TyreTyre not in ['Q', 'P']:
            return JSONResponse(
                status_code=400, 
                content={'message':"Unexpected 'TyreTyre' value for %s , only ['Q', 'P'] accepted." % tire.SupplierTireId, 'result':False}
            )
        if tire.TyreTechnology not in ['RF', 'SS', 'ST']:
            return JSONResponse(
                status_code=400, 
                content={'message':"Unexpected 'TyreTechnology' value for %s, only ['RF', 'SS', 'ST'] accepted." % tire.SupplierTireId, 'result':False}
            )
    
    try:
        res = env['tyre.tire'].sudo()._create_tires([x.dict() for x in params])
    except Exception as e:
        return JSONResponse(
            status_code=400, 
            content={'message':"Create Tire: %s." % e, 'result': False}
        )

    if not res:
        return JSONResponse(
            status_code=500, 
            content={'message':"Generic Error.", 'result': False}
        )
    
    return ResponseStandard(
        message="Tyres created.",
        result=True
    )