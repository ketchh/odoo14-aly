# -*- coding: utf-8 -*-

def migrate(cr, version):
    """
    Migrazione iniziale del modulo Enhanced Reports.
    Crea i dati di report per tutte le checklist già completate.
    """
    
    # Ottieni tutte le checklist completate senza dati di report
    cr.execute("""
        SELECT id 
        FROM checklist_checklist 
        WHERE state = 'done' 
        AND data_compilazione IS NOT NULL
        ORDER BY data_compilazione DESC
        LIMIT 1000
    """)
    
    checklist_ids = [row[0] for row in cr.fetchall()]
    
    if checklist_ids:
        # Log della migrazione
        cr.execute("""
            INSERT INTO ir_logging (name, level, dbname, line, func, path, message, create_date, create_uid)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), 1)
        """, (
            'netcheck_2_report_enhanced.migration',
            'INFO',
            cr.dbname,
            1,
            'migrate',
            'migrations/14.0.1.0.0/post-migration.py',
            f'Starting migration of {len(checklist_ids)} completed checklists to enhanced reporting structure'
        ))
        
        # Crea i dati di report per ogni checklist in batch
        batch_size = 50
        migrated_count = 0
        error_count = 0
        
        for i in range(0, len(checklist_ids), batch_size):
            batch_ids = checklist_ids[i:i + batch_size]
            
            try:
                # Usa il registry di Odoo per accedere al modello
                from odoo.registry import Registry
                from odoo.api import Environment
                
                registry = Registry(cr.dbname)
                with registry.cursor() as new_cr:
                    env = Environment(new_cr, 1, {})  # uid=1 (admin)
                    checklists = env['checklist.checklist'].browse(batch_ids)
                    
                    for checklist in checklists:
                        try:
                            if checklist.state == 'done' and not checklist.has_report_data:
                                checklist.create_report_data()
                                migrated_count += 1
                        except Exception as e:
                            error_count += 1
                            # Log dell'errore ma continua
                            cr.execute("""
                                INSERT INTO ir_logging (name, level, dbname, line, func, path, message, create_date, create_uid)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), 1)
                            """, (
                                'netcheck_2_report_enhanced.migration',
                                'WARNING',
                                cr.dbname,
                                1,
                                'migrate',
                                'migrations/14.0.1.0.0/post-migration.py',
                                f'Failed to migrate checklist {checklist.id}: {str(e)}'
                            ))
                    
                    new_cr.commit()
                    
            except Exception as e:
                error_count += len(batch_ids)
                # Log dell'errore del batch
                cr.execute("""
                    INSERT INTO ir_logging (name, level, dbname, line, func, path, message, create_date, create_uid)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), 1)
                """, (
                    'netcheck_2_report_enhanced.migration',
                    'ERROR',
                    cr.dbname,
                    1,
                    'migrate',
                    'migrations/14.0.1.0.0/post-migration.py',
                    f'Failed to migrate batch {i//batch_size + 1}: {str(e)}'
                ))
        
        # Log del risultato finale
        cr.execute("""
            INSERT INTO ir_logging (name, level, dbname, line, func, path, message, create_date, create_uid)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), 1)
        """, (
            'netcheck_2_report_enhanced.migration',
            'INFO',
            cr.dbname,
            1,
            'migrate',
            'migrations/14.0.1.0.0/post-migration.py',
            f'Migration completed: {migrated_count} checklists migrated successfully, {error_count} errors'
        ))
    
    else:
        # Log se non ci sono checklist da migrare
        cr.execute("""
            INSERT INTO ir_logging (name, level, dbname, line, func, path, message, create_date, create_uid)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), 1)
        """, (
            'netcheck_2_report_enhanced.migration',
            'INFO',
            cr.dbname,
            1,
            'migrate',
            'migrations/14.0.1.0.0/post-migration.py',
            'No completed checklists found to migrate'
        ))
