from odoo import _, api, fields, models
import time
AVAILABLE_MODEL = []
### RICORDARSI DI FARE L'OVERRIDE DELLE FUNZIONI E AGGUNGERE AVAILABLE MODEL 
### PER BLOCCARE SOLO SU DETERMINATI MODELLI SELEZIONATI
### if model not in AVAILABLE_MODEL:
###     return False

class StoreResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def get_records(self, model=False, fields=['id','name'], page=1, order="id desc", limit=8, domain=[]):
        """
        Funzione che prende i record del model, va ereditata per aggiungere il domain o 
        gli viene passato dal client
        """
        if not model:
            return []
        if page<=1:
            offset=0
        elif page > 1:
            offset = limit * (page-1)
        try:
            datas = self.env[model].sudo().with_context({'lang':self.env.user.lang}).search(
                domain, offset=offset, limit=limit, order=order)
            count = self.env[model].sudo().search_count(domain)
            results = {
                'next': True if count > (limit*page) else False, 
                'prev': True if page>1 else False,
                'records': []
            }
            for data in datas:
                attrs = {}
                for field in fields:
                    if isinstance(field, list):
                        if data[field[0]]:
                            attrs[field[0]] = [data[field[0]]['id']]
                        else:
                            attrs[field[0]] = ['']
                        for item in field[1:]:
                            if data[field[0]]:
                                attrs[field[0]].append(data[field[0]][item])
                            else:
                                attrs[field[0]].append('')
                    else:
                        if data[field]:
                            attrs[field] = data[field]
                        else:
                            attrs[field] = ''
                results['records'].append(attrs)
            return results
        except:
            return {'error': "C'è stato un errore imprevisto."}
    
    @api.model
    def cancel_record(self, model=False, record_id=False):
        """
        Mette a false active
        """
        if not model or not record_id:
            return {'error': "C'è stato un errore imprevisto."}
        try:
            record = self.env[model].sudo().with_context({'lang':self.env.user.lang}).browse(record_id)
            record.active = False
            return True
        except:
            return {'error': "C'è stato un errore imprevisto."}

    @api.model
    def get_data_record(self, model=False, record_id=False, fields=['id','name']):
        if not model or not record_id:
            return {'error': "C'è stato un errore imprevisto."}
        try:
            data = self.env[model].sudo().with_context({'lang':self.env.user.lang}).browse(record_id)
            attrs = {}
            for field in fields:
                if isinstance(field, list):
                    if data[field[0]]:
                        attrs[field[0]] = [data[field[0]]['id']]
                    else:
                        attrs[field[0]] = ['']
                    for item in field[1:]:
                        if data[field[0]]:
                            attrs[field[0]].append(data[field[0]][item])
                        else:
                            attrs[field[0]].append('')
                else:
                    if data[field]:
                        attrs[field] = data[field]
                    else:
                        attrs[field] = ''
            return attrs
        except:
            return {'error': "C'è stato un errore imprevisto."}

    @api.model
    def save_record(self, model=False, args=False):
        ### completamente ereditata ogni modello ha la sua save particolare
        pass