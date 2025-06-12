#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Demo script per testare il modulo hr_attendance_geolocation_map

Questo script simula l'utilizzo del modulo creando dati di esempio
e mostrando come dovrebbe funzionare l'integrazione.
"""

def demo_attendance_locations():
    """
    Simula i dati di una presenza con coordinate geografiche
    """
    
    # Esempio di presenza con check-in e check-out
    attendance_data = {
        'id': 123,
        'employee_name': 'Mario Rossi',
        'check_in': '2025-06-12 08:30:00',
        'check_out': '2025-06-12 17:45:00',
        'check_in_latitude': 41.9028,  # Roma - Colosseo
        'check_in_longitude': 12.4964,
        'check_out_latitude': 41.8919, # Roma - Vaticano
        'check_out_longitude': 12.4814,
    }
    
    print("=== DEMO HR Attendance Geolocation Map ===")
    print(f"Dipendente: {attendance_data['employee_name']}")
    print(f"ID Presenza: {attendance_data['id']}")
    print()
    
    print("📍 PUNTI GEOGRAFICI:")
    print(f"🔴 Check-in:  {attendance_data['check_in']}")
    print(f"   Coordinate: {attendance_data['check_in_latitude']}, {attendance_data['check_in_longitude']}")
    print(f"   Posizione: Colosseo, Roma")
    print()
    
    print(f"🔵 Check-out: {attendance_data['check_out']}")
    print(f"   Coordinate: {attendance_data['check_out_latitude']}, {attendance_data['check_out_longitude']}")
    print(f"   Posizione: Vaticano, Roma")
    print()
    
    # Simula l'azione del bottone "Mostra Mappa"
    action_data = {
        'type': 'ir.actions.client',
        'tag': 'hr_attendance_map',
        'name': 'Attendance Locations',
        'params': {
            'locations': [
                {
                    'latitude': attendance_data['check_in_latitude'],
                    'longitude': attendance_data['check_in_longitude'],
                    'type': 'check_in',
                    'color': 'red',
                    'title': 'Check-in',
                    'time': '12/06/2025 08:30:00',
                    'employee': attendance_data['employee_name'],
                },
                {
                    'latitude': attendance_data['check_out_latitude'],
                    'longitude': attendance_data['check_out_longitude'],
                    'type': 'check_out',
                    'color': 'blue',
                    'title': 'Check-out',
                    'time': '12/06/2025 17:45:00',
                    'employee': attendance_data['employee_name'],
                }
            ],
            'attendance_id': attendance_data['id'],
        }
    }
    
    print("🗺️  AZIONE MAPPA GENERATA:")
    print(f"Action Type: {action_data['type']}")
    print(f"Tag: {action_data['tag']}")
    print(f"Numero di punti: {len(action_data['params']['locations'])}")
    print()
    
    print("🎯 FUNZIONALITÀ DEL MODULO:")
    print("✓ Bottone 'Mostra Mappa' nella vista form presenza")
    print("✓ Mappa interattiva con OpenStreetMap")
    print("✓ Marker rossi per check-in")
    print("✓ Marker blu per check-out")
    print("✓ Popup informativi con dettagli")
    print("✓ Legenda per distinguere i tipi di marker")
    print("✓ Zoom automatico per mostrare tutti i punti")
    print()
    
    print("📋 ISTRUZIONI DI UTILIZZO:")
    print("1. Installare il modulo hr_attendance_geolocation_map in Odoo")
    print("2. Assicurarsi che hr_attendance_geolocation sia già installato")
    print("3. Creare presenza con dati di geolocalizzazione")
    print("4. Aprire la vista form della presenza")
    print("5. Cliccare il bottone 'Mostra Mappa'")
    print("6. Visualizzare la mappa con i punti colorati")
    print()
    
    print("🔧 NOTE TECNICHE:")
    print("- Utilizza Leaflet.js per la visualizzazione mappe")
    print("- OpenStreetMap come provider di tile (gratuito)")
    print("- Widget JavaScript personalizzato per l'integrazione")
    print("- Template QWeb per l'interfaccia utente")
    print("- CSS personalizzato per i marker colorati")
    
    return action_data

if __name__ == "__main__":
    demo_data = demo_attendance_locations()
    
    print("\n" + "="*50)
    print("Demo completata! Il modulo è pronto per essere testato.")
    print("="*50)
