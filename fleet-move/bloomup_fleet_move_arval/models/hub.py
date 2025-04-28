from odoo import models, fields, api, _
import xlrd
import base64
from odoo.exceptions import UserError, ValidationError
import datetime 

class Arvaltasktipology(models.Model):
    _inherit = "task.typology"
    
    code = fields.Char(
        string="Column Name"
    )
    value = fields.Char(
        string="Value"
    )
    
class ArvalImporter(models.Model): 
    _inherit = "hub.importer"
       
    def save_import(self):
        """
        Legge il file e per ogni auto controlla se esiste nel db quel numero di telaio.
        Se esiste crea le attività altrimenti crea l'auto e le attività.
        
        se non è configurata la colonna csv allora prende il nome della selection
        """
        for record in self:
            
            if record.state == 'done':
                continue
            
            if record.source_data == 'internal':
                for line in record.internal_vehicle_ids:
                    auto = line.vehicle_id
                    task = auto.create_activities(record.project_id)
                    for t in task:
                        record.tasks = [(4, t.id, 0)]
                record.state = 'done'
                continue
                
            if not record.source_file:
                continue
                
            output = base64.b64decode(record.source_file)
            wb = xlrd.open_workbook(file_contents=output or b'')
            sheets = wb.sheet_names()
            # prendo il primo sheet ma possiamo configurare
            sheet = wb.sheet_by_name(sheets[0])
            
            attrs = {}
            for res in dict(self.env['hub.importer.config']._fields['field_id'].selection):
                line = record.project_id.partner_id.csv_hub_configuration.filtered(lambda x: x.field_id == res)
                name = dict(self.env['hub.importer.config']._fields['field_id'].selection)[res]
                if line:
                    name = line.name
                attrs[res] = name.strip()
            
            i = -1
            header = []
            for rowx, row in enumerate(map(sheet.row, range(sheet.nrows)), 1):
                values=[]
                i+=1
                for colx, cell in enumerate(row, 1):
                    values.append(cell.value)
                if i==0:
                    header=values
                    break
            datas=[]
            i=-1
            for rowx, row in enumerate(map(sheet.row, range(sheet.nrows)), 1):
                values=[]
                i+=1
                for colx, cell in enumerate(row, 1):
                    values.append(cell.value)
                if i>0:
                    dict_values = dict(zip(header,values))
                    datas.append(dict_values)
            
            for riga in datas:
                foundit = False
                auto = False
                create_attrs = {}
                if attrs['vin_sn'] in riga and riga[attrs['vin_sn']]:
                    res = self.env['fleet.vehicle'].search([('vin_sn','=',riga[attrs['vin_sn']].strip())])
                    if res:
                        auto = res[0]
                        auto.hub_importer_ids = [(4, record.id, 0)]
                        foundit = True
                if auto:   
                    task = auto.create_activities_arval(record.project_id, riga=riga)
                    for t in task:
                        record.tasks = [(4, t.id, 0)]

class ARvalVeicoli(models.Model):
    _inherit = "fleet.vehicle"
                         
    def create_activities_arval(self, project_id, riga=False):
        """
        Crea le attività default per questa auto
        project_id : obbligatorio
        """
        # predere le tipologia di attività default
        if not project_id:
            raise ValidationError(_("You can't create task without project"))
        typologies = self.env['task.typology'].search([])
        tasks = []
        for record in self:
            pricelist = project_id.get_pricelist()
            for type in typologies:
                # controllo che esista il rigo config
                create = False
                if type.code and type.value and riga:
                    if riga[type.code].lower().strip() == type.value.lower().strip(): 
                        create = True
                if type.default:
                    create = True
                if create:
                    delay_days = type.get_delay(pricelist)
                    attrs = {
                        'task_typology_id': type.id,
                        'vehicle_id': record.id,
                        'partner_id': project_id.partner_id.id,
                        'project_id': project_id.id,
                        'name': type.name,
                        'date_deadline': datetime.datetime.now() + datetime.timedelta(days=delay_days)
                    }
                    tasks.append(self.env['project.task'].create(attrs))
        return tasks
