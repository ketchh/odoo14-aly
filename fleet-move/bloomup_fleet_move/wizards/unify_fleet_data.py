# -*- coding: utf-8 -*-
from odoo import models, fields, api

class FleetVehicleDataUnifier(models.TransientModel):
    _name = 'fleet.vehicle.data.unifier'
    _description = 'Unifica brand e modelli differenziati solo dal case'

    name = fields.Char(string='name')

    def unify_brands_and_models_by_case(self):
        """
        Unifica sia i brand che i modelli (fleet.vehicle.model.brand e fleet.vehicle.model)
        i cui nomi differiscono solo per maiuscolo/minuscolo.
        """
        self._unify_brands_by_case()
        self._unify_models_by_case()
        return True

    def _unify_brands_by_case(self):
        """
        Esegue l’unificazione dei brand in base al nome, ignorando il maiuscolo/minuscolo.
        Reindirizza i modelli che puntano al brand duplicato verso il brand canonico.
        """
        Brand = self.env['fleet.vehicle.model.brand']
        all_brands = Brand.search([])
        
        # Dizionario {nome_normalizzato: brand_canonico}
        canonical_map = {}

        for brand in all_brands:
            normalized_name = brand.name.strip().lower()
            
            if normalized_name not in canonical_map:
                # Se è la prima volta che troviamo questo nome normalizzato,
                # impostiamo questo brand come "canonico"
                canonical_map[normalized_name] = brand
            else:
                # Altrimenti è un duplicato: unifichiamolo con il canonico
                canonical_brand = canonical_map[normalized_name]
                
                # Reindirizza tutti i "fleet.vehicle.model" che puntano a brand duplicato
                self._reassign_models_to_brand(
                    duplicate_brand=brand,
                    new_brand=canonical_brand
                )

                # Opzionale: rinomina o elimina il brand duplicato
                brand.write({
                    'name': f"DEPRECATED - {brand.name}",
                })
                # Se vuoi proprio rimuoverlo (stai attento alle dipendenze!):
                # brand.unlink()

        # (Opzionale) Normalizza tutti i brand canonici in Title Case
        for brand in canonical_map.values():
            brand.write({
                'name': brand.name.strip().title()
            })

    def _reassign_models_to_brand(self, duplicate_brand, new_brand):
        """
        Reindirizza tutti i modelli che puntano a duplicate_brand verso new_brand.
        """
        Model = self.env['fleet.vehicle.model']
        # Trova i modelli che puntano al brand duplicato
        models_with_duplicate = Model.search([
            ('brand_id', '=', duplicate_brand.id)
        ])
        # Assegna il brand canonico
        if models_with_duplicate:
            models_with_duplicate.write({'brand_id': new_brand.id})

    def _unify_models_by_case(self):
        """
        Unifica i modelli (fleet.vehicle.model) in base al brand e al nome,
        ignorando le differenze di maiuscolo/minuscolo.
        Reindirizza i veicoli (fleet.vehicle) che puntano al modello duplicato.
        """
        Model = self.env['fleet.vehicle.model']
        all_models = Model.search([])

        # Dizionario {(brand_id, nome_normalizzato): modello_canonico}
        canonical_map = {}

        for model in all_models:
            # Normalizziamo nome e teniamo traccia del brand
            normalized_name = model.name.strip().lower()
            brand_id = model.brand_id.id if model.brand_id else False

            key = (brand_id, normalized_name)

            if key not in canonical_map:
                # Se è la prima volta che troviamo questa combinazione,
                # impostiamo questo modello come "canonico"
                canonical_map[key] = model
            else:
                # Altrimenti è un duplicato
                canonical_model = canonical_map[key]

                # Reindirizza i veicoli che puntano a questo modello duplicato
                self._reassign_vehicles_to_model(
                    duplicate_model=model,
                    new_model=canonical_model
                )

                # Opzionale: rinomina o elimina il modello duplicato
                model.write({
                    'name': f"DEPRECATED - {model.name}"
                })
                # Se vuoi proprio rimuoverlo (stai attento alle dipendenze!):
                # model.unlink()

        # (Opzionale) Normalizza i nomi dei modelli canonici in Title Case
        for model in canonical_map.values():
            model.write({
                'name': model.name.strip().title()
            })

    def _reassign_vehicles_to_model(self, duplicate_model, new_model):
        """
        Reindirizza tutti i veicoli (fleet.vehicle) che puntano al model duplicato
        verso il model canonico.
        """
        Vehicle = self.env['fleet.vehicle']
        vehicles_with_duplicate = Vehicle.search([
            ('model_id', '=', duplicate_model.id)
        ])
        if vehicles_with_duplicate:
            vehicles_with_duplicate.write({
                'model_id': new_model.id
            })
