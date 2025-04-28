# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import xlrd
import base64
import csv
import io 
import ast
import pprint
from datetime import datetime

class IPAT(models.Model):
    _name = "bloomup.ipat"
    _description = "IPAT Importer"
    
    name = fields.Char(
        string="Name"
    )
    model = fields.Many2one(
        string="Model",
        comodel_name="ir.model"
    )
    file = fields.Binary(
        string="File to Import"
    )
    message = fields.Text(
        string="Message"
    )
    refused = fields.Text(
        string="Refused"
    )
    line_ids = fields.One2many(
        comodel_name='bloomup.ipat.lines', 
        inverse_name='ipat_id', 
        string='Lines'
    )
    header = fields.Char(
        string="Header"
    )
    datas =fields.Text(
        string="Datas"
    )
    
    def get_header(self):
        self.ensure_one()
        output = base64.b64decode(self.file)
        wb = xlrd.open_workbook(file_contents=output or b'')
        sheets = wb.sheet_names()
        # TODO: prendo il primo sheet ma possiamo configurare
        sheet = wb.sheet_by_name(sheets[0])
        i = -1
        for rowx, row in enumerate(map(sheet.row, range(sheet.nrows)), 1):
            values=[]
            i+=1
            for colx, cell in enumerate(row, 1):
                values.append(cell.value)
            if i==0:
                header=values
                break
        self.header=header
    
    def get_datas(self):
        self.ensure_one()
        self.refused = ''
        output = base64.b64decode(self.file)
        wb = xlrd.open_workbook(file_contents=output or b'')
        sheets = wb.sheet_names()
        # TODO: prendo il primo sheet ma possiamo configurare
        sheet = wb.sheet_by_name(sheets[0])
        i = -1
        header = ast.literal_eval(self.header)
        datas=[]
        for rowx, row in enumerate(map(sheet.row, range(sheet.nrows)), 1):
            values=[]
            i+=1
            for colx, cell in enumerate(row, 1):
                values.append((cell.value, cell.ctype))
            if i>0:
                dict_values = dict(zip(header,values))
                datas.append(dict_values)
        # filtro le linee con required
        required_fields = self.line_ids.filtered(lambda x: x.required).mapped('column_name')
        lines_refused = {}
        sanitized_datas = []
        for data in datas:
            req = True
            for f in required_fields:
                if not str(data[f][0]).strip():
                    req=False
                    index = datas.index(data) + 2
                    if lines_refused.get(index):
                        lines_refused[index].append(f)
                    else:
                        lines_refused[index] = [f]
            if req:
                sanitized_datas.append(data)
        if len(lines_refused):
            self.refused = lines_refused
        self.datas=sanitized_datas

    def load_file(self):
        """
        Carica il file:
        le varie lines con il column name impostato
        """
        
        for record in self:
            if record.file:
                record.get_header()
                record.get_datas()
                header = ast.literal_eval(record.header)       
                for head in header:
                    self.env['bloomup.ipat.lines'].create({
                        'column_name': head,
                        'ipat_id': record.id
                    })
    
    def load_datas(self):
        """
        carica i dati e l'header
        """
        for record in self:
            if record.file:
                record.get_header()
                record.get_datas()
    
    def clear_datas(self):
        """
        Pulisce i dati e l'header
        """
        for record in self:
            record.header = ''
            record.datas = ''
    
    def change_file(self):
        """
        Cambia il file:
        - cancella tutti i dati e le linee
        """
        for record in self:
            record.clear_datas()
            record.line_ids.unlink()
            record.file = False
    
    def search_record(self, data=False):
        """
        fa la ricerca se esiste il record:
        - fa il dominio di ricerca (in AND)
        - restituisce il record trovato oppure queryset vuoto
        """
        self.ensure_one()
        if not data:
            return False
        # fa il dominio di ricerca (in AND)
        domain_search = []
        to_search = self.line_ids.filtered(lambda x:x.to_search)
        for ts in to_search:
            operator = '=ilike'
            value = self.get_record_value(data=data,line=ts)
            if ts.field_type == 'many2one' or ts.field_type == 'integer' or ts.field_type=='float':
                operator='='
            if ts.field_type == 'many2one' or ts.field_type == 'integer':
                value = int(value)
            if ts.field_type == 'many2one' and value == 0:
                value = False
            if ts.field_type=='float':
                value = float(value)
            domain_search.append((ts.field.name,operator,value))
        try:
            result = self.env[self.model.model].search(domain_search)
        except:
            return False
        return result
    
    def get_record_value(self, data=False, line=False):
        """
        restituisce il valore da inserire nel campo
        può essere sovrascritta per ogni tipo e per ogni logica esterna
        """
        if not data or not line:
            return False
        
        if line.fixed:
            # TODO: controlla il tipo del field
            fi = line.code
            if fi.isnumeric():
                try:
                    fi = int(fi)
                except ValueError:
                    fi = float(fi)
            return fi
        
        if line.field_type == 'many2one':
            # fai la ricerca
            result = line.ref_ipat.search_record(data=data)
            if result:
                return result[0].id
            else:
                return False
        # controllo se c'è un code.
        if line.code:
            if line.field_type == 'date' or line.field_type == 'datetime':
                if data[line.column_name]:
                    try:
                        if data[line.column_name][1] == 3:
                            datetime_date = xlrd.xldate_as_datetime(data[line.column_name][0], 0)
                        else:
                            datetime_date = datetime.strptime(str(data[line.column_name][0]), line.code)
                        return datetime_date
                    except:
                        return False
                else:
                    return False
            match = ast.literal_eval(line.code)
            lower_match = {}
            for m in match:
                lower_match[m.lower()] = match[m]
            d = data[line.column_name][0].lower()
            if d in lower_match:
                return lower_match[d] 
        
        if line.field_type == 'integer':
            try:
                return int(data[line.column_name][0])
            except:
                return 0
        if line.field_type == 'float':
            try:
                return float(data[line.column_name][0])
            except:
                return 0
                
        return str(data[line.column_name][0]).strip()
    
    def start_import(self):
        """
        Importa:
        - importa prima i ref_ipat per creare quei dati che poi associa
        - per ogni dato fa la ricerca
        - crea
        """
        for record in self:
            message = []
            
            lines = record.line_ids.filtered(lambda x: x.field)
            if not lines:
                message = _("No lines configured.")
                record.message = message
                break
            try:
                datas = ast.literal_eval(record.datas)
            except:
                message = _("No datas or problems with datas.")
                record.message = message
                break
            
            # importa prima i ref_ipat per creare quei dati che poi associa
            ref_ipat = record.line_ids.filtered(lambda x: x.ref_ipat and not x.no_create)
            for ref in ref_ipat:
                # copia i dati negli altri ipat per importarli
                ref.ref_ipat.datas = record.datas
                ref.ref_ipat.header = record.header
                ref.ref_ipat.start_import()
                
            # per ogni dato fa la ricerca
            # crea
            create_count = 0
            search_count = 0
            fail_count = []
            to_search = self.line_ids.filtered(lambda x:x.to_search)
            
            for data in datas:
                result = False
                if to_search:
                    result = record.search_record(data=data)
                if not result:       
                    attrs = {}
                    
                    for line in lines:
                        attrs[line.field.name] = record.get_record_value(data=data, line=line) 
                    
                    try:
                        self.env[record.model.model].create(attrs)
                        create_count += 1
                    except:
                        fail_count.append(datas.index(data) + 2)
                else:
                    search_count += 1
            message.append(_('Records found: %s') % search_count)
            message.append(_('Records created: %s') % create_count)
            message.append(_('Records failed: %s') % fail_count)
            record.message = '\n'.join(message)
                    

class IPATLines(models.Model):
    _name = "bloomup.ipat.lines"
    _description = "Ipat Lines"
    
    column_name = fields.Char(
        string="File Column Name"
    )
    ipat_id = fields.Many2one(
        string="Ipat",
        comodel_name="bloomup.ipat"
    )
    model_id = fields.Many2one(
        string="Model",
        comodel_name="ir.model",
        related="ipat_id.model"
    )
    field = fields.Many2one(
        string="Model Field",
        comodel_name="ir.model.fields"
    )
    field_type = fields.Selection(
        string="Field Type",
        related='field.ttype'
    )
    ref_ipat = fields.Many2one(
        string="Ipat Reference",
        comodel_name="bloomup.ipat"
    )
    code = fields.Text(
        string="Code"
    )
    fixed = fields.Boolean(
        string="Fixed",
        default=False
    )
    no_create=fields.Boolean(
        string="No Create",
        default=False
    )
    to_search=fields.Boolean(
        string="To Search",
        default=False
    ) # identifica l'oggetto e lo cerca per questo campo o un gruppo di questi (in AND)
    required = fields.Boolean(
        string="Required",
        default=False
    ) 
    # required funziona su singolo ipat ma anche e soprattutto sul padre
    # in datas mette solo le righe (load_datas) che hanno tutti i
    # campi required compilati