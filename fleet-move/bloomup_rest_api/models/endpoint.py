from __future__ import annotations

import sys

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from typing import Any, List

from odoo import _, api, fields, models
from odoo.api import Environment
from odoo.exceptions import ValidationError

from odoo.addons.base.models.res_partner import Partner
from odoo.addons.base.models.res_users import Users

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from odoo.addons.fastapi.dependencies import (
    authenticated_partner_from_basic_auth_user,
    authenticated_partner_impl,
    odoo_env,
    basic_auth_user
)
from typing import List, Union

from odoo.addons.base.models.res_partner import Partner

from .routes import router

class FastapiEndpoint(models.Model):
    _inherit = "fastapi.endpoint"

    app: str = fields.Selection(
        selection_add=[("bloomup_tyre", "Bloomup Tyre")], ondelete={"bloomup_tyre": "cascade"}
    )
    bloomup_tyre_auth_method = fields.Selection(
        selection=[('api_key', "API KEY"),("http_basic", "HTTP Basic")],
        string="Authentication method",
    )
    bloomup_tyre_show_docs = fields.Boolean(
        string="Show Docs",
        default=False
    )
    bloomup_tyre_show_redoc = fields.Boolean(
        string="Show Redoc",
        default=False
    )

    def _get_fastapi_routers(self) -> List[APIRouter]:
        """ 
        Add to router
        
        variable router comes from '''from .routes import router''' 
        where it's instantiated
        """
        if self.app == "bloomup_tyre":
            return [router]
        return super()._get_fastapi_routers()
    
    @api.model
    def _fastapi_app_fields(self) -> List[str]:
        """ 
        Add new fields to fastapi list
        """
        fields = super()._fastapi_app_fields()
        fields.append("bloomup_tyre_auth_method")
        fields.append("bloomup_tyre_show_docs")
        fields.append("bloomup_tyre_show_redoc")
        return fields
    
    def _prepare_fastapi_app_params(self) -> Dict[str, Any]:
        """
        Return the params to pass to the Fast API app constructor
        
        see https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration/
        """
        res = super()._prepare_fastapi_app_params()
       
        # disable swagger
        if not self.bloomup_tyre_show_docs:
            res.update(
                {
                    'docs_url': None,
                }
            )
        else:
            res.update({
                'swagger_ui_parameters':{
                    'syntaxHighlight':False,
                    'defaultModelsExpandDepth': -1,
                    'defaultModelRendering': "model"
                }
            })
        
        if not self.bloomup_tyre_show_redoc:
            res.update(
                {'redoc_url': None}
            )
        
        return res
    
    def _get_fastapi_app_dependencies(self) -> List[Depends]:
        res=[(Depends(APIKeyHeader(name="api-key")))]
        return res
    
    def _get_app(self):
        app = super()._get_app()
        if self.app == "bloomup_tyre":
            # Here we add the overrides to the authenticated_partner_impl method
            # according to the authentication method configured on the demo app
            if self.bloomup_tyre_auth_method == "http_basic":
                authenticated_partner_impl_override = (
                    authenticated_partner_from_basic_auth_user
                )
            else:
                authenticated_partner_impl_override = (
                    api_key_based_authenticated_partner_impl
                )
            app.dependency_overrides[
                authenticated_partner_impl
            ] = authenticated_partner_impl_override
        return app
    
def api_key_based_authenticated_partner_impl(
    api_key: Annotated[
        str,
        Depends(
            APIKeyHeader(
                name="api-key",
            )
        ),
    ],
    env: Annotated[Environment, Depends(odoo_env)],
) -> Partner:
    """A dummy implementation that look for a user with the same login
    as the provided api key
    """
    result = env['fastapi.token'].sudo().search([('token','=',api_key)],limit=1)
    partner = False
    if result:
        partner = result.user_id.partner_id
        
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect API Key"
        )
    return partner
