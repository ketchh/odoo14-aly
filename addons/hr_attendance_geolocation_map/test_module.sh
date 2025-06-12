#!/bin/bash

# Script per testare l'installazione del modulo hr_attendance_geolocation_map

echo "=== Test del modulo HR Attendance Geolocation Map ==="
echo ""

# Verifica la struttura del modulo
echo "1. Verifica struttura del modulo..."
MODULE_PATH="/home/falx/Documents/Lavoro/AWS/alyservice-odoo-new/alyservice-odoo-2/addons/hr_attendance_geolocation_map"

if [ -d "$MODULE_PATH" ]; then
    echo "✓ Directory del modulo trovata"
else
    echo "✗ Directory del modulo non trovata"
    exit 1
fi

# Verifica file essenziali
FILES_TO_CHECK=(
    "__manifest__.py"
    "__init__.py"
    "models/__init__.py"
    "models/hr_attendance.py"
    "views/hr_attendance_views.xml"
    "views/assets.xml"
    "views/templates.xml"
    "static/src/js/attendance_map_widget.js"
    "static/src/css/attendance_map.css"
)

for file in "${FILES_TO_CHECK[@]}"; do
    if [ -f "$MODULE_PATH/$file" ]; then
        echo "✓ $file"
    else
        echo "✗ $file mancante"
    fi
done

echo ""
echo "2. Verifica sintassi Python..."

# Controlla sintassi Python
python3 -m py_compile "$MODULE_PATH/__manifest__.py" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ __manifest__.py sintassi corretta"
else
    echo "✗ __manifest__.py errore di sintassi"
fi

python3 -m py_compile "$MODULE_PATH/models/hr_attendance.py" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ models/hr_attendance.py sintassi corretta"
else
    echo "✗ models/hr_attendance.py errore di sintassi"
fi

echo ""
echo "3. Verifica XML..."

# Controlla sintassi XML
xmllint --noout "$MODULE_PATH/views/hr_attendance_views.xml" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ hr_attendance_views.xml sintassi corretta"
else
    echo "✗ hr_attendance_views.xml errore di sintassi"
fi

xmllint --noout "$MODULE_PATH/views/assets.xml" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ assets.xml sintassi corretta"
else
    echo "✗ assets.xml errore di sintassi"
fi

xmllint --noout "$MODULE_PATH/views/templates.xml" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ templates.xml sintassi corretta"
else
    echo "✗ templates.xml errore di sintassi"
fi

echo ""
echo "=== Test completato ==="
echo ""
echo "Il modulo dovrebbe essere pronto per l'installazione in Odoo."
echo "Per installarlo:"
echo "1. Riavviare Odoo con -u all"
echo "2. Andare in Apps e cercare 'HR Attendance Geolocation Map'"
echo "3. Installare il modulo"
