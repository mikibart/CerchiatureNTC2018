#!/usr/bin/env python3
"""
Test della struttura del progetto
Verifica che tutti i moduli siano importabili
"""

import os
import sys
import importlib

def test_imports():
    """Testa che tutti i moduli siano importabili"""
    
    print("🔍 Test importazione moduli...\n")
    
    modules_to_test = [
        'src',
        'src.gui',
        'src.gui.main_window',
        'src.gui.modules',
        'src.gui.modules.input_module',
        'src.gui.modules.openings_module',
        'src.gui.modules.calc_module',
        'src.gui.modules.report_module',
        'src.widgets',
        'src.widgets.wall_canvas',
        'src.widgets.profile_selector',
        'src.core',
        'src.core.models',
        'src.core.models.project',
        'src.core.models.wall',
        'src.core.models.opening',
        'src.core.models.reinforcement',
        'src.core.engine',
        'src.core.engine.masonry',
        'src.core.engine.steel_frame',
        'src.core.engine.concrete_frame',
        'src.core.engine.verifications',
        'src.core.database',
        'src.core.database.profiles',
        'src.core.database.materials',
        'src.io',
        'src.io.project_manager',
        'src.report',
        'src.report.generator',
    ]
    
    success = []
    failed = []
    
    for module_name in modules_to_test:
        try:
            importlib.import_module(module_name)
            success.append(module_name)
            print(f"✅ {module_name}")
        except ImportError as e:
            failed.append((module_name, str(e)))
            print(f"❌ {module_name}: {e}")
    
    print(f"\n📊 Risultati:")
    print(f"   Successo: {len(success)}/{len(modules_to_test)}")
    print(f"   Falliti: {len(failed)}")
    
    if failed:
        print("\n⚠️  Moduli con errori:")
        for module, error in failed:
            print(f"   - {module}: {error}")
    else:
        print("\n🎉 Tutti i moduli sono importabili correttamente!")
    
    return len(failed) == 0


def test_resources():
    """Verifica che le risorse siano presenti"""
    
    print("\n🔍 Test risorse e file dati...\n")
    
    resources_to_check = [
        'data/materials.json',
        'data/profiles.json',
        'requirements.txt',
        'README.md',
        '.gitignore',
    ]
    
    for resource in resources_to_check:
        if os.path.exists(resource):
            size = os.path.getsize(resource)
            print(f"✅ {resource} ({size} bytes)")
        else:
            print(f"❌ {resource} - Non trovato")


def test_pyqt5():
    """Verifica installazione PyQt5"""
    
    print("\n🔍 Test PyQt5...\n")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import QT_VERSION_STR
        from PyQt5.Qt import PYQT_VERSION_STR
        
        print(f"✅ PyQt5 installato correttamente")
        print(f"   Qt version: {QT_VERSION_STR}")
        print(f"   PyQt version: {PYQT_VERSION_STR}")
        return True
    except ImportError:
        print("❌ PyQt5 non installato")
        print("   Eseguire: pip install PyQt5")
        return False


def main():
    """Esegue tutti i test"""
    
    print("=" * 60)
    print("TEST STRUTTURA PROGETTO CERCHIATURE NTC 2018")
    print("=" * 60)
    
    # Test imports
    imports_ok = test_imports()
    
    # Test risorse
    test_resources()
    
    # Test PyQt5
    pyqt_ok = test_pyqt5()
    
    print("\n" + "=" * 60)
    
    if imports_ok and pyqt_ok:
        print("✅ TUTTI I TEST PASSATI - Il progetto è pronto!")
        print("\nPuoi eseguire: python main.py")
    else:
        print("⚠️  ALCUNI TEST FALLITI")
        print("\nControlla gli errori sopra e:")
        print("1. Assicurati di essere nella directory del progetto")
        print("2. Installa le dipendenze: pip install -r requirements.txt")
    
    print("=" * 60)


if __name__ == "__main__":
    main()