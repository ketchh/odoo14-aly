# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

_logger = logging.getLogger(__name__)

class FleetPartner(models.Model):
    """
    Indirizzi di prelievo e di consegna delle auto

    ------
    Non esiste distinzione tra i due tipi in quanto
    un indirizzo di consegna oggi può essere un
    indirizzo di prelievo domani.
    ------
    
    ------
    Usata la stessa logica di partner_firstname
    con le stesse funzioni riadattate.
    ------

    ------
    Gli utenti portali possono inserire indirizzi
    di cui saranno gli owner_id (l'azienda che è padre)
    ------

    active : bool
        attivo si/no
    name : str
        nome completo o ragione sociale
    firstname/lastname : str
        nome e cognome
    company_type : selection
        tipo azienda o persona
    street/street2 : str
        indirizzo su due righe
    city : str
        città
    state_id : m2o->res.country.state
        provincia
    country_id : m2o->res.country
        nazione
    zip: str
        cap
    phone : str
        numero di telefono
    fiscalcode : str 16
        codice fiscale (se company_type == 'person')
    vat : str
        partita iva 
    owner_id : m2o->res.partner
        azienda padre di chi ha inserito/possiede gli indirizzi
    email : str
        e-mail
    reference : str
        persona di riferimento (es: alla cortese attenzione di Pippo)
    """
    _name = "fleet.partner"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Fleet Partner"

    active = fields.Boolean(
        string="Active",
        default=True,
        copy=False
    )
    name = fields.Char(
        compute="_compute_name",
        inverse="_inverse_name_after_cleaning_whitespace",
        required=False,
        store=True,
        readonly=False,
        tracking=True
    )
    firstname = fields.Char(
        string="First Name",
        tracking=True
    )
    lastname = fields.Char(
        string="Last Name",
        tracking=True
    )
    company_type = fields.Selection(
        string="Type",
        selection=[
            ('company', _('Company')),
            ('person', _('Person'))
        ],
        default='company',
        tracking=True
    )
    street = fields.Char(
        string="Street",
        tracking=True
    )
    street2 = fields.Char(
        string="Street 2",
        tracking=True
    )
    city = fields.Char(
        string="City",
        tracking=True
    )
    state_id = fields.Many2one(
        string="State",
        comodel_name="res.country.state",
        tracking=True
    )
    country_id = fields.Many2one(
        string="Country",
        comodel_name="res.country",
        tracking=True
    )

    zip = fields.Char(
        string="Zip",
        tracking=True
    )
    
    fiscalcode = fields.Char(
        "Fiscal Code", 
        size=16, 
        help="Italian Fiscal Code",
        tracking=True
    )
    vat = fields.Char(
        string="Vat",
        tracking=True
    )
    owner_id = fields.Many2one(
        string="Partner",
        comodel_name="res.partner",
        tracking=True
    )
    reference = fields.Char(
        string='Reference',
        tracking=True
    )

    def toggle_active(self):
        for move in self:
            move.active = not move.active
            
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        
        if name and operator in ('=', 'ilike', '=ilike', 'like', '=like'):
            
            domain = expression.OR([
                [['name',operator,name]],
                [['street',operator,name]],
                [['street2',operator,name]],
                [['city',operator,name]],
                [['state_id',operator,name]],
                [['country_id',operator,name]],
                [['zip',operator,name]]
            ])
            return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return super(FleetPartner, self)._name_search(name=name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)


    def name_get(self):
        result = []
        for address in self:
            name = ""
            if address.name:
                name = address.name
            if address.street:
                name += ', ' + address.street
                
            # if address.street2:
            #     name += ', ' + address.street2
            if address.city:
                name += ', ' + address.city
            if address.state_id:
                name += ' (' + address.state_id.code +')'
            if address.zip:
                name += ', ' + address.zip
            result.append((address.id, name))
        return result

    @api.constrains("fiscalcode")
    def check_fiscalcode(self):
        for partner in self:
            if not partner.fiscalcode:
                continue
            elif partner.company_type == "person":
                if len(partner.fiscalcode) != 16:
                    # Check fiscalcode of a person
                    msg = _("The fiscal code doesn't seem to be correct.")
                    raise ValidationError(msg)
        return True
        
    @api.model
    def create(self, vals):
        """Add inverted names at creation if unavailable."""
        context = dict(self.env.context)
        name = vals.get("name", context.get("default_name"))

        if name is not None:
            # Calculate the splitted fields
            inverted = self._get_inverse_name(
                self._get_whitespace_cleaned_name(name),
                vals.get("is_company", self.default_get(["is_company"])),
            )
            for key, value in inverted.items():
                if not vals.get(key) or context.get("copy"):
                    vals[key] = value

            # Remove the combined fields
            if "name" in vals:
                del vals["name"]
            if "default_name" in context:
                del context["default_name"]

        return super(FleetPartner, self.with_context(context)).create(vals)

    def copy(self, default=None):
        """Ensure partners are copied right.

        Odoo adds ``(copy)`` to the end of :attr:`~.name`, but that would get
        ignored in :meth:`~.create` because it also copies explicitly firstname
        and lastname fields.
        """
        return super(FleetPartner, self.with_context(copy=True)).copy(default)

    @api.model
    def default_get(self, fields_list):
        """Invert name when getting default values."""
        result = super(FleetPartner, self).default_get(fields_list)

        inverted = self._get_inverse_name(
            self._get_whitespace_cleaned_name(result.get("name", "")),
            result.get("is_company", False),
        )

        for field in list(inverted.keys()):
            if field in fields_list:
                result[field] = inverted.get(field)

        return result

    @api.model
    def _names_order_default(self):
        return "first_last"

    @api.model
    def _get_names_order(self):
        """Get names order configuration from system parameters.
        You can override this method to read configuration from language,
        country, company or other"""
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("partner_names_order", self._names_order_default())
        )

    @api.model
    def _get_computed_name(self, lastname, firstname):
        """Compute the 'name' field according to splitted data.
        You can override this method to change the order of lastname and
        firstname the computed name"""
        order = self._get_names_order()
        if order == "last_first_comma":
            return ", ".join(p for p in (lastname, firstname) if p)
        elif order == "first_last":
            return " ".join(p for p in (firstname, lastname) if p)
        else:
            return " ".join(p for p in (lastname, firstname) if p)

    @api.depends("firstname", "lastname")
    def _compute_name(self):
        """Write the 'name' field according to splitted data."""
        for record in self:
            record.name = record._get_computed_name(record.lastname, record.firstname)

    def _inverse_name_after_cleaning_whitespace(self):
        """Clean whitespace in :attr:`~.name` and split it.

        The splitting logic is stored separately in :meth:`~._inverse_name`, so
        submodules can extend that method and get whitespace cleaning for free.
        """
        for record in self:
            # Remove unneeded whitespace
            clean = record._get_whitespace_cleaned_name(record.name)
            record.name = clean
            record._inverse_name()

    @api.model
    def _get_whitespace_cleaned_name(self, name, comma=False):
        """Remove redundant whitespace from :param:`name`.

        Removes leading, trailing and duplicated whitespace.
        """
        if isinstance(name, bytes):
            # With users coming from LDAP, name can be a byte encoded string.
            # This happens with FreeIPA for instance.
            name = name.decode("utf-8")

        try:
            name = " ".join(name.split()) if name else name
        except UnicodeDecodeError:
            # with users coming from LDAP, name can be a str encoded as utf-8
            # this happens with ActiveDirectory for instance, and in that case
            # we get a UnicodeDecodeError during the automatic ASCII -> Unicode
            # conversion that Python does for us.
            # In that case we need to manually decode the string to get a
            # proper unicode string.
            name = " ".join(name.decode("utf-8").split()) if name else name

        if comma:
            name = name.replace(" ,", ",")
            name = name.replace(", ", ",")
        return name

    @api.model
    def _get_inverse_name(self, name, is_company=False):
        """Compute the inverted name.

        - If the partner is a company, save it in the lastname.
        - Otherwise, make a guess.

        This method can be easily overriden by other submodules.
        You can also override this method to change the order of name's
        attributes

        When this method is called, :attr:`~.name` already has unified and
        trimmed whitespace.
        """
        # Company name goes to the lastname
        if is_company or not name:
            parts = [name or False, False]
        # Guess name splitting
        else:
            order = self._get_names_order()
            # Remove redundant spaces
            name = self._get_whitespace_cleaned_name(
                name, comma=(order == "last_first_comma")
            )
            parts = name.split("," if order == "last_first_comma" else " ", 1)
            if len(parts) > 1:
                if order == "first_last":
                    parts = [" ".join(parts[1:]), parts[0]]
                else:
                    parts = [parts[0], " ".join(parts[1:])]
            else:
                while len(parts) < 2:
                    parts.append(False)
        return {"lastname": parts[0], "firstname": parts[1]}

    def _inverse_name(self):
        """Try to revert the effect of :meth:`._compute_name`."""
        for record in self:
            is_company = False
            if record.company_type == 'company':
                is_company = True
            parts = record._get_inverse_name(record.name, is_company)
            record.lastname = parts["lastname"]
            record.firstname = parts["firstname"]

class ResPartner(models.Model):
    _inherit = "res.partner"

    fleet_partner_ids = fields.One2many(
        string="Fleet Partner",
        comodel_name="fleet.partner",
        inverse_name="owner_id",
    )